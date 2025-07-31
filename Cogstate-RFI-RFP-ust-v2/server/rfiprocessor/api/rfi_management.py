# rfiprocessor/api/rfi_management.py
 
from datetime import datetime, timedelta
 
from fastapi import HTTPException
 
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Document, IngestionStatus, RfiDocument, RfiStatus, QUESTION_STATUS_PENDING, QUESTION_STATUS_COMPLETED
from rfiprocessor.models.data_models import (
    ActiveRFIItem,
    ActiveRFIUser,
    ActiveRFIListResponse,
    SpecificRFIRequest,
    SpecificRFIResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    QuestionResponse,
    KnowledgeBaseItem,
    MetaData
)
from rfiprocessor.utils.logger import get_logger
 
logger = get_logger(__name__)
 
async def get_active_rfi_list():
    """
    Retrieve list of all active RFI/RFP documents.
    
    Returns:
        ActiveRFIListResponse: List of active RFI/RFP documents with their details
    """
    logger.info("=== GETTING ACTIVE RFI LIST ===")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            active_rfi_list = []
            
            # 1. Get all RFI documents from RfiDocument table that are not completed
            active_rfi_documents = db_session.query(RfiDocument).filter(
                RfiDocument.status != RfiStatus.COMPLETED
            ).all()
            
            logger.info(f"Found {len(active_rfi_documents)} active RFI documents from RfiDocument table")
            
            for rfi_doc in active_rfi_documents:
                # Extract data from the RFI document
                payload = rfi_doc.payload or {}
                saved_sections = payload.get("saved_sections", [])
                
                # Calculate progress based on completed sections
                total_sections = len(saved_sections)
                completed_sections = sum(1 for section in saved_sections if section.get("status") == QUESTION_STATUS_COMPLETED)
                progress = int((completed_sections / total_sections * 100) if total_sections > 0 else 0)
                
                # Get unique users who have worked on this RFI
                users_set = set()
                for section in saved_sections:
                    user = section.get("user")
                    if user:
                        users_set.add(user)
                
                users = [ActiveRFIUser(name=user) for user in users_set]
                
                # Determine current section being worked on
                current_section = "All Sections"
                if saved_sections:
                    # Find the most recent section that's not completed
                    recent_sections = [s for s in saved_sections if s.get("status") != QUESTION_STATUS_COMPLETED]
                    if recent_sections:
                        current_section = f"Section: {recent_sections[0].get('questionId', 'Unknown')}"
                
                # Create due date (you might want to store this in the database)
                # For now, we'll use a default due date
                due_date = (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
                
                # Create active RFI item
                active_rfi_item = ActiveRFIItem(
                    id=rfi_doc.id,
                    title=rfi_doc.title,
                    status=rfi_doc.status.value if rfi_doc.status else RfiStatus.IN_PROGRESS.value,
                    updated=rfi_doc.updated_at.isoformat() + "Z" if rfi_doc.updated_at else datetime.utcnow().isoformat() + "Z",
                    dueDate=due_date,
                    section=current_section,
                    progress=progress,
                    users=users
                )
                
                active_rfi_list.append(active_rfi_item)
            
            # 2. Get all processed RFI/RFP documents from Document table that are ready for work
            processed_rfi_documents = db_session.query(Document).filter(
                Document.document_type == "RFI/RFP",
                Document.ingestion_status == IngestionStatus.VECTORIZED,
                Document.rfi_json_payload.isnot(None)
            ).all()
            
            logger.info(f"Found {len(processed_rfi_documents)} processed RFI documents from Document table")
            
            for doc in processed_rfi_documents:
                # Extract data from the processed document
                rfi_payload = doc.rfi_json_payload or {}
                qa_pairs = rfi_payload.get("qa_pairs", [])
                
                # Calculate progress based on questions with answers
                total_questions = len(qa_pairs)
                answered_questions = sum(1 for qa in qa_pairs if qa.get("answer") and qa.get("answer").strip())
                progress = int((answered_questions / total_questions * 100) if total_questions > 0 else 0)
                
                # Create default users (since these are from processed documents)
                users = [ActiveRFIUser(name="AI Assistant")]
                
                # Determine current section being worked on
                current_section = "All Sections"
                if qa_pairs:
                    # Find the first question without an answer
                    unanswered_questions = [qa for qa in qa_pairs if not qa.get("answer") or not qa.get("answer").strip()]
                    if unanswered_questions:
                        current_section = f"Question: {unanswered_questions[0].get('question', 'Unknown')[:50]}..."
                
                # Create due date
                due_date = (datetime.utcnow() + timedelta(days=90)).isoformat() + "Z"
                
                # Create active RFI item
                active_rfi_item = ActiveRFIItem(
                    id=str(doc.id),  # Convert to string to match RfiDocument ID format
                    title=rfi_payload.get("meta_data", {}).get("company_name", doc.source_filename),
                    status=RfiStatus.NOT_STARTED.value,
                    updated=doc.updated_at.isoformat() + "Z" if doc.updated_at else datetime.utcnow().isoformat() + "Z",
                    dueDate=due_date,
                    section=current_section,
                    progress=progress,
                    users=users
                )
                
                active_rfi_list.append(active_rfi_item)
            
            logger.info(f"Returning {len(active_rfi_list)} total active RFI items")
            
            return ActiveRFIListResponse(
                success=True,
                data=active_rfi_list  # Return flat list of ActiveRFIItem objects
            )
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error getting active RFI list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
 
async def get_specific_rfi_details(request: SpecificRFIRequest):
    """
    Retrieve details of a specific RFI by responseId.
    
    Args:
        request: SpecificRFIRequest containing the RFI response ID
    
    Returns:
        SpecificRFIResponse: Detailed information about the specific RFI
    """
    logger.info("=== GETTING SPECIFIC RFI DETAILS ===")
    logger.info(f"Requested RFI response ID: {request.responseId}")
    
    try:
        # Get database session
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        
        try:
            # Find the RFI document by ID directly (for draft answers workflow)
            rfi_document = db_session.query(RfiDocument).filter(RfiDocument.id == request.responseId).first()
            
            if not rfi_document:
                # Fallback: try to find by searching through saved_sections (for regular RFI workflow)
                logger.info(f"Direct lookup failed, searching through saved_sections...")
                all_rfi_documents = db_session.query(RfiDocument).all()
                for doc in all_rfi_documents:
                    if doc.payload and doc.payload.get("saved_sections"):
                        for section in doc.payload["saved_sections"]:
                            if section.get("id") == request.responseId:
                                rfi_document = doc
                                break
                        if rfi_document:
                            break
            
            if not rfi_document:
                logger.warning(f"RFI document not found for responseId: {request.responseId}")
                raise HTTPException(status_code=404, detail="RFI document not found")
            
            logger.info(f"Found RFI document: {rfi_document.title}")
            
            # Extract data from the RFI document
            payload = rfi_document.payload or {}
            
            # Handle both data structures: 'questions' (draft answers) and 'saved_sections' (regular RFI)
            questions = []
            progress = 0
            
            if payload.get("questions"):
                # Draft answers workflow - questions are stored in 'questions' array
                logger.info("Using 'questions' array from draft answers workflow")
                questions_data = payload.get("questions", [])
                logger.info(f"Found {len(questions_data)} questions in payload")
                total_questions = len(questions_data)
                completed_questions = sum(1 for q in questions_data if q.get("status") == QUESTION_STATUS_COMPLETED)
                progress = int((completed_questions / total_questions * 100) if total_questions > 0 else 0)
                
                logger.info(f"Processing {total_questions} questions, {completed_questions} completed, progress: {progress}%")
                
                for i, question_data in enumerate(questions_data, 1):
                    try:
                        logger.info(f"Processing question {i}/{total_questions}: {question_data.get('question', '')[:50]}...")
                        # Get real knowledge base items for this question
                        from rfiprocessor.services.vector_store_service import vector_store_service
                        
                        try:
                            # Search for relevant knowledge base items based on the question
                            question_text = question_data.get("question", "")
                            if question_text:
                                similar_chunks = vector_store_service.search_similar_chunks(
                                    question_text,
                                    k=3
                                )
                                
                                kb_items = []
                                for j, chunk in enumerate(similar_chunks):
                                    metadata = chunk.get('metadata', {})
                                    content = chunk.get('content', '')
                                    
                                    kb_item = KnowledgeBaseItem(
                                        id=f"kb_{metadata.get('source_document_id', 'unknown')}_{j}",
                                        title=metadata.get('title', content.split('\n')[0][:50] if content else 'Knowledge Base Item'),
                                        category=metadata.get('category', metadata.get('document_grade', 'General')),
                                        snippet=content[:200] + "..." if len(content) > 200 else content,
                                        fullText=content
                                    )
                                    kb_items.append(kb_item)
                            else:
                                kb_items = question_data.get("knowledgeBase", [])
                                
                        except Exception as e:
                            logger.warning(f"Error getting knowledge base items for question {i}: {str(e)}")
                            kb_items = question_data.get("knowledgeBase", [])
                        
                        question_response = QuestionResponse(
                            id=question_data.get("id", i),
                            question=question_data.get("question", ""),
                            response=question_data.get("response", ""),
                            status=question_data.get("status", QUESTION_STATUS_PENDING),
                            assignedTo=question_data.get("assignedTo", "Unassigned"),
                            knowledgeBase=kb_items
                        )
                        questions.append(question_response)
                        logger.info(f"Added question {i} to response list. Total questions so far: {len(questions)}")
                    except Exception as e:
                        logger.error(f"Error processing question {i}: {str(e)}", exc_info=True)
                        # Continue with next question instead of breaking
                        continue
                    
            elif payload.get("saved_sections"):
                # Regular RFI workflow - questions are stored in 'saved_sections' array
                logger.info("Using 'saved_sections' array from regular RFI workflow")
                saved_sections = payload.get("saved_sections", [])
                total_sections = len(saved_sections)
                completed_sections = sum(1 for section in saved_sections if section.get("status") == QUESTION_STATUS_COMPLETED)
                progress = int((completed_sections / total_sections * 100) if total_sections > 0 else 0)
                
                for i, section in enumerate(saved_sections, 1):
                    # Get real knowledge base items for this question
                    from rfiprocessor.services.vector_store_service import vector_store_service
                    
                    try:
                        # Search for relevant knowledge base items based on the question
                        question_text = section.get("question", "")
                        if question_text:
                            similar_chunks = vector_store_service.search_similar_chunks(
                                question_text,
                                k=3
                            )
                            
                            kb_items = []
                            for j, chunk in enumerate(similar_chunks):
                                metadata = chunk.get('metadata', {})
                                content = chunk.get('content', '')
                                
                                kb_item = KnowledgeBaseItem(
                                    id=f"kb_{metadata.get('source_document_id', 'unknown')}_{j}",
                                    title=metadata.get('title', content.split('\n')[0][:50] if content else 'Knowledge Base Item'),
                                    category=metadata.get('category', metadata.get('document_grade', 'General')),
                                    snippet=content[:200] + "..." if len(content) > 200 else content,
                                    fullText=content
                                )
                                kb_items.append(kb_item)
                        else:
                            kb_items = []
                            
                    except Exception as e:
                        logger.warning(f"Error getting knowledge base items for question {i}: {str(e)}")
                        kb_items = []
                    
                    question_response = QuestionResponse(
                        id=i,
                        question=section.get("question", ""),
                        response=section.get("response", ""),
                        status=section.get("status", QUESTION_STATUS_PENDING),
                        assignedTo=section.get("user", "Unassigned"),
                        knowledgeBase=kb_items
                    )
                    questions.append(question_response)
            else:
                logger.warning("No questions or saved_sections found in payload")
                questions = []
                progress = 0
            
            logger.info(f"Final result: {len(questions)} questions prepared for response")
            
            # Determine current section being worked on
            current_section = "All Sections"
            if payload.get("questions"):
                # For draft answers workflow
                recent_questions = [q for q in payload.get("questions", []) if q.get("status") != QUESTION_STATUS_COMPLETED]
                if recent_questions:
                    current_section = f"Question: {recent_questions[0].get('id', 'Unknown')}"
            elif payload.get("saved_sections"):
                # For regular RFI workflow
                saved_sections = payload.get("saved_sections", [])
                recent_sections = [s for s in saved_sections if s.get("status") != QUESTION_STATUS_COMPLETED]
                if recent_sections:
                    current_section = f"Section: {recent_sections[0].get('questionId', 'Unknown')}"
            
            # Create metadata using real document information
            metadata = MetaData(
                source_document_id=rfi_document.id,
                source_filename=rfi_document.source_filename,
                document_type="RFI/RFP",
                company_name=rfi_document.title.split()[0] if rfi_document.title else "Unknown Company",
                domain="Clinical Research",  # Default domain for RFI documents
                question_type="mixed",  # RFI documents typically have mixed question types
                document_grade="Standard"
            )
            
            # Create the response
            response = SpecificRFIResponse(
                id=rfi_document.id,
                title=rfi_document.title,
                success=True,
                fileName=rfi_document.source_filename,
                status=rfi_document.status.value if rfi_document.status else RfiStatus.IN_PROGRESS.value,
                lastUpdated=rfi_document.updated_at.isoformat() + "Z" if rfi_document.updated_at else datetime.utcnow().isoformat() + "Z",
                section=current_section,
                progress=progress,
                questions=questions,
                metaData=metadata
            )
            
            logger.info(f"Successfully retrieved RFI details for responseId: {request.responseId}")
            
            return response
            
        finally:
            db_session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specific RFI details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
 
async def submit_review(request: SubmitReviewRequest):
    """
    Submit the completed RFI/RFP for review.
    
    Args:
        request: SubmitReviewRequest containing the responseId, status, and user
        
    Returns:
        SubmitReviewResponse: Success status and message
    """
    logger.info("=== SUBMITTING RFI FOR REVIEW ===")
    logger.info(f"Requested response ID: {request.responseId}")
    logger.info(f"Status: {request.status}")
    logger.info(f"User: {request.user}")
    
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
                        if section.get("id") == request.responseId:
                            rfi_document = doc
                            target_section = section
                            break
                    if rfi_document:
                        break
            
            if not rfi_document:
                logger.warning(f"RFI document not found containing responseId: {request.responseId}")
                raise HTTPException(status_code=404, detail="RFI document not found")
            
            logger.info(f"Found RFI document: {rfi_document.title}")
            
            # Extract saved sections from the RFI document
            payload = rfi_document.payload or {}
            saved_sections = payload.get("saved_sections", [])
            
            # Check if all questions are completed (progress should be 100%)
            total_sections = len(saved_sections)
            completed_sections = sum(1 for section in saved_sections if section.get("status") == QUESTION_STATUS_COMPLETED)
            progress = int((completed_sections / total_sections * 100) if total_sections > 0 else 0)
            
            logger.info(f"Total sections: {total_sections}")
            logger.info(f"Completed sections: {completed_sections}")
            logger.info(f"Progress: {progress}%")
            
            # Validate that all questions are completed and progress is 100%
            if progress < 100:
                logger.warning(f"Cannot submit for review: Progress is {progress}%, must be 100%")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot submit for review. Progress is {progress}%, all questions must be completed (100%)"
                )
            
            if completed_sections != total_sections:
                logger.warning(f"Cannot submit for review: {completed_sections}/{total_sections} sections completed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot submit for review. {completed_sections}/{total_sections} sections completed. All sections must be completed."
                )
            
            # Update the RFI document status to REVIEW_READY
            rfi_document.status = RfiStatus.REVIEW_READY
            rfi_document.updated_at = datetime.utcnow()
            rfi_document.updated_by_user = request.user
            
            # Commit the changes
            db_session.commit()
            
            logger.info(f"Successfully submitted RFI for review. Status updated to: {RfiStatus.REVIEW_READY.value}")
            
            return SubmitReviewResponse(
                message=f"RFI '{rfi_document.title}' successfully submitted for review by {request.user}",
                success=True
            )
            
        finally:
            db_session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting RFI for review: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")