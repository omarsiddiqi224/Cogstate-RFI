# rfiprocessor/db/db_models.py

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from .database import Base

class IngestionStatus(enum.Enum):
    """Enumeration for the status of a document in the ingestion pipeline."""
    PENDING = "PENDING"
    MARKDOWN_CONVERTED = "MARKDOWN_CONVERTED"
    CLASSIFIED = "CLASSIFIED"
    PARSED = "PARSED"
    CHUNKED = "CHUNKED"
    VECTORIZED = "VECTORIZED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    """
    SQLAlchemy model for the 'documents' table.
    Tracks the state of each source document throughout the ingestion pipeline.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    
    # File tracking
    source_filename = Column(String, nullable=False, index=True)
    source_filepath = Column(String, unique=True, nullable=False)
    processed_filepath = Column(String, nullable=True)
    markdown_filepath = Column(String, nullable=True)
    
    # Classification and Parsing
    document_type = Column(String, nullable=True, index=True) # e.g., 'RFI/RFP', 'Supporting Document'
    document_grade = Column(String, nullable=True) # e.g., 'SOP', 'Past Response'
    rfi_json_payload = Column(JSON, nullable=True) # Stores the large JSON from the Parser Agent
    
    # Pipeline Status
    ingestion_status = Column(
        Enum(IngestionStatus), 
        nullable=False, 
        default=IngestionStatus.PENDING,
        index=True
    )
    error_message = Column(Text, nullable=True) # To log processing errors
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Chunks
    # A single document can be broken down into multiple chunks.
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.source_filename}', status='{self.ingestion_status.name}')>"


class Chunk(Base):
    """
    SQLAlchemy model for the 'chunks' table.
    Stores individual text chunks generated from documents, ready for vectorization.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to link back to the parent document
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Chunk content and metadata
    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=False)
    
    # Vector store information
    vector_id = Column(String, nullable=True, index=True, unique=True) # ID from ChromaDB or other vector store
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to Document
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<Chunk(id={self.id}, document_id={self.document_id}, vector_id='{self.vector_id}')>"