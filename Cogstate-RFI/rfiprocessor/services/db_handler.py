# rfiprocessor/services/db_handler.py

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import os

from ..db.db_models import Document, Chunk, IngestionStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseHandler:
    """
    A service class to handle all database interactions (CRUD operations)
    for the Document and Chunk models. It encapsulates the database logic.
    """

    def __init__(self, db_session: Session):
        """
        Initializes the handler with a database session.
        
        Args:
            db_session (Session): An active SQLAlchemy session.
        """
        self.db = db_session

    def add_or_get_document(self, source_filepath: str) -> Document:
        """
        Adds a new document to the database if it doesn't exist based on the source path.
        If it already exists, it returns the existing document record. This prevents duplicates.

        Args:
            source_filepath (str): The unique source path of the file.

        Returns:
            Document: The newly created or existing Document ORM object.
        """
        existing_doc = self.db.query(Document).filter(Document.source_filepath == source_filepath).first()
        
        if existing_doc:
            logger.info(f"Document with path '{source_filepath}' already exists. Returning existing record ID {existing_doc.id}.")
            return existing_doc
        
        source_filename = os.path.basename(source_filepath)
        
        new_doc = Document(
            source_filename=source_filename,
            source_filepath=source_filepath,
            ingestion_status=IngestionStatus.PENDING
        )
        
        self.db.add(new_doc)
        self.db.commit()
        self.db.refresh(new_doc)
        logger.info(f"Added new document '{source_filename}' to database with ID {new_doc.id}.")
        return new_doc

    def get_documents_by_status(self, status: IngestionStatus) -> List[Document]:
        """
        Retrieves all documents from the database that match a given ingestion status.

        Args:
            status (IngestionStatus): The status to filter by.

        Returns:
            List[Document]: A list of Document objects.
        """
        logger.debug(f"Querying for documents with status: {status.name}")
        return self.db.query(Document).filter(Document.ingestion_status == status).all()

    def update_document(self, document_id: int, updates: Dict[str, Any]) -> Optional[Document]:
        """
        Updates a document record with the given key-value pairs.

        Args:
            document_id (int): The ID of the document to update.
            updates (Dict[str, Any]): A dictionary of fields to update. 
                                     Keys must match Document model attributes.

        Returns:
            Optional[Document]: The updated Document object, or None if not found.
        """
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Cannot update. Document with ID {document_id} not found.")
            return None
        
        logger.info(f"Updating document ID {document_id} with: {updates}")
        for key, value in updates.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
            else:
                logger.warning(f"Attempted to update non-existent attribute '{key}' on Document model.")
        
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def add_chunks_to_document(self, document_id: int, chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
        """
        Adds a list of new chunks associated with a specific document.

        Args:
            document_id (int): The ID of the parent document.
            chunks_data (List[Dict[str, Any]]): A list of dictionaries, where each
                                                dict contains 'chunk_text' and 'chunk_metadata'.

        Returns:
            List[Chunk]: The list of newly created Chunk ORM objects.
        """
        if not self.db.query(Document).filter(Document.id == document_id).first():
            msg = f"Cannot add chunks. Document with ID {document_id} not found."
            logger.error(msg)
            raise ValueError(msg)

        new_chunks = [
            Chunk(
                document_id=document_id,
                chunk_text=data.get("chunk_text"),
                chunk_metadata=data.get("chunk_metadata", {})
            ) for data in chunks_data
        ]
        
        self.db.add_all(new_chunks)
        self.db.commit()
        logger.info(f"Added {len(new_chunks)} chunks to document ID {document_id}.")
        
        # Refresh each object to load database-generated values like 'id'
        for chunk in new_chunks:
            self.db.refresh(chunk)
            
        return new_chunks

    def update_chunk_vector_ids(self, chunk_vector_map: Dict[int, str]):
        """
        Efficiently updates multiple chunk records with their vector IDs.

        Args:
            chunk_vector_map (Dict[int, str]): A dictionary mapping chunk_id to vector_id.
        """
        chunk_ids = list(chunk_vector_map.keys())
        chunks_to_update = self.db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()

        for chunk in chunks_to_update:
            if chunk.id in chunk_vector_map:
                chunk.vector_id = chunk_vector_map[chunk.id]
        
        self.db.commit()
        logger.info(f"Updated vector IDs for {len(chunks_to_update)} chunks.")