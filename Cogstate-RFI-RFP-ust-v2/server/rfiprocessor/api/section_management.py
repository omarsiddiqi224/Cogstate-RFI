# rfiprocessor/api/section_management.py

from datetime import datetime

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
            # Check if a section with this responseId already exists to avoid duplication
            # We'll search through all RFI documents to find if this responseId exists
            existing_document = None
            existing_section = None
            
            all_rfi_documents = db_session.query(RfiDocument).all()
            for doc in all_rfi_documents:
                if doc.payload and doc.payload.get("saved_sections"):
                    for section in doc.payload["saved_sections"]:
                        if section.get("id") == request.responseId:
                            existing_document = doc
                            existing_section = section
                            break
                    if existing_document:
                        break
            
            if existing_document and existing_section:
                # Update existing section
                logger.info(f"Updating existing section with responseId: {request.responseId}")
                
                # Update the existing section
                existing_section.update({
                    "questionId": request.questionId,
                    "question": request.question,
                    "response": request.response,
                    "status": request.status,
                    "user": request.user,
                    "saved_at": datetime.utcnow().isoformat()
                })
                
                # Update the document
                existing_document.updated_by_user = request.user
                existing_document.updated_at = datetime.utcnow()
                
                db_session.commit()
                db_session.refresh(existing_document)
                
                rfi_document = existing_document
                
            else:
                # Create a new RFI document entry to store the saved section
                logger.info(f"Creating new section with responseId: {request.responseId}")
                
                rfi_document = RfiDocument(
                    title=f"Saved Section - {request.question[:50]}...",
                    source_filename=f"section_{request.responseId}",
                    number_of_questions=1,
                    status=RfiStatus.IN_REVIEW,
                    progress=100,
                    updated_by_user=request.user,
                    payload={
                        "saved_sections": [{
                            "id": request.responseId,
                            "questionId": request.questionId,
                            "question": request.question,
                            "response": request.response,
                            "status": request.status,
                            "user": request.user,
                            "saved_at": datetime.utcnow().isoformat()
                        }]
                    }
                )
                
                # Add to database
                db_session.add(rfi_document)
                db_session.commit()
                db_session.refresh(rfi_document)
            
            # Create the response data - matching the exact format you specified
            saved_section_data = {
                "responseId": request.responseId,
                "questionId": request.questionId,
                "question": request.question,
                "response": request.response,
                "status": request.status,
                "user": request.user
            }
            
            logger.info(f"Section saved successfully with document ID: {rfi_document.id}")
            
            return SaveSectionResponse(
                success=True,
                data=saved_section_data
            )
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error saving section: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
            # Check if a section with this responseId already exists
            existing_document = None
            existing_section = None
            
            all_rfi_documents = db_session.query(RfiDocument).all()
            for doc in all_rfi_documents:
                if doc.payload and doc.payload.get("saved_sections"):
                    for section in doc.payload["saved_sections"]:
                        if section.get("id") == request.responseId:
                            existing_document = doc
                            existing_section = section
                            break
                    if existing_document:
                        break
            
            if existing_document and existing_section:
                # Update existing section status to completed
                logger.info(f"Marking existing section as complete with responseId: {request.responseId}")
                
                # Update the existing section with completed status
                existing_section.update({
                    "questionId": request.questionId,
                    "question": request.question,
                    "response": request.response,
                    "status": QUESTION_STATUS_COMPLETED,  # Force status to completed
                    "user": request.user,
                    "completed_at": datetime.utcnow().isoformat()
                })
                
                # Update the document
                existing_document.updated_by_user = request.user
                existing_document.updated_at = datetime.utcnow()
                
                db_session.commit()
                db_session.refresh(existing_document)
                
                rfi_document = existing_document
                
            else:
                # Create a new RFI document entry to store the completed section
                logger.info(f"Creating new completed section with responseId: {request.responseId}")
                
                rfi_document = RfiDocument(
                    title=f"Completed Section - {request.question[:50]}...",
                    source_filename=f"completed_section_{request.responseId}",
                    number_of_questions=1,
                    status=RfiStatus.COMPLETED,
                    progress=100,
                    updated_by_user=request.user,
                    payload={
                        "saved_sections": [{
                            "id": request.responseId,
                            "questionId": request.questionId,
                            "question": request.question,
                            "response": request.response,
                            "status": QUESTION_STATUS_COMPLETED,  # Force status to completed
                            "user": request.user,
                            "completed_at": datetime.utcnow().isoformat()
                        }]
                    }
                )
                
                # Add to database
                db_session.add(rfi_document)
                db_session.commit()
                db_session.refresh(rfi_document)
            
            # Create the response data - matching the exact format you specified
            marked_complete_data = {
                "responseId": request.responseId,
                "questionId": request.questionId,
                "question": request.question,
                "response": request.response,
                "status": QUESTION_STATUS_COMPLETED,  # Always return completed status
                "user": request.user
            }
            
            logger.info(f"Section marked as complete successfully with document ID: {rfi_document.id}")
            
            return MarkCompleteResponse(
                success=True,
                data=marked_complete_data
            )
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error marking section complete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")