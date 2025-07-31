# rfiprocessor/services/rfi_document_service.py

from typing import Optional, Tuple
from fastapi import HTTPException

from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import RfiDocument
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)

class RFIDocumentService:
    """Shared service for RFI document lookup operations."""
    
    @staticmethod
    def find_document_by_response_id(response_id: str) -> Tuple[Optional[RfiDocument], Optional[dict]]:
        """
        Find RFI document and target section by response ID.
        
        Args:
            response_id: The response ID to search for
            
        Returns:
            Tuple of (rfi_document, target_section) or (None, None) if not found
        """
        logger.info(f"Looking for RFI document with responseId: {response_id}")
        
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            all_rfi_documents = db_session.query(RfiDocument).all()
            
            for doc in all_rfi_documents:
                if doc.payload and doc.payload.get("saved_sections"):
                    for section in doc.payload["saved_sections"]:
                        if section.get("id") == response_id:
                            logger.info(f"Found RFI document: {doc.title}")
                            return doc, section
            
            logger.warning(f"No RFI document found containing responseId: {response_id}")
            return None, None
            
        finally:
            db_session.close()
    
    @staticmethod
    def find_document_by_response_id_or_raise(response_id: str, entity_name: str = "RFI document") -> Tuple[RfiDocument, dict]:
        """
        Find RFI document by response ID or raise HTTPException if not found.
        
        Args:
            response_id: The response ID to search for
            entity_name: Name of the entity for error message
            
        Returns:
            Tuple of (rfi_document, target_section)
            
        Raises:
            HTTPException: If document not found
        """
        rfi_document, target_section = RFIDocumentService.find_document_by_response_id(response_id)
        
        if not rfi_document:
            raise HTTPException(
                status_code=404, 
                detail=f"{entity_name} not found containing responseId: {response_id}"
            )
        
        return rfi_document, target_section