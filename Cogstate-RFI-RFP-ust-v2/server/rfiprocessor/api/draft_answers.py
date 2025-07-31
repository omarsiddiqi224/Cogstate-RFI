# rfiprocessor/api/draft_answers.py

import os
import uuid
import json
import shutil
from datetime import datetime
from typing import List

from fastapi import File, UploadFile, Form, HTTPException, BackgroundTasks

from config.config import Config
from rfiprocessor.services.markdown_converter import MarkdownConverter
from rfiprocessor.core.agents.blank_rfi_parser import BlankRfiParserAgent
from rfiprocessor.core.agents.answer_generator import AnswerGeneratorAgent
from rfiprocessor.services.vector_store_service import VectorStoreService
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.services.file_upload_service import FileUploadService
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Document, IngestionStatus, RfiStatus, RfiDocument, QUESTION_STATUS_PENDING, QUESTION_STATUS_PROCESSING, QUESTION_STATUS_COMPLETED
from rfiprocessor.models.data_models import (
    FileUploadResponse,
    QuestionResponse,
    KnowledgeBaseItem,
    MetaData
)
from rfiprocessor.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)
file_upload_service = FileUploadService()

async def process_draft_answers(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fileName: str = Form(...),
    fileType: str = Form(...),
    size: int = Form(...),
    user: str = Form(default="test")
):
    """
    Process blank RFI documents using the blank RFI parser for draft answers.
    
    Flow:
    1. Convert document to markdown
    2. Use blank RFI parser to extract questions (no answers)
    3. Save JSON in blank json directory
    4. Run inference pipeline to find answers from vector store
    5. Return structured response
    
    Args:
        file: Uploaded file
        fileName: Original file name
        fileType: File extension (pdf, docx, doc, xls, xlsx, md)
        size: File size in bytes
        user: User identifier (default: 'test')
    
    Returns:
        FileUploadResponse: Processing status and extracted data
    """
    logger.info("=== DRAFT ANSWERS PROCESSING STARTED ===")
    logger.info(f"Received draft answers request:")
    logger.info(f"  - fileName: '{fileName}'")
    logger.info(f"  - fileType: '{fileType}'")
    logger.info(f"  - size: {size} bytes")
    logger.info(f"  - user: '{user}'")
    
    try:
        # Validate file using shared service
        file_upload_service.validate_file_size(size)
        file_upload_service.validate_file_extension(
            filename=fileName,
            file_type=fileType,
            content_type=file.content_type
        )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        logger.info(f"Generated document ID: {document_id}")
        
        # Use actual file information instead of form parameters
        actual_filename = file.filename or fileName
        actual_file_type = file.content_type or fileType
        actual_size = file.size or size
        
        logger.info(f"Using actual file data:")
        logger.info(f"  - Actual filename: '{actual_filename}'")
        logger.info(f"  - Actual content type: '{actual_file_type}'")
        logger.info(f"  - Actual size: {actual_size} bytes")
        
        # Save file to blank incoming directory
        blank_incoming_path = os.path.join("data/blank/incoming", actual_filename)
        os.makedirs(os.path.dirname(blank_incoming_path), exist_ok=True)
        
        # Ensure file stream is at the beginning
        await file.seek(0)
        
        # Read the file content and save it
        content = await file.read()
        with open(blank_incoming_path, "wb") as buffer:
            buffer.write(content)
        
        incoming_path = blank_incoming_path
        logger.info(f"File saved to blank incoming directory: {incoming_path}")
        
        # Create RfiDocument entry for draft answers
        logger.info("Creating RfiDocument entry for draft answers...")
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            
            # Create RfiDocument entry
            rfi_document = RfiDocument(
                title=f"Draft Answers - {actual_filename}",
                source_filename=actual_filename,
                number_of_questions=0,
                status=RfiStatus.IN_PROGRESS,
                progress=0,
                updated_by_user=user
            )
            
            db_session.add(rfi_document)
            db_session.commit()
            db_session.refresh(rfi_document)
            
            logger.info(f"RfiDocument created with ID: {rfi_document.id}")
            
            # Process the document immediately (not in background)
            logger.info("Processing draft answers immediately...")
            await process_draft_answers_background(rfi_document.id, incoming_path)
            
            # Get the processed results directly from database
            logger.info("Getting processed results from database...")
            db_session.refresh(rfi_document)
            
            if rfi_document.payload and rfi_document.payload.get('questions'):
                logger.info("Returning processed results with questions and answers")
                response = create_response_from_processed_data(document_id, actual_filename, rfi_document)
            else:
                logger.error("No processed results found in database")
                raise HTTPException(status_code=500, detail="Processing failed - no results found")
            
            logger.info(f"Draft answers processing completed: {actual_filename}, Document ID: {document_id}")
            logger.info("=== DRAFT ANSWERS PROCESSING COMPLETED ===")
            return response
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error processing draft answers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def create_initial_draft_response(
    document_id: str, fileName: str, rfi_document_id: str
) -> FileUploadResponse:
    """Create initial response for draft answers processing."""
    logger.info(f"Creating initial draft response for RfiDocument ID: {rfi_document_id}")
    
    # Get RfiDocument from database
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        rfi_document = (
            db_session.query(RfiDocument)
            .filter(RfiDocument.id == rfi_document_id)
            .first()
        )
        
        if not rfi_document:
            logger.error("RfiDocument not found in database")
            raise HTTPException(status_code=404, detail="RfiDocument not found")
        
        # Check if RfiDocument is already processed and has results
        if (rfi_document.payload 
                and rfi_document.payload.get('questions')):
            logger.info("RfiDocument is already processed, returning actual results")
            return create_response_from_processed_data(document_id, fileName, rfi_document)
        
        # Create placeholder questions while processing
        questions = [
            QuestionResponse(
                id=1,
                question="Processing blank RFI document...",
                response="Document is being analyzed and questions are being extracted. Please wait.",
                status=QUESTION_STATUS_PROCESSING,
                assignedTo="AI Assistant",
                knowledgeBase=[]
            )
        ]
        
        # Create metadata
        metadata = MetaData(
            source_document_id=rfi_document.id,
            source_filename=fileName,
            document_type="RFI/RFP",
            company_name="Processing...",
            domain="Processing...",
            question_type="mixed",
            document_grade="Standard"
        )
        
        # Create title
        title = f"Processing {fileName}"
        
        return FileUploadResponse(
            id=document_id,
            title=title,
            success=True,
            fileName=fileName,
            status=RfiStatus.IN_PROGRESS.value,
            lastUpdated=rfi_document.updated_at,
            section="Processing...",
            progress=10,
            questions=questions,
            metaData=metadata
        )
            
    finally:
        db_session.close()

def create_response_from_processed_data(document_id: str, fileName: str, rfi_document: RfiDocument) -> FileUploadResponse:
    """Create response from already processed draft answers data."""
    try:
        # Extract data from the processed RFI payload
        rfi_data = rfi_document.payload
        
        # Convert questions to QuestionResponse format
        questions = []
        for question_data in rfi_data.get('questions', []):
            question_response = QuestionResponse(
                id=question_data.get('id', 0),
                question=question_data.get('question', ''),
                response=question_data.get('response', ''),
                status=question_data.get('status', config.QUESTION_STATUS_DRAFT),
                assignedTo=question_data.get('assignedTo', 'AI Assistant'),
                knowledgeBase=question_data.get('knowledgeBase', [])
            )
            questions.append(question_response)
        
        # Create metadata from processed data
        meta_data = rfi_data.get('meta_data', {})
        metadata = MetaData(
            source_document_id=rfi_document.id,
            source_filename=fileName,
            document_type="RFI/RFP",
            company_name=meta_data.get('company_name', 'Unknown'),
            domain=meta_data.get('category', 'Unknown'),
            question_type="mixed",
            document_grade="Standard"
        )
        
        # Create title from company name or filename
        title = f"{meta_data.get('company_name', 'Unknown')} RFI"
        if title == "Unknown RFI":
            title = f"{os.path.splitext(fileName)[0]} RFI"
        
        return FileUploadResponse(
            id=document_id,
            title=title,
            success=True,
            fileName=fileName,
            status=RfiStatus.NOT_STARTED.value,
            lastUpdated=rfi_document.updated_at,
            section="All Sections",
            progress=0,
            questions=questions,
            metaData=metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating response from processed data: {str(e)}", exc_info=True)
        # Fallback to processing response
        return create_processing_response(document_id, fileName, rfi_document)

def create_processing_response(document_id: str, fileName: str, rfi_document: RfiDocument) -> FileUploadResponse:
    """Create response for documents still being processed."""
    logger.info(f"Creating processing response for RfiDocument: {rfi_document.id}")
    
    # Create placeholder questions while processing
    questions = [
        QuestionResponse(
            id=1,
            question="Processing in progress...",
            response="Document is being analyzed and parsed. Please wait.",
            status=QUESTION_STATUS_PROCESSING,
            assignedTo="AI Assistant",
            knowledgeBase=[]
        )
    ]
    
    # Create metadata
    metadata = MetaData(
        source_document_id=rfi_document.id,
        source_filename=fileName,
        document_type="RFI/RFP",
        company_name="Processing...",
        domain="Processing...",
        question_type="processing",
        document_grade="Standard"
    )
    
    # Create title
    title = f"Processing {fileName}"
    
    return FileUploadResponse(
        id=document_id,
        title=title,
        success=True,
        fileName=fileName,
        status=RfiStatus.IN_PROGRESS.value,
        lastUpdated=rfi_document.updated_at,
        section="Processing...",
        progress=10,
        questions=questions,
        metaData=metadata
    )

async def process_draft_answers_background(rfi_document_id: str, file_path: str):
    """Background task to process the blank RFI document for draft answers."""
    try:
        logger.info(f"=== BACKGROUND DRAFT ANSWERS PROCESSING STARTED ===")
        logger.info(f"Processing RfiDocument ID: {rfi_document_id}")
        
        # Step 1: Convert document to markdown and save to blank markdown directory
        logger.info("Converting document to markdown...")
        converter = MarkdownConverter()
        markdown_content, markdown_path = converter.convert_to_markdown(file_path)
        
        # Move markdown file to blank markdown directory
        blank_markdown_dir = "data/blank/markdown"
        os.makedirs(blank_markdown_dir, exist_ok=True)
        blank_markdown_path = os.path.join(blank_markdown_dir, os.path.basename(markdown_path))
        shutil.move(markdown_path, blank_markdown_path)
        markdown_path = blank_markdown_path
        logger.info(f"Markdown file moved to blank directory: {markdown_path}")
        
        # Step 2: Use blank RFI parser to extract questions
        logger.info("Using blank RFI parser to extract questions...")
        llm_instance = get_advanced_llm()
        blank_parser = BlankRfiParserAgent(llm=llm_instance)
        parsed_data = blank_parser.parse(markdown_content)
        
        # Step 3: Save JSON in blank json directory
        logger.info("Saving parsed JSON in blank json directory...")
        save_blank_json(parsed_data, file_path)
        
        # Step 4: Run inference pipeline to find answers
        logger.info("Running inference pipeline to find answers...")
        questions_with_answers = run_inference_for_questions(parsed_data.get("questions", []))
        
        # Step 5: Update database with results
        logger.info("Updating database with results...")
        update_database_with_results(rfi_document_id, parsed_data, questions_with_answers)
        
        # Step 6: Move original file to processed directory
        logger.info("Moving original file to processed directory...")
        try:
            processed_dir = "data/blank/processed"
            os.makedirs(processed_dir, exist_ok=True)
            
            original_filename = os.path.basename(file_path)
            processed_path = os.path.join(processed_dir, original_filename)
            
            # Check if file exists before moving
            if os.path.exists(file_path):
                # Handle case where file already exists in processed directory
                if os.path.exists(processed_path):
                    # Add timestamp to filename to avoid conflicts
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    name, ext = os.path.splitext(original_filename)
                    new_filename = f"{name}_{timestamp}{ext}"
                    processed_path = os.path.join(processed_dir, new_filename)
                    logger.info(f"File already exists in processed directory, using new name: {new_filename}")
                
                shutil.move(file_path, processed_path)
                logger.info(f"Original file moved to processed directory: {processed_path}")
            else:
                logger.warning(f"Original file not found at {file_path}, skipping move to processed directory")
        except Exception as e:
            logger.error(f"Error moving file to processed directory: {str(e)}", exc_info=True)
            # Don't fail the entire process if file move fails
        
        logger.info(f"Background draft answers processing completed for RfiDocument ID: {rfi_document_id}")
        logger.info("=== BACKGROUND DRAFT ANSWERS PROCESSING COMPLETED ===")
        
    except Exception as e:
        logger.error(f"Error processing draft answers background: {str(e)}", exc_info=True)
        # Update database with error status
        update_database_with_error(rfi_document_id, str(e))

def save_blank_json(parsed_data: dict, original_file_path: str) -> str:
    """Save parsed data to blank json directory."""
    try:
        # Create blank json directory if it doesn't exist
        blank_json_dir = "data/blank/json"
        os.makedirs(blank_json_dir, exist_ok=True)
        
        # Generate filename based on original file
        original_filename = os.path.basename(original_file_path)
        base_name = os.path.splitext(original_filename)[0]
        json_filename = f"{base_name}_blank.json"
        json_path = os.path.join(blank_json_dir, json_filename)
        
        # Save the parsed data
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved blank RFI JSON to: {json_path}")
        return json_path
        
    except Exception as e:
        logger.error(f"Error saving blank JSON: {str(e)}", exc_info=True)
        raise

def run_inference_for_questions(questions: List[dict]) -> List[dict]:
    """Run inference pipeline to find answers for questions from vector store."""
    try:
        logger.info(f"Running inference for {len(questions)} questions...")
        
        # Initialize inference components
        vector_handler = VectorStoreService()
        answer_generator = AnswerGeneratorAgent()
        
        questions_with_answers = []
        
        for i, question_data in enumerate(questions, 1):
            question_text = question_data.get("question", "")
            logger.info(f"Processing question {i}/{len(questions)}: {question_text[:70]}...")
            
            try:
                # Search for similar chunks in vector store
                logger.info(f"Searching vector store for question: {question_text[:100]}...")
                context_chunks = vector_handler.search_similar_chunks(question_text, k=5)
                logger.info(f"Found {len(context_chunks)} context chunks for question {i}")
                
                # Generate answer using the answer generator
                if context_chunks:
                    logger.info(f"Generating answer using {len(context_chunks)} context chunks...")
                    draft_answer = answer_generator.generate_answer(question_text, context_chunks)
                    logger.info(f"Generated answer: {draft_answer[:100]}...")
                else:
                    logger.warning(f"No context chunks found for question {i}")
                    draft_answer = "No relevant information was found in the knowledge base to answer this question."
                
                # Create knowledge base items from context chunks
                kb_items = [
                    {
                        "id": f"kb_{c['metadata'].get('source_document_id', 0)}_{j}",
                        "title": c['metadata'].get('source_filename', 'Unknown'),
                        "category": c['metadata'].get('document_grade', 'General'),
                        "snippet": c['content'][:250] + "..." if len(c['content']) > 250 else c['content'],
                        "fullText": c['content']
                    }
                    for j, c in enumerate(context_chunks)
                ]
                
                # Create question with answer
                question_with_answer = {
                    "id": i,
                    "question": question_text,
                    "response": draft_answer,
                    "status": config.QUESTION_STATUS_DRAFT,
                    "assignedTo": "AI Assistant",
                    "knowledgeBase": kb_items
                }
                
                questions_with_answers.append(question_with_answer)
                logger.info(f"Generated answer for question {i}: {draft_answer[:100]}...")
                
            except Exception as e:
                logger.warning(f"Failed to generate answer for question {i}: {e}")
                # Create question with error response
                question_with_answer = {
                    "id": i,
                    "question": question_text,
                    "response": "",
                    "status": config.QUESTION_STATUS_DRAFT,
                    "assignedTo": "AI Assistant",
                    "knowledgeBase": []
                }
                questions_with_answers.append(question_with_answer)
        
        logger.info(f"Successfully processed {len(questions_with_answers)} questions")
        return questions_with_answers
        
    except Exception as e:
        logger.error(f"Error running inference for questions: {str(e)}", exc_info=True)
        raise

def update_database_with_results(rfi_document_id: str, parsed_data: dict, questions_with_answers: List[dict]):
    """Update database with the processed results."""
    try:
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            
            # Create the final payload structure
            meta_data = parsed_data.get("meta_data", {})
            final_payload = {
                "id": rfi_document_id,
                "title": meta_data.get("company_name", "Draft Answers"),
                "fileName": meta_data.get("source_filename", "Unknown"),
                "status": RfiStatus.IN_PROGRESS.value,
                "lastUpdated": datetime.utcnow().isoformat(),
                "progress": 0,
                "questions": questions_with_answers,
                "meta_data": meta_data
            }
            
            # Update RfiDocument with results
            updates = {
                "payload": final_payload,
                "status": RfiStatus.IN_PROGRESS,
                "progress": 0,
                "number_of_questions": len(questions_with_answers),
                "updated_by_user": "AI Assistant"
            }
            
            db_handler.update_record(rfi_document_id, updates, model_class=RfiDocument)
            logger.info(f"Successfully updated database for RfiDocument ID: {rfi_document_id}")
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error updating database with results: {str(e)}", exc_info=True)
        raise

def update_database_with_error(rfi_document_id: str, error_message: str):
    """Update database with error status."""
    try:
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            
            updates = {
                "status": RfiStatus.FAILED,
                "payload": {
                    "error": error_message
                }
            }
            
            db_handler.update_record(rfi_document_id, updates, model_class=RfiDocument)
            logger.info(f"Updated database with error for RfiDocument ID: {rfi_document_id}")
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error updating database with error: {str(e)}", exc_info=True) 