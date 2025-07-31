# rfiprocessor/db/db_models.py

import enum
import uuid
from datetime import datetime

def generate_uuid():
    """Generate a UUID string for database primary keys."""
    return str(uuid.uuid4())
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
    
# --- Inference Pipeline Models ---

# Question status constants
QUESTION_STATUS_PENDING = "pending"
QUESTION_STATUS_PROCESSING = "processing"
QUESTION_STATUS_COMPLETED = "completed"

class RfiStatus(enum.Enum):
    """Enumeration for the status of a new RFI being processed for response generation."""
    IN_PROGRESS = "IN_PROGRESS"       # AI is actively generating the draft.
    REVIEW_READY = "REVIEW_READY"     # AI work is done, draft is ready for human review.
    IN_REVIEW = "IN_REVIEW"           # A user is actively editing the draft.
    COMPLETED = "COMPLETED"           # User has finalized and approved the document.
    FAILED = "FAILED"   
    NOT_STARTED = "NOT_STARTED"              # An error occurred during the generation process.

class RfiDocument(Base):
    """
    SQLAlchemy model for the 'rfi_documents' table.
    Tracks the state and holds the payload for a new RFI being answered by the system.
    """
    __tablename__ = "rfi_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    source_filename = Column(String, nullable=False)
    number_of_questions = Column(Integer, default=0, nullable=False)
    status = Column(Enum(RfiStatus), nullable=False, default=RfiStatus.IN_PROGRESS, index=True)
    progress = Column(Integer, default=0, nullable=False)
    payload = Column(JSON, nullable=True)
    updated_by_user = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        # Updated repr for better debugging
        return f"<RfiDocument(id={self.id}, title='{self.title}', questions={self.number_of_questions}, status='{self.status.name}')>"