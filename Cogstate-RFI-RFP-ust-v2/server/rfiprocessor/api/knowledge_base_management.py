# rfiprocessor/api/knowledge_base_management.py

import os
from datetime import datetime
from typing import List, Optional

from fastapi import File, UploadFile, Form, HTTPException

# Import existing services and models
from config.config import Config
from rfiprocessor.services.markdown_converter import MarkdownConverter
from rfiprocessor.services.chunker import ChunkerService
from rfiprocessor.services.vector_store_service import VectorStoreService
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.services.file_upload_service import FileUploadService
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Document, IngestionStatus
from rfiprocessor.models.data_models import KnowledgeBaseEntryRequest, KnowledgeBaseEntryResponse
from rfiprocessor.utils.logger import get_logger

# Initialize configuration and logger
config = Config()
logger = get_logger(__name__)

# Initialize shared services
file_upload_service = FileUploadService()

# Knowledge base specific validation constants
ENTRY_TYPES = config.KNOWLEDGE_BASE_ENTRY_TYPES
SERVICE_CATEGORIES = config.KNOWLEDGE_BASE_SERVICE_CATEGORIES
BATCH_SIZE = config.KNOWLEDGE_BASE_BATCH_SIZE
DOCUMENT_TYPE = config.KNOWLEDGE_BASE_DOCUMENT_TYPE

def validate_entry_type(entry_type: str) -> bool:
    """Validate entry type."""
    return entry_type in ENTRY_TYPES

def validate_service_category(service_category: Optional[str]) -> bool:
    """Validate service category."""
    if service_category is None:
        return True
    return service_category in SERVICE_CATEGORIES

async def add_knowledge_base_entry(
    entryType: str = Form(...),
    serviceName: Optional[str] = Form(None),
    serviceCategory: Optional[str] = Form(None),
    description: str = Form(...),
    tags: str = Form(...),
    attachments: List[UploadFile] = File([])
):
    """
    Submit new knowledge base entries for approval.
    
    This endpoint uses the existing document processing infrastructure:
    - MarkdownConverter for file conversion
    - ChunkerService for text chunking
    - VectorStoreService for embedding
    - DatabaseHandler for persistence
    """
    
    try:
        # Validate entry type
        if not validate_entry_type(entryType):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid entryType. Must be one of: {', '.join(ENTRY_TYPES)}"
            )
        
        # Validate service category if provided
        if not validate_service_category(serviceCategory):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid serviceCategory. Must be one of: {', '.join(SERVICE_CATEGORIES)}"
            )
        
        # Validate attachments using shared service
        for attachment in attachments:
            # Validate file extension
            file_upload_service.validate_file_extension(
                filename=attachment.filename,
                content_type=attachment.content_type
            )
        
        # Process attachments using existing infrastructure
        processed_files = []
        
        for attachment in attachments:
            # Save file using shared service
            incoming_path = await file_upload_service.save_file(attachment)
            
            # Validate file size after saving
            file_size = os.path.getsize(incoming_path)
            file_upload_service.validate_file_size(file_size)
            
            # Use existing services to process the file
            db_session_generator = get_db_session()
            db_session = next(db_session_generator)
            
            try:
                db_handler = DatabaseHandler(db_session)
                
                # Register document in database (using existing logic)
                document = db_handler.add_or_get_document(source_filepath=incoming_path)
                
                # Update document metadata for knowledge base
                updates = {
                    "document_type": DOCUMENT_TYPE,
                    "document_grade": entryType,
                    "ingestion_status": IngestionStatus.PENDING
                }
                db_handler.update_document(document.id, updates)
                
                # Process file using existing pipeline components
                converter = MarkdownConverter()
                chunker = ChunkerService(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
                vector_store = VectorStoreService()
                
                # Convert to markdown (using existing logic)
                markdown_content, _ = converter.convert_to_markdown(incoming_path)
                
                # Create chunks (using existing logic)
                chunks_data = chunker.create_chunks_for_document(document, markdown_content)
                
                if chunks_data:
                    # Add chunks to database (using existing logic)
                    db_handler.add_chunks_to_document(document.id, chunks_data)
                    db_handler.update_document(document.id, {"ingestion_status": IngestionStatus.CHUNKED})
                    
                    # Add to vector store (using existing logic)
                    vector_ids = vector_store.add_documents(batch_size=BATCH_SIZE)
                    
                    # Update final status
                    db_handler.update_document(document.id, {"ingestion_status": IngestionStatus.VECTORIZED})
                    
                    processed_files.append({
                        "filename": attachment.filename,
                        "document_id": document.id,
                        "status": "processed"
                    })
                else:
                    processed_files.append({
                        "filename": attachment.filename,
                        "document_id": document.id,
                        "status": "no_chunks_created"
                    })
                
            finally:
                db_session.close()
        
        # Create success response
        message = f"Successfully processed {len(processed_files)} knowledge base entries"
        if processed_files:
            message += f". Document IDs: {[f['document_id'] for f in processed_files]}"
        
        return KnowledgeBaseEntryResponse(
            message=message,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge base entry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")