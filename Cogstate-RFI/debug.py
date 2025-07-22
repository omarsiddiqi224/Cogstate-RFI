#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import shutil
from tqdm import tqdm

# --- Core Application Imports ---
from config.config import Config
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.utils.wlak_dir import list_all_file_paths
from rfiprocessor.services.markdown_converter import MarkdownConverter, ProcessorType
from rfiprocessor.core.agents.document_classifier import DocumentClassifierAgent

# --- Database Imports ---
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import IngestionStatus

# --- Initial Setup ---
config = Config()
logger = get_logger(__name__)

def run_markdown_conversion_pipeline():
    """
    Scans for new files, converts them to markdown, and tracks progress in the database.
    """

    # --- Step 1: Markdown Conversion ---
    logger.info("--- Starting Markdown Conversion Pipeline ---")

    # Initialize services
    converter = MarkdownConverter()
    classifier = DocumentClassifierAgent()

    # Get a database session and initialize the handler
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)

        # 1. Scan the incoming directory for all files
        all_files = list_all_file_paths(config.INCOMING_DATA_PATH)

        # 2. Register all found files in the database if they don't exist
        logger.info(f"Found {len(all_files)} files. Registering new files in the database...")
        for file_path in all_files:
            # This will add the document if new, or get the existing one.
            db_handler.add_or_get_document(source_filepath=file_path)

        # 3. Fetch only the documents that are pending conversion
        pending_docs = db_handler.get_documents_by_status(IngestionStatus.PENDING)

        # Filter out unsupported files
        valid_docs = [
            doc for doc in pending_docs 
            if any(doc.source_filename.lower().endswith(ext) for ext in config.VALID_FILE_EXTNS)
        ]

        if not valid_docs:
            logger.info("No new documents to convert. Pipeline finished.")
            return

        logger.info(f"Found {len(valid_docs)} new documents to process.")

        # 4. Process each pending document
        for doc in tqdm(valid_docs, desc="Converting files to Markdown"):
            try:
                logger.info(f"Processing document: {doc.source_filename} (ID: {doc.id})")

                # Determine which processor to use
                processor_to_use = ProcessorType.MARKITDOWN
                if any(doc.source_filename.lower().endswith(ext) for ext in config.UNSTRD_FILE_EXTNS):
                    processor_to_use = ProcessorType.UNSTRUCTURED

                # Convert the file to markdown
                markdown_content, markdown_path = converter.convert_to_markdown(
                    file_path=doc.source_filepath,
                    processor=processor_to_use
                )

                # Move the original raw file to the processed directory
                destination_path = os.path.join(config.PROCESSED_DATA_PATH, doc.source_filename)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.move(doc.source_filepath, destination_path)

                # Update the document record in the database with the new status and paths
                updates = {
                    "markdown_filepath": markdown_path,
                    "processed_filepath": destination_path,
                    "ingestion_status": IngestionStatus.MARKDOWN_CONVERTED,
                    "error_message": None # Clear any previous errors
                }
                db_handler.update_document(doc.id, updates)
                logger.info(f"Successfully converted and moved document ID {doc.id}.")

            except Exception as e:
                logger.error(f"Error processing document ID {doc.id} ('{doc.source_filename}'): {e}", exc_info=True)
                # Update the document record to reflect the failure
                db_handler.update_document(
                    doc.id,
                    {
                        "ingestion_status": IngestionStatus.FAILED,
                        "error_message": str(e)
                    }
                )

    finally:
        # Ensure the database session is closed
        db_session.close()
        logger.info("--- Markdown Conversion Pipeline Finished ---")

    # Get a database session and initialize the handler
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)

        # --- Step 2: Document Classification ---
        logger.info("--- Starting Document Classification Step ---")
        docs_to_classify = db_handler.get_documents_by_status(IngestionStatus.MARKDOWN_CONVERTED)

        if not docs_to_classify:
            logger.info("No new documents to classify.")
        else:
            logger.info(f"Found {len(docs_to_classify)} documents to classify.")

        for doc in tqdm(docs_to_classify, desc="Classifying documents"):
            try:
                logger.info(f"Classifying document: {doc.source_filename} (ID: {doc.id})")

                # Read the markdown content from the file
                with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # Call the classifier agent
                classification = classifier.classify(markdown_content)

                # Update the document in the database
                updates = {
                    "document_type": classification.get("document_type"),
                    "document_grade": classification.get("document_grade"),
                    "ingestion_status": IngestionStatus.CLASSIFIED,
                    "error_message": None
                }
                db_handler.update_document(doc.id, updates)
                logger.info(f"Successfully classified document ID {doc.id}.")

            except Exception as e:
                logger.error(f"Error classifying document ID {doc.id}: {e}", exc_info=True)
                db_handler.update_document(
                    doc.id,
                    {"ingestion_status": IngestionStatus.FAILED, "error_message": f"Classification failed: {e}"}
                )

    finally:
        db_session.close()
        logger.info("--- Ingestion Pipeline Finished ---")


if __name__ == "__main__":
    logger.info("Application started.")

    # Ensure the database and tables are created before running the pipeline
    init_db()

    # Run the main processing function
    run_markdown_conversion_pipeline()

    logger.info("Application finished.")


# In[ ]:


from tqdm import tqdm

# --- Core Application Imports ---
from config.config import Config
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.core.agents.document_classifier import DocumentClassifierAgent

# --- Database Imports ---
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import IngestionStatus

# --- Initial Setup ---
config = Config()
logger = get_logger(__name__)

def run_document_classification_pipeline():
    """
    Scans for markdown_converted files, classify them to RFI/RFO or Supporting Document with grades, and tracks progress in the database.
    """

    classifier = DocumentClassifierAgent()

    # Get a database session and initialize the handler
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)

        # --- Step 2: Document Classification ---
        logger.info("--- Starting Document Classification Step ---")
        docs_to_classify = db_handler.get_documents_by_status(IngestionStatus.MARKDOWN_CONVERTED)

        if not docs_to_classify:
            logger.info("No new documents to classify.")
        else:
            logger.info(f"Found {len(docs_to_classify)} documents to classify.")

        for doc in tqdm(docs_to_classify, desc="Classifying documents"):
            try:
                logger.info(f"Classifying document: {doc.source_filename} (ID: {doc.id})")

                # Read the markdown content from the file
                with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # Call the classifier agent
                classification = classifier.classify(markdown_content)

                # Update the document in the database
                updates = {
                    "document_type": classification.get("document_type"),
                    "document_grade": classification.get("document_grade"),
                    "ingestion_status": IngestionStatus.CLASSIFIED,
                    "error_message": None
                }
                db_handler.update_document(doc.id, updates)
                logger.info(f"Successfully classified document ID {doc.id}.")

            except Exception as e:
                logger.error(f"Error classifying document ID {doc.id}: {e}", exc_info=True)
                db_handler.update_document(
                    doc.id,
                    {"ingestion_status": IngestionStatus.FAILED, "error_message": f"Classification failed: {e}"}
                )

    finally:
            db_session.close()
            logger.info("--- Ingestion Pipeline Finished ---")

if __name__ == "__main__":
    logger.info("Application started.")

    # Ensure the database and tables are created before running the pipeline
    init_db()

    # Run the main processing function
    run_document_classification_pipeline()

    logger.info("Application finished.")


# In[1]:


from tqdm import tqdm
from pydantic import ValidationError

# --- Core Application Imports ---
from config.config import Config
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.core.agents.rfi_parser import RfiParserAgent

# --- Database Imports ---
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import IngestionStatus
from rfiprocessor.models.data_models import RFIJson

# --- Initial Setup ---
config = Config()
logger = get_logger(__name__)

def run_rfi_parser_pipeline():
    """
    Scans for classified RFI/RFP files and processes them through the RFI parser pipeline.
    """
    logger.info("--- Starting RFI Parsing Pipeline ---")
    rfi_parser = RfiParserAgent()

    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)

        # --- Step 3: RFI/RFP Parsing ---
        logger.info("--- Starting RFI/RFP Parsing Step ---")
        docs_to_parse = db_handler.get_documents_by_status(IngestionStatus.CLASSIFIED)

        if not docs_to_parse:
            logger.info("No new classified documents to parse.")
        else:
            logger.info(f"Found {len(docs_to_parse)} documents to potentially parse.")

        for doc in tqdm(docs_to_parse, desc="Parsing RFI/RFP documents"):
            try:
                # Only process documents that were classified as RFI/RFP
                if doc.document_type != "RFI/RFP":
                    logger.info(f"Skipping parsing for doc ID {doc.id} (type: {doc.document_type}). Marking as parsed.")
                    # For non-RFI docs, we just update the status to move them along the pipeline
                    db_handler.update_document(doc.id, {"ingestion_status": IngestionStatus.PARSED})
                    continue

                logger.info(f"Parsing RFI/RFP document: {doc.source_filename} (ID: {doc.id})")

                # Read the markdown content
                with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # Call the RFI Parser Agent
                parsed_data = rfi_parser.parse(markdown_content)

                # Save parsed output to data/json_output
                import os, json
                output_dir = "data/json_output"
                os.makedirs(output_dir, exist_ok=True)
                json_filename = os.path.splitext(doc.source_filename)[0] + ".json"
                output_path = os.path.join(output_dir, json_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_data, f, indent=2, ensure_ascii=False)

                # Validate the structured output with Pydantic
                try:
                    validated_data = RFIJson.model_validate(parsed_data)
                    logger.info(f"Successfully validated JSON structure for doc ID {doc.id}.")
                except ValidationError as ve:
                    # If validation fails, log the specific error and mark the doc as failed
                    error_details = f"Pydantic validation failed for doc ID {doc.id}: {ve}"
                    logger.error(error_details)
                    db_handler.update_document(
                        doc.id,
                        {"ingestion_status": IngestionStatus.FAILED, "error_message": error_details}
                    )
                    continue # Skip to the next document

                # Update the document record with the JSON payload and new status
                updates = {
                    "rfi_json_payload": validated_data.model_dump(), # Use the validated data
                    "ingestion_status": IngestionStatus.PARSED,
                    "error_message": None
                }
                db_handler.update_document(doc.id, updates)
                logger.info(f"Successfully parsed and stored JSON for document ID {doc.id}.")

            except Exception as e:
                error_msg = f"Error parsing document ID {doc.id}: {e}"
                logger.error(error_msg, exc_info=True)
                db_handler.update_document(
                    doc.id,
                    {"ingestion_status": IngestionStatus.FAILED, "error_message": error_msg}
                )

    finally:
        db_session.close()
        logger.info("--- Ingestion Pipeline Finished ---")

# The if __name__ == "__main__": block remains the same
if __name__ == "__main__":
    logger.info("Application started.")
    init_db()
    run_rfi_parser_pipeline()
    logger.info("Application finished.")


# In[2]:


# rfiprocessor/services/chunker.py

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter

from rfiprocessor.db.db_models import Document
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)

class ChunkerService:
    """
    A service responsible for breaking down documents into smaller, meaningful chunks.
    It applies different strategies based on the document type.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        """
        Initializes the ChunkerService.

        Args:
            chunk_size (int): The target size for text chunks (for supporting docs).
            chunk_overlap (int): The overlap between consecutive chunks.
        """
        # This text splitter is specifically for supporting documents.
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""], # Splits by paragraph, then line, etc.
        )
        logger.info(f"ChunkerService initialized with chunk_size={chunk_size} and chunk_overlap={chunk_overlap}")

    def create_chunks_for_document(self, doc: Document, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Main method to create chunks for a document. It routes to the appropriate
        chunking strategy based on the document's type.

        Args:
            doc (Document): The database ORM object for the document.
            markdown_content (str): The full markdown content of the document.

        Returns:
            List[Dict[str, Any]]: A list of chunk dictionaries, ready for database insertion.
        """
        logger.info(f"Creating chunks for document ID {doc.id} (Type: {doc.document_type})")

        if doc.document_type == "RFI/RFP":
            return self._chunk_rfi_document(doc)
        else:
            return self._chunk_supporting_document(doc, markdown_content)

    def _chunk_rfi_document(self, doc: Document) -> List[Dict[str, Any]]:
        """
        Chunks an RFI/RFP document by treating each Q&A pair as a separate chunk.
        """
        if not doc.rfi_json_payload or "qa_pairs" not in doc.rfi_json_payload:
            logger.warning(f"Document ID {doc.id} is of type RFI/RFP but has no Q&A payload. Skipping.")
            return []

        chunks = []
        qa_pairs = doc.rfi_json_payload.get("qa_pairs", [])
        meta_data = doc.rfi_json_payload.get("meta_data", {})

        for qa in qa_pairs:
            chunk_text = f"Question: {qa.get('question', 'N/A')}\n\nAnswer: {qa.get('answer', 'N/A')}"

            chunk_metadata = {
                "source_document_id": doc.id,
                "source_filename": doc.source_filename,
                "document_type": doc.document_type,
                "company_name": meta_data.get("company_name", "Unknown"),
                "domain": qa.get("domain", "General"),
                "question_type": qa.get("type", "open-ended")
            }

            chunks.append({
                "chunk_text": chunk_text,
                "chunk_metadata": chunk_metadata
            })

        logger.info(f"Created {len(chunks)} Q&A-based chunks for document ID {doc.id}.")
        return chunks

    def _chunk_supporting_document(self, doc: Document, markdown_content: str) -> List[Dict[str, Any]]:
        """
        Chunks a supporting document using semantic splitting (e.g., by paragraph).
        """
        if not markdown_content.strip():
            logger.warning(f"Markdown content for document ID {doc.id} is empty. Skipping chunking.")
            return []

        # Use the text splitter to create chunks from the markdown content
        split_texts = self.text_splitter.split_text(markdown_content)

        chunks = []
        for text in split_texts:
            chunk_metadata = {
                "source_document_id": doc.id,
                "source_filename": doc.source_filename,
                "document_type": doc.document_type,
                "document_grade": doc.document_grade
            }
            chunks.append({
                "chunk_text": text,
                "chunk_metadata": chunk_metadata
            })

        logger.info(f"Created {len(chunks)} semantic chunks for document ID {doc.id}.")
        return chunks


# In[ ]:


import os
import shutil
from tqdm import tqdm

# --- Core Application Imports ---
from config.config import Config
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.core.agents.rfi_parser import RfiParserAgent

# --- Database Imports ---
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import IngestionStatus
from rfiprocessor.models.data_models import RFIJson

# --- Initial Setup ---
config = Config()
logger = get_logger(__name__)


def run_chunking_pipeline():
    """
    Scans for new files and processes them through the ingestion pipeline.
    """
    logger.info("--- Starting Ingestion Pipeline ---")

    # Initialize services and agents
    chunker = ChunkerService(config.CHUNK_SIZE, config. CHUNK_OVERLAP)

    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)
        # --- Step 4: Document Chunking ---
        logger.info("--- Starting Document Chunking Step ---")
        docs_to_chunk = db_handler.get_documents_by_status(IngestionStatus.PARSED)

        if not docs_to_chunk:
            logger.info("No new parsed documents to chunk.")
        else:
            logger.info(f"Found {len(docs_to_chunk)} documents to chunk.")

        for doc in tqdm(docs_to_chunk, desc="Chunking documents"):
            try:
                logger.info(f"Chunking document: {doc.source_filename} (ID: {doc.id})")

                # We need the markdown content for supporting docs.
                # RFI docs don't need it for chunking, but it's cleaner to always have it.
                with open(doc.markdown_filepath, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()

                # Call the chunker service
                chunks_data = chunker.create_chunks_for_document(doc, markdown_content)

                if not chunks_data:
                    logger.warning(f"No chunks were created for document ID {doc.id}. Moving to next stage.")
                else:
                    # Add the created chunks to the database
                    db_handler.add_chunks_to_document(doc.id, chunks_data)

                # Update the document status to CHUNKED
                db_handler.update_document(doc.id, {"ingestion_status": IngestionStatus.CHUNKED})
                logger.info(f"Successfully chunked and stored chunks for document ID {doc.id}.")

            except Exception as e:
                error_msg = f"Error chunking document ID {doc.id}: {e}"
                logger.error(error_msg, exc_info=True)
                db_handler.update_document(
                    doc.id,
                    {"ingestion_status": IngestionStatus.FAILED, "error_message": error_msg}
                )

    finally:
        db_session.close()
        logger.info("--- Ingestion Pipeline Finished ---")

# The if __name__ == "__main__": block remains the same
if __name__ == "__main__":
    logger.info("Application started.")
    init_db()
    run_ingestion_pipeline()
    logger.info("Application finished.")

