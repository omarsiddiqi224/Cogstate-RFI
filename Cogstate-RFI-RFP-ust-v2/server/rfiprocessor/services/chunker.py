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