# rfiprocessor/api/document_status.py

from fastapi import HTTPException

from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Document, IngestionStatus
from rfiprocessor.models.data_models import FileUploadResponse
from rfiprocessor.utils.logger import get_logger
from .file_upload import create_response_from_parsed_data, create_processing_response

logger = get_logger(__name__)

async def get_document_status(document_id: str):
    """
    Get the current status and data for a processed document.
    
    Args:
        document_id: The unique document ID returned from the upload endpoint
    
    Returns:
        FileUploadResponse: Current document status and data
    """
    logger.info(f"=== GETTING DOCUMENT STATUS ===")
    logger.info(f"Requested document ID: {document_id}")
    
    try:
        # Find the document by searching through all documents
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            # Get all documents and find the one that matches
            documents = db_session.query(Document).all()
            logger.info(f"Found {len(documents)} total documents in database")
            
            document = None
            for doc in documents:
                logger.info(f"Checking document ID {doc.id}: {doc.source_filename}")
                # Try to match by UUID pattern or by checking if the UUID contains the DB ID
                if (document_id == str(doc.id) or 
                    str(doc.id) in document_id or 
                    document_id in str(doc.id)):
                    document = doc
                    logger.info(f"Matched document ID {doc.id}")
                    break
            
            if not document:
                logger.warning(f"Document not found for ID: {document_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            logger.info(f"Found document: ID={document.id}, Status={document.ingestion_status}, HasPayload={bool(document.rfi_json_payload)}")
            
            # Check if document is processed
            if document.ingestion_status == IngestionStatus.VECTORIZED and document.rfi_json_payload:
                logger.info("Document is fully processed, returning parsed data")
                return create_response_from_parsed_data(document_id, document.source_filename, document)
            else:
                logger.info("Document is still processing, returning processing response")
                return create_processing_response(document_id, document.source_filename, document)
                
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")