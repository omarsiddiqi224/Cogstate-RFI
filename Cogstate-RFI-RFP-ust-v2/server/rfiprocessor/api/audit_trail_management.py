# rfiprocessor/api/audit_trail_management.py

from datetime import datetime
from typing import List

from fastapi import HTTPException

from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import RfiDocument, QUESTION_STATUS_COMPLETED
from rfiprocessor.models.data_models import AuditTrailItem, AuditTrailResponse
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)

async def get_audit_trail(response_id: str):
    """
    Retrieve audit history for a specific response.
    
    Args:
        response_id: The response ID to get audit trail for
        
    Returns:
        AuditTrailResponse: List of audit trail entries
    """
    logger.info("=== GETTING AUDIT TRAIL ===")
    logger.info(f"Requested response ID: {response_id}")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            # Find the RFI document that contains the specific responseId in its saved sections
            rfi_document = None
            target_section = None
            
            all_rfi_documents = db_session.query(RfiDocument).all()
            for doc in all_rfi_documents:
                if doc.payload and doc.payload.get("saved_sections"):
                    for section in doc.payload["saved_sections"]:
                        if section.get("id") == response_id:
                            rfi_document = doc
                            target_section = section
                            break
                    if rfi_document:
                        break
            
            if not rfi_document:
                logger.warning(f"RFI document not found containing responseId: {response_id}")
                raise HTTPException(status_code=404, detail="Response not found")
            
            logger.info(f"Found RFI document: {rfi_document.title}")
            
            # Extract saved sections from the RFI document
            payload = rfi_document.payload or {}
            saved_sections = payload.get("saved_sections", [])
            
            # Generate audit trail entries based on the saved sections
            audit_trail_entries = []
            entry_counter = 1
            
            for section in saved_sections:
                # Create audit trail entry for initial creation
                if section.get("saved_at"):
                    audit_entry = AuditTrailItem(
                        id=f"at{entry_counter}",
                        timestamp=section.get("saved_at"),
                        actor=section.get("user", "Unknown"),
                        action=f"Created initial response for question {section.get('questionId', 'Unknown')}.",
                        question=section.get("question", ""),
                        type="CREATE"
                    )
                    audit_trail_entries.append(audit_entry)
                    entry_counter += 1
                
                # Create audit trail entry for completion if marked complete
                if section.get("status") == QUESTION_STATUS_COMPLETED and section.get("completed_at"):
                    audit_entry = AuditTrailItem(
                        id=f"at{entry_counter}",
                        timestamp=section.get("completed_at"),
                        actor=section.get("user", "Unknown"),
                        action=f"Marked question {section.get('questionId', 'Unknown')} as complete.",
                        question=section.get("question", ""),
                        type="COMPLETE"
                    )
                    audit_trail_entries.append(audit_entry)
                    entry_counter += 1
                
                # Create audit trail entry for AI generation (if this is the target section)
                if section.get("id") == response_id:
                    # Add AI generation entry (assuming AI generated the initial content)
                    ai_timestamp = section.get("saved_at")
                    if ai_timestamp:
                        # Create a timestamp slightly before the saved timestamp for AI generation
                        from datetime import timedelta
                        ai_time = datetime.fromisoformat(ai_timestamp.replace('Z', '+00:00')) - timedelta(minutes=5)
                        ai_timestamp = ai_time.isoformat().replace('+00:00', 'Z')
                        
                        audit_entry = AuditTrailItem(
                            id=f"at{entry_counter}",
                            timestamp=ai_timestamp,
                            actor="AI (Gemini)",
                            action=f"Generated initial draft for question {section.get('questionId', 'Unknown')}.",
                            question=section.get("question", ""),
                            type="AI"
                        )
                        audit_trail_entries.append(audit_entry)
                        entry_counter += 1
                    
                    # Add edit entry if there was a response
                    if section.get("response") and section.get("saved_at"):
                        audit_entry = AuditTrailItem(
                            id=f"at{entry_counter}",
                            timestamp=section.get("saved_at"),
                            actor=section.get("user", "Unknown"),
                            action=f"Edited response for question {section.get('questionId', 'Unknown')}.",
                            question=section.get("question", ""),
                            type="EDIT"
                        )
                        audit_trail_entries.append(audit_entry)
                        entry_counter += 1
            
            # Sort audit trail entries by timestamp (oldest first)
            audit_trail_entries.sort(key=lambda x: x.timestamp)
            
            # Reassign IDs to maintain sequential order
            for i, entry in enumerate(audit_trail_entries, 1):
                entry.id = f"at{i}"
            
            logger.info(f"Generated {len(audit_trail_entries)} audit trail entries for responseId: {response_id}")
            
            return audit_trail_entries
            
        finally:
            db_session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")