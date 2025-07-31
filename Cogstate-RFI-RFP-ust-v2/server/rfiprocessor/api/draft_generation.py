# rfiprocessor/api/draft_generation.py

from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from rfiprocessor.models.data_models import DraftRequest, DraftResponse
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import RfiDocument
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.core.agents.answer_generator import AnswerGeneratorAgent
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.utils.error_handler import APIErrorHandler
from config.config import Config

logger = get_logger(__name__)
config = Config()

async def generate_draft(request: DraftRequest) -> DraftResponse:
    """
    Takes a user-edited response for a specific question and uses an AI agent
    to polish it into a final draft, then updates the database.
    
    Args:
        request: DraftRequest containing the question and user's draft
    
    Returns:
        DraftResponse: Success status and generated draft data
    """
    logger.info(f"Received request to generate draft for RFI ID {request.responseId}, Question ID {request.questionId}")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            db_handler = DatabaseHandler(db_session)
            
            # 1. Fetch the RFI document from the database
            rfi_doc = db_handler.get_document_by_id(request.responseId, model_class=RfiDocument)
            if not rfi_doc or not rfi_doc.payload:
                raise APIErrorHandler.not_found("RFI document", request.responseId, "responseId")
            
            # 2. Initialize and run the drafting agent
            try:
                drafter = AnswerGeneratorAgent()
                # For draft generation, we'll use the user's response as context
                # and generate a polished version
                polished_answer = drafter.generate_answer(
                    question=request.question,
                    context_chunks=[{"content": request.response, "metadata": {"source": "user_draft"}}]
                )
            except Exception as e:
                logger.error(f"AnswerGeneratorAgent failed for RFI {request.responseId}: {e}", exc_info=True)
                raise APIErrorHandler.internal_error(f"Failed to generate polished draft: {str(e)}")
            
            # 3. Update the specific question in the JSON payload
            payload = rfi_doc.payload
            question_found = False
            
            for q in payload.get("questions", []):
                if str(q.get("id")) == str(request.questionId):
                    q["response"] = polished_answer
                    q["status"] = request.status  # Use the status from the request
                    question_found = True
                    break
            
            if not question_found:
                raise APIErrorHandler.not_found("question", str(request.questionId), "questionId")
            
            # 4. Save the updated payload and user info back to the database
            updates = {
                "payload": payload,
                "updated_by_user": request.user
            }
            db_handler.update_record(request.responseId, updates, model_class=RfiDocument)
            
            # 5. Return the success response
            response_data = {
                "responseId": request.responseId,
                "questionId": request.questionId,
                "question": request.question,
                "response": polished_answer,
                "status": request.status,  # Use the status from the request
                "user": request.user
            }
            
            logger.info(f"Successfully generated draft for RFI {request.responseId}, Question {request.questionId}")
            
            return DraftResponse(
                success=True,
                data=response_data
            )
            
        finally:
            db_session.close()
            
    except HTTPException:
        # Re-raise HTTP exceptions as they're already properly formatted
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_draft: {str(e)}", exc_info=True)
        raise APIErrorHandler.internal_error(f"Unexpected error: {str(e)}")