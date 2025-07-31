import os
import json
import shutil
from tqdm import tqdm
from pydantic import ValidationError
from contextlib import contextmanager
from typing import List, Dict, Any, Generator
from sqlalchemy import func

# --- Core Application Imports ---
from config.config import Config
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.utils.wlak_dir import list_all_file_paths
from rfiprocessor.services.markdown_converter import MarkdownConverter, ProcessorType
from rfiprocessor.core.agents.document_classifier import DocumentClassifierAgent
from rfiprocessor.core.agents.rfi_parser import RfiParserAgent
from rfiprocessor.services.chunker import ChunkerService
from rfiprocessor.services.vector_store_service import VectorStoreService

# --- Database Imports ---
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import Chunk, IngestionStatus
from rfiprocessor.models.data_models import RFIJson
from langchain_core.documents import Document
from rfiprocessor.db import db_models

# --- Initial Setup ---
config = Config()
logger = get_logger(__name__)


class IngestionPipeline:
    """Main pipeline class that orchestrates the document ingestion process."""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.converter = MarkdownConverter()
        self.classifier = DocumentClassifierAgent()
        self.rfi_parser = RfiParserAgent()
        self.chunker = ChunkerService(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        self.vector_store_service = VectorStoreService()
    
    @contextmanager
    def get_db_handler(self) -> Generator[DatabaseHandler, None, None]:
        """Context manager for database session handling."""
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            yield DatabaseHandler(db_session)
        finally:
            db_session.close()
    
    def run_full_pipeline(self) -> None:
        """Runs the complete ingestion pipeline."""
        logger.info("Starting full ingestion pipeline")
        
        self._run_markdown_conversion()
        self._run_document_classification()
        self._run_rfi_parsing()
        self._run_document_chunking()
        self._run_vector_store_embedding()
        
        logger.info("Full ingestion pipeline completed")
    
    def _run_markdown_conversion(self) -> None:
        """Step 1: Convert documents to markdown format."""
        logger.info("--- Starting Markdown Conversion Pipeline ---")
        
        with self.get_db_handler() as db_handler:
            # Register all files in database
            self._register_files_in_database(db_handler)
            
            # Get pending documents
            pending_docs = db_handler.get_documents_by_status(IngestionStatus.PENDING)
            valid_docs = self._filter_valid_documents(pending_docs)
            
            if not valid_docs:
                logger.info("No new documents to convert. Pipeline finished.")
                return
            
            logger.info(f"Found {len(valid_docs)} new documents to process.")
            
            # Process each document
            for doc in tqdm(valid_docs, desc="Converting files to Markdown"):
                self._convert_single_document(db_handler, doc)
        
        logger.info("--- Markdown Conversion Pipeline Finished ---")
    
    def _run_document_classification(self) -> None:
        """Step 2: Classify documents as RFI/RFP or Supporting Document."""
        logger.info("--- Starting Document Classification Step ---")
        
        with self.get_db_handler() as db_handler:
            docs_to_classify = db_handler.get_documents_by_status(IngestionStatus.MARKDOWN_CONVERTED)
            
            if not docs_to_classify:
                logger.info("No new documents to classify.")
                return
            
            logger.info(f"Found {len(docs_to_classify)} documents to classify.")
            
            for doc in tqdm(docs_to_classify, desc="Classifying documents"):
                self._classify_single_document(db_handler, doc)
        
        logger.info("--- Document Classification Step Finished ---")
    
    def _run_rfi_parsing(self) -> None:
        """Step 3: Parse RFI/RFP documents."""
        logger.info("--- Starting RFI Parsing Pipeline ---")
        
        with self.get_db_handler() as db_handler:
            docs_to_parse = db_handler.get_documents_by_status(IngestionStatus.CLASSIFIED)
            
            if not docs_to_parse:
                logger.info("No new classified documents to parse.")
                return
            
            logger.info(f"Found {len(docs_to_parse)} documents to potentially parse.")
            
            for doc in tqdm(docs_to_parse, desc="Parsing RFI/RFP documents"):
                self._parse_single_document(db_handler, doc)
        
        logger.info("--- RFI Parsing Pipeline Finished ---")
    
    def _run_document_chunking(self) -> None:
        """Step 4: Chunk parsed documents."""
        logger.info("--- Starting Chunking Pipeline ---")
        
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            docs_to_chunk = db_handler.get_documents_by_status(IngestionStatus.PARSED)
            
            if not docs_to_chunk:
                logger.info("No new parsed documents to chunk.")
                return
            
            logger.info(f"Found {len(docs_to_chunk)} documents to chunk.")
            
            # Get starting chunk ID
            max_chunk_id = db_session.query(func.max(Chunk.id)).scalar() or 0
            logger.info(f"Starting new chunk IDs from {max_chunk_id + 1}")
            current_chunk_id = max_chunk_id + 1
            
            for doc in tqdm(docs_to_chunk, desc="Chunking documents"):
                current_chunk_id = self._chunk_single_document(db_handler, doc, current_chunk_id)
        finally:
            db_session.close()
        
        logger.info("--- Chunking Pipeline Finished ---")
    
    def _run_vector_store_embedding(self) -> None:
        """Step 5: Embed chunks into vector store."""
        logger.info("--- Starting Vector Store Pipeline ---")
        
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            chunked_docs = db_handler.get_documents_by_status(IngestionStatus.CHUNKED)
            
            # Get chunks to embed
            chunks_to_embed = db_session.query(Chunk).join(
                db_models.Document
            ).filter(
                db_models.Document.ingestion_status == IngestionStatus.CHUNKED
            ).all()
            
            if not chunks_to_embed:
                logger.info("No chunked documents to embed.")
                return
            
            logger.info(f"Found {len(chunks_to_embed)} chunks to embed.")
            
            # Convert and embed chunks
            documents = self._prepare_chunks_for_embedding(chunks_to_embed)
            self._embed_documents_to_vector_store(db_handler, documents, chunked_docs)
        finally:
            db_session.close()
        
        logger.info("--- Vector Store Pipeline Finished ---")
    
    def _register_files_in_database(self, db_handler: DatabaseHandler) -> None:
        """Register all found files in the database."""
        all_files = list_all_file_paths(config.INCOMING_DATA_PATH)
        logger.info(f"Found {len(all_files)} files. Registering new files in the database...")
        
        for file_path in all_files:
            db_handler.add_or_get_document(source_filepath=file_path)
    
    def _filter_valid_documents(self, pending_docs: List[Any]) -> List[Any]:
        """Filter out unsupported file types."""
        return [
            doc for doc in pending_docs 
            if any(doc.source_filename.lower().endswith(ext) for ext in config.VALID_FILE_EXTNS)
        ]
    
    def _convert_single_document(self, db_handler: DatabaseHandler, doc: Any) -> None:
        """Convert a single document to markdown."""
        try:
            logger.info(f"Processing document: {doc.source_filename} (ID: {doc.id})")
            
            # Determine processor type
            processor_to_use = ProcessorType.MARKITDOWN
            if any(doc.source_filename.lower().endswith(ext) for ext in config.UNSTRD_FILE_EXTNS):
                processor_to_use = ProcessorType.UNSTRUCTURED
            
            # Convert to markdown
            markdown_content, markdown_path = self.converter.convert_to_markdown(
                file_path=doc.source_filepath,
                processor=processor_to_use
            )
            
            # Move original file
            destination_path = os.path.join(config.PROCESSED_DATA_PATH, doc.source_filename)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.move(doc.source_filepath, destination_path)
            
            # Update database
            updates = {
                "markdown_filepath": markdown_path,
                "processed_filepath": destination_path,
                "ingestion_status": IngestionStatus.MARKDOWN_CONVERTED,
                "error_message": None
            }
            db_handler.update_document(doc.id, updates)
            logger.info(f"Successfully converted and moved document ID {doc.id}.")
            
        except Exception as e:
            logger.error(f"Error processing document ID {doc.id} ('{doc.source_filename}'): {str(e)}", exc_info=True)
            db_handler.update_document(
                doc.id,
                {
                    "ingestion_status": IngestionStatus.FAILED,
                    "error_message": str(e)
                }
            )
    
    def _classify_single_document(self, db_handler: DatabaseHandler, doc: Any) -> None:
        """Classify a single document."""
        try:
            logger.info(f"Classifying document: {doc.source_filename} (ID: {doc.id})")
            
            # Read markdown content
            with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Classify document
            classification = self.classifier.classify(markdown_content)
            
            # Update database
            updates = {
                "document_type": classification.get("document_type"),
                "document_grade": classification.get("document_grade"),
                "ingestion_status": IngestionStatus.CLASSIFIED,
                "error_message": None
            }
            db_handler.update_document(doc.id, updates)
            logger.info(f"Successfully classified document ID {doc.id}.")
            
        except Exception as e:
            logger.error(f"Error classifying document ID {doc.id}: {str(e)}", exc_info=True)
            db_handler.update_document(
                doc.id,
                {"ingestion_status": IngestionStatus.FAILED, "error_message": f"Classification failed: {str(e)}"}
            )
    
    def _parse_single_document(self, db_handler: DatabaseHandler, doc: Any) -> None:
        """Parse a single RFI/RFP document."""
        try:
            # Skip non-RFI/RFP documents
            if doc.document_type != "RFI/RFP":
                logger.info(f"Skipping parsing for doc ID {doc.id} (type: {doc.document_type}). Marking as parsed.")
                db_handler.update_document(doc.id, {"ingestion_status": IngestionStatus.PARSED})
                return
            
            logger.info(f"Parsing RFI/RFP document: {doc.source_filename} (ID: {doc.id})")
            
            # Read markdown content
            with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # Parse document
            parsed_data = self.rfi_parser.parse(markdown_content)
            
            # Save to JSON file
            self._save_parsed_json(doc, parsed_data)
            
            # Validate with Pydantic
            try:
                validated_data = RFIJson.model_validate(parsed_data)
                logger.info(f"Successfully validated JSON structure for doc ID {doc.id}.")
            except ValidationError as ve:
                error_details = f"Pydantic validation failed for doc ID {doc.id}: {ve}"
                logger.error(error_details)
                db_handler.update_document(
                    doc.id,
                    {"ingestion_status": IngestionStatus.FAILED, "error_message": error_details}
                )
                return
            
            # Update database
            updates = {
                "rfi_json_payload": validated_data.model_dump(),
                "ingestion_status": IngestionStatus.PARSED,
                "error_message": None
            }
            db_handler.update_document(doc.id, updates)
            logger.info(f"Successfully parsed and stored JSON for document ID {doc.id}.")
            
        except Exception as e:
            error_msg = f"Error parsing document ID {doc.id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            db_handler.update_document(
                doc.id,
                {"ingestion_status": IngestionStatus.FAILED, "error_message": error_msg}
            )
    
    def _save_parsed_json(self, doc: Any, parsed_data: Dict[str, Any]) -> None:
        """Save parsed data to JSON file."""
        output_dir = config.PARSED_JSON_PATH
        os.makedirs(output_dir, exist_ok=True)
        json_filename = os.path.splitext(doc.source_filename)[0] + ".json"
        output_path = os.path.join(output_dir, json_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved parsed output to {output_path}")
    
    def _chunk_single_document(self, db_handler: DatabaseHandler, doc: Any, current_chunk_id: int) -> int:
        """Chunk a single document and return the next available chunk ID."""
        try:
            logger.info(f"Chunking document: {doc.source_filename} (ID: {doc.id})")
            
            # Prepare content for chunking
            if doc.document_type == "RFI/RFP" and doc.rfi_json_payload:
                markdown_content = ""  # Not used for RFI/RFP
                logger.info("Chunking as RFI/RFP (using JSON payload)...")
            elif doc.markdown_filepath:
                with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                logger.info("Chunking as supporting document (using markdown content)...")
            else:
                logger.info("Skipping: Document is missing required data for chunking.")
                return current_chunk_id
            
            # Create chunks
            chunks_data = self.chunker.create_chunks_for_document(doc, markdown_content)
            logger.info(f"Number of chunks: {len(chunks_data)}")
            
            if chunks_data:
                # Assign chunk IDs
                for chunk_data in chunks_data:
                    chunk_data['id'] = current_chunk_id
                    current_chunk_id += 1
                
                # Save to database
                db_handler.add_chunks_to_document(doc.id, chunks_data)
                db_handler.update_document(doc.id, {"ingestion_status": IngestionStatus.CHUNKED})
                
                logger.info(f"Chunked document ID {doc.id}: {len(chunks_data)} chunks")
                logger.info(f"Successfully chunked and stored chunks for document ID {doc.id}.")
            else:
                logger.warning(f"No chunks were created for document ID {doc.id}. Moving to next stage.")
            
            return current_chunk_id
            
        except Exception as e:
            logger.error(f"Error chunking document ID {doc.id}: {str(e)}", exc_info=True)
            db_handler.update_document(
                doc.id,
                {"ingestion_status": IngestionStatus.FAILED, "error_message": f"Chunking failed: {str(e)}"}
            )
            return current_chunk_id
    
    def _prepare_chunks_for_embedding(self, chunks_to_embed: List[Chunk]) -> List[Document]:
        """Convert database chunks to LangChain Documents."""
        documents = []
        
        for chunk in tqdm(chunks_to_embed, desc="Preparing chunks for vector store"):
            try:
                document = Document(
                    page_content=chunk.chunk_text,
                    metadata=chunk.chunk_metadata,
                    id=str(chunk.id)
                )
                documents.append(document)
            except Exception as e:
                logger.error(f"Error preparing chunk ID {chunk.id}: {e}", exc_info=True)
                continue
        
        return documents
    
    def _embed_documents_to_vector_store(self, db_handler: DatabaseHandler, documents: List[Document], chunked_docs: List[Any]) -> None:
        """Embed documents to vector store and update database."""
        try:
            logger.info(f"Adding {len(documents)} chunks to vector store...")
            vector_ids = self.vector_store_service.add_documents(batch_size=self.batch_size)
            logger.info(f"Successfully added {len(vector_ids)} chunks to ChromaDB.")
            
            # Update document statuses
            for doc in chunked_docs:
                doc_id = int(doc.id)
                db_handler.update_document(
                    doc_id,
                    {"ingestion_status": IngestionStatus.VECTORIZED}
                )

                # Move original file
                file_name = doc.markdown_filepath.split("/")[-1]
                destination_path = os.path.join(config.PROCESSED_MARKDOWN_PATH, file_name)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.move(doc.markdown_filepath, destination_path)
                
        except Exception as e:
            logger.error(f"Error embedding documents for doc ID {doc.id}: {str(e)}", exc_info=True)
            db_handler.update_document(
                doc.id,
                {"ingestion_status": IngestionStatus.FAILED, "error_message": f"Embedding failed: {str(e)}"}
            )


def run_ingestion_pipeline(batch_size: int = 100) -> None:
    """
    Main entry point for the ingestion pipeline.
    
    Args:
        batch_size: Number of documents to process in each batch
    """
    pipeline = IngestionPipeline(batch_size)
    pipeline.run_full_pipeline()


if __name__ == "__main__":
    logger.info("Application started.")
    
    # Ensure the database and tables are created before running the pipeline
    init_db()
    
    # Run the main processing function
    run_ingestion_pipeline()
    
    logger.info("Application finished.")