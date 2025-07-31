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
    Retrieve audit history for a specific RFI document.
    The response_id parameter is the RFI document ID, not a question ID.
    """
    logger.info("=== GETTING AUDIT TRAIL ===")
    logger.info(f"Requested RFI document ID: {response_id}")

    try:
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            # First, try to find the RFI document by its ID
            rfi_document = db_session.query(RfiDocument).filter(RfiDocument.id == response_id).first()
            
            if not rfi_document:
                logger.warning(f"RFI document not found with ID: {response_id}")
                raise HTTPException(status_code=404, detail="RFI document not found")
            logger.info(f"Found RFI document: {rfi_document.title}")
            payload = rfi_document.payload or {}
            audit_trail_entries = []
            entry_counter = 1
            
            # Helper to add entries from a section/question
            def add_entries_from_section(section, is_question=False):
                nonlocal entry_counter
                question_id = section.get('questionId', section.get('id', 'Unknown'))
                
                # AI generation (always add for draft answers workflow)
                if is_question and section.get("response"):
                    # Estimate AI generation time (5 minutes before first save)
                    ai_timestamp = section.get("saved_at") or rfi_document.created_at.isoformat()
                    if ai_timestamp:
                        from datetime import timedelta
                        ai_time = datetime.fromisoformat(ai_timestamp.replace('Z', '+00:00')) - timedelta(minutes=5)
                        ai_timestamp = ai_time.isoformat().replace('+00:00', 'Z')
                        audit_entry = AuditTrailItem(
                            id=f"at{entry_counter}",
                            timestamp=ai_timestamp,
                            actor="AI (Gemini)",
                            action=f"Generated initial draft for question {question_id}.",
                            question=section.get("question", ""),
                            type="AI"
                        )
                        audit_trail_entries.append(audit_entry)
                        entry_counter += 1
                
                # Creation/Initial save
                if section.get("saved_at"):
                    audit_entry = AuditTrailItem(
                        id=f"at{entry_counter}",
                        timestamp=section.get("saved_at"),
                        actor=section.get("user", "AI Assistant"),
                        action=f"Created initial response for question {question_id}.",
                        question=section.get("question", ""),
                        type="CREATE"
                    )
                    audit_trail_entries.append(audit_entry)
                    entry_counter += 1
                
                # Completion
                if section.get("status") == QUESTION_STATUS_COMPLETED and section.get("completed_at"):
                    audit_entry = AuditTrailItem(
                        id=f"at{entry_counter}",
                        timestamp=section.get("completed_at"),
                        actor=section.get("user", "Unknown"),
                        action=f"Marked question {question_id} as complete.",
                        question=section.get("question", ""),
                        type="COMPLETE"
                    )
                    audit_trail_entries.append(audit_entry)
                    entry_counter += 1
                
                # Edit (if there's a response and it's been saved)
                if section.get("response") and section.get("saved_at"):
                    audit_entry = AuditTrailItem(
                        id=f"at{entry_counter}",
                        timestamp=section.get("saved_at"),
                        actor=section.get("user", "Unknown"),
                        action=f"Edited response for question {question_id}.",
                        question=section.get("question", ""),
                        type="EDIT"
                    )
                    audit_trail_entries.append(audit_entry)
                    entry_counter += 1
            
            # Add entries from saved_sections (regular RFI workflow)
            for section in payload.get("saved_sections", []):
                add_entries_from_section(section)
            
            # Add entries from questions array (draft answers workflow)
            for question in payload.get("questions", []):
                add_entries_from_section(question, is_question=True)
            
            # Add document-level audit entries
            if rfi_document.created_at:
                audit_entry = AuditTrailItem(
                    id=f"at{entry_counter}",
                    timestamp=rfi_document.created_at.isoformat(),
                    actor="System",
                    action="RFI document created and processing started.",
                    question="",
                    type="CREATE"
                )
                audit_trail_entries.append(audit_entry)
                entry_counter += 1
            
            # Sort by timestamp and reassign IDs
            audit_trail_entries.sort(key=lambda x: x.timestamp)
            for i, entry in enumerate(audit_trail_entries, 1):
                entry.id = f"at{i}"
            
            logger.info(f"Generated {len(audit_trail_entries)} audit trail entries for RFI document: {response_id}")
            return audit_trail_entries
        finally:
            db_session.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit trail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
