# rfiprocessor/api/section_management.py

from datetime import datetime
from typing import Optional, Tuple, Dict, Any

from fastapi import HTTPException

from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import RfiDocument, RfiStatus, QUESTION_STATUS_COMPLETED
from rfiprocessor.models.data_models import (
    SaveSectionRequest,
    SaveSectionResponse,
    MarkCompleteRequest,
    MarkCompleteResponse
)
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)

def find_existing_section(
    db_session, 
    response_id: str, 
    question_id: str
) -> Tuple[Optional[RfiDocument], Optional[Dict[str, Any]]]:
    """
    Find existing section/question in RFI documents.
    
    Args:
        db_session: Database session
        response_id: Response ID to search for
        question_id: Question ID to search for
        
    Returns:
        Tuple[Optional[RfiDocument], Optional[Dict]]: (document, section) or (None, None)
    """
    all_rfi_documents = db_session.query(RfiDocument).all()
    
    for doc in all_rfi_documents:
        # Check saved_sections (regular RFI workflow)
        if doc.payload and doc.payload.get("saved_sections"):
            for section in doc.payload["saved_sections"]:
                if section.get("id") == response_id:
                    return doc, section
        
        # Check questions array (draft answers workflow)
        if doc.payload and doc.payload.get("questions"):
            for question in doc.payload["questions"]:
                if str(question.get("id")) == str(question_id):
                    return doc, question
    
    return None, None

def update_section_in_document(
    existing_document: RfiDocument,
    question_id: str,
    updated_data: Dict[str, Any]
) -> None:
    """
    Update a section/question in the document payload.
    
    Args:
        existing_document: The document to update
        question_id: ID of the question to update
        updated_data: Data to update the question with
    """
    # Create a new payload with the updated question
    updated_payload = existing_document.payload.copy()
    questions = updated_payload.get("questions", [])
    
    # Find and update the specific question
    for i, question in enumerate(questions):
        if str(question.get("id")) == str(question_id):
            questions[i] = {
                **question,  # Keep existing fields
                **updated_data  # Add updated fields
            }
            break
    
    # Update the entire payload to ensure SQLAlchemy detects the change
    existing_document.payload = updated_payload
    
    # Force SQLAlchemy to mark the payload as modified
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(existing_document, "payload")

def calculate_and_update_progress(existing_document: RfiDocument) -> None:
    """
    Calculate and update progress based on completed sections/questions.
    
    Args:
        existing_document: The document to update progress for
    """
    payload = existing_document.payload or {}
    
    # Calculate progress based on workflow type
    if payload.get("questions"):
        # Draft answers workflow - questions are stored in 'questions' array
        questions = payload.get("questions", [])
        total_questions = len(questions)
        completed_questions = sum(1 for question in questions if question.get("status") == QUESTION_STATUS_COMPLETED)
        progress = int((completed_questions / total_questions * 100) if total_questions > 0 else 0)
    else:
        # Regular RFI workflow - questions are stored in 'saved_sections' array
        saved_sections = payload.get("saved_sections", [])
        total_sections = len(saved_sections)
        completed_sections = sum(1 for section in saved_sections if section.get("status") == QUESTION_STATUS_COMPLETED)
        progress = int((completed_sections / total_sections * 100) if total_sections > 0 else 0)
    
    # Update document status based on progress
    if progress == 100:
        existing_document.status = RfiStatus.COMPLETED
    elif progress >= 50:
        existing_document.status = RfiStatus.IN_REVIEW
    else:
        existing_document.status = RfiStatus.IN_PROGRESS
    
    existing_document.progress = progress
    logger.info(f"Updated progress to {progress}% and status to {existing_document.status}")

async def save_section(request: SaveSectionRequest):
    """
    Save an updated section/answer for a specific question.
    
    Args:
        request: SaveSectionRequest containing the section data to save
    
    Returns:
        SaveSectionResponse: Success status and saved data
    """
    logger.info("=== SAVE SECTION STARTED ===")
    logger.info(f"Received save section request:")
    logger.info(f"  - responseId: '{request.responseId}'")
    logger.info(f"  - question: '{request.question[:50]}...'")
    logger.info(f"  - status: '{request.status}'")
    logger.info(f"  - user: '{request.user}'")
    logger.info(f"  - response length: {len(request.response)} characters")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            # Find existing section
            existing_document, existing_section = find_existing_section(
                db_session, request.responseId, request.questionId
            )
            
            if existing_document and existing_section:
                # Update existing section
                logger.info(f"Updating existing section with responseId: {request.responseId}")
                
                updated_data = {
                    "questionId": request.questionId,
                    "question": request.question,
                    "response": request.response,
                    "status": request.status,
                    "user": request.user,
                    "saved_at": datetime.utcnow().isoformat()
                }
                
                update_section_in_document(existing_document, request.questionId, updated_data)
                calculate_and_update_progress(existing_document)
                
                # Commit changes
                db_session.commit()
                logger.info("Section saved successfully")
                
                return SaveSectionResponse(
                    success=True,
                    message="Section saved successfully",
                    data=updated_data
                )
            else:
                logger.warning(f"Section not found with responseId: {request.responseId}")
                raise HTTPException(status_code=404, detail="Section not found")
                
        finally:
            db_session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving section: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

async def mark_complete(request: MarkCompleteRequest):
    """
    Mark a section/question as complete by updating its status.
    
    Args:
        request: MarkCompleteRequest containing the section data to mark as complete
    
    Returns:
        MarkCompleteResponse: Success status and marked complete data
    """
    logger.info("=== MARK COMPLETE STARTED ===")
    logger.info(f"Received mark complete request:")
    logger.info(f"  - responseId: '{request.responseId}'")
    logger.info(f"  - questionId: '{request.questionId}'")
    logger.info(f"  - question: '{request.question[:50]}...'")
    logger.info(f"  - status: '{request.status}'")
    logger.info(f"  - user: '{request.user}'")
    logger.info(f"  - response length: {len(request.response)} characters")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            # Find existing section
            existing_document, existing_section = find_existing_section(
                db_session, request.responseId, request.questionId
            )
            
            if existing_document and existing_section:
                # Update existing section status to completed
                logger.info(f"Marking existing section as complete with responseId: {request.responseId}")
                logger.info(f"Found question with ID: '{existing_section.get('id')}', current status: '{existing_section.get('status')}'")
                
                updated_data = {
                    "questionId": request.questionId,
                    "question": request.question,
                    "response": request.response,
                    "status": QUESTION_STATUS_COMPLETED,  # Force status to completed
                    "user": request.user,
                    "completed_at": datetime.utcnow().isoformat()
                }
                
                update_section_in_document(existing_document, request.questionId, updated_data)
                calculate_and_update_progress(existing_document)
                
                # Commit changes
                db_session.commit()
                logger.info("Section marked as complete successfully")
                
                return MarkCompleteResponse(
                    success=True,
                    message="Section marked as complete successfully",
                    data=updated_data
                )
            else:
                logger.warning(f"Section not found with responseId: {request.responseId}")
                raise HTTPException(status_code=404, detail="Section not found")
                
        finally:
            db_session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking section complete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")