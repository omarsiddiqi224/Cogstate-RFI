# rfiprocessor/api/file_upload.py

import os
import uuid
from datetime import datetime
from typing import List

from fastapi import File, UploadFile, Form, HTTPException, BackgroundTasks

from config.config import Config
from rfiprocessor.services.run_ingestion import IngestionPipeline
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.services.file_upload_service import FileUploadService
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Document, IngestionStatus, RfiStatus, QUESTION_STATUS_PENDING, QUESTION_STATUS_PROCESSING, QUESTION_STATUS_COMPLETED
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

async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fileName: str = Form(...),
    fileType: str = Form(...),
    size: int = Form(...),
    user: str = Form(default="test")
):
    """
    Upload RFI/RFP document files and extract markdown content.
    
    Args:
        file: Uploaded file
        fileName: Original file name
        fileType: File extension (pdf, docx, doc, xls, xlsx, md)
        size: File size in bytes
        user: User identifier (default: 'test')
    
    Returns:
        FileUploadResponse: Processing status and extracted data
    """
    logger.info("=== FILE UPLOAD STARTED ===")
    logger.info(f"Received upload request:")
    logger.info(f"  - fileName: '{fileName}'")
    logger.info(f"  - fileType: '{fileType}'")
    logger.info(f"  - size: {size} bytes")
    logger.info(f"  - user: '{user}'")
    logger.info(f"  - file.filename: '{file.filename}'")
    logger.info(f"  - file.content_type: '{file.content_type}'")
    
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
        
        # Save file using shared service
        incoming_path = await file_upload_service.save_file(file, actual_filename)
        
        # Register document in database
        logger.info("Registering document in database...")
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            db_handler = DatabaseHandler(db_session)
            document = db_handler.add_or_get_document(source_filepath=incoming_path)
            logger.info(f"Document registered in DB with ID: {document.id}")
            logger.info(f"Document status: {document.ingestion_status}")
            logger.info(f"Document filename: {document.source_filename}")
            
            # Start background processing
            logger.info("Starting background processing task...")
            background_tasks.add_task(process_document_background, document.id)
            
            # Create initial response
            logger.info("Creating initial response...")
            response = create_initial_response(document_id, actual_filename, document.id)
            
            logger.info(f"File uploaded successfully: {actual_filename}, Document ID: {document_id}")
            logger.info("=== FILE UPLOAD COMPLETED ===")
            return response
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

def create_initial_response(
    document_id: str, fileName: str, db_document_id: int
) -> FileUploadResponse:
    """Create initial response for file upload."""
    logger.info(f"Creating initial response for document ID: {db_document_id}")
    logger.info(f"Using fileName: '{fileName}'")
    
    # Get document from database to check if it's already processed
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        document = (
            db_session.query(Document)
            .filter(Document.id == db_document_id)
            .first()
        )
        
        logger.info(f"Retrieved document from DB:")
        logger.info(f"  - Document ID: {document.id if document else 'None'}")
        logger.info(f"  - Source filename: {document.source_filename if document else 'None'}")
        logger.info(f"  - Ingestion status: {document.ingestion_status if document else 'None'}")
        logger.info(f"  - Has RFI payload: {bool(document.rfi_json_payload) if document else False}")
        
        if not document:
            logger.error("Document not found in database")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is already processed
        if (document.ingestion_status == IngestionStatus.VECTORIZED 
                and document.rfi_json_payload):
            logger.info("Document is fully processed, using parsed data")
            # Use real parsed data
            return create_response_from_parsed_data(
                document_id, fileName, document
            )
        else:
            logger.info("Document is still processing, using processing response")
            # Return initial response for processing
            return create_processing_response(
                document_id, fileName, document
            )
            
    finally:
        db_session.close()

def create_response_from_parsed_data(document_id: str, fileName: str, document: Document) -> FileUploadResponse:
    """Create response using real parsed RFI data."""
    try:
        # Extract data from the parsed RFI JSON payload
        rfi_data = document.rfi_json_payload
        
        if not rfi_data or not rfi_data.get('qa_pairs'):
            logger.warning(
                f"No QA pairs found in parsed data for document {document.id}"
            )
            return create_processing_response(document_id, fileName, document)
        
        # Initialize the inference pipeline components (same as run_inference_for_rfi)
        try:
            from rfiprocessor.core.agents.answer_generator import AnswerGeneratorAgent
            from rfiprocessor.services.vector_store_service import VectorStoreService
            
            vector_handler = VectorStoreService()
            answer_generator = AnswerGeneratorAgent()
            logger.info("Inference pipeline components initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize inference components: {e}")
            vector_handler = None
            answer_generator = None
        
        # Convert QA pairs to QuestionResponse format using the exact logic from run_inference_for_rfi
        questions = []
        for i, qa_pair in enumerate(rfi_data.get('qa_pairs', []), 1):
            question_text = qa_pair.get('question', '')
            answer_text = qa_pair.get('answer', '')
            
            # Use the exact logic from run_inference_for_rfi
            if vector_handler and answer_generator:
                try:
                    # Search for similar chunks (same as in run_inference_for_rfi)
                    context_chunks = vector_handler.search_similar_chunks(question_text, k=5)
                    
                    # Generate answer using the answer generator (same as in run_inference_for_rfi)
                    if context_chunks:
                        draft_answer = answer_generator.generate_answer(question_text, context_chunks)
                        answer_text = draft_answer
                    else:
                        answer_text = "No relevant information was found in the knowledge base to answer this question."
                    
                    # Create knowledge base items from context chunks (same format as run_inference_for_rfi)
                    kb_items = [
                        KnowledgeBaseItem(
                            id=f"kb_{c['metadata'].get('source_document_id', 0)}_{j}",
                            title=c['metadata'].get('source_filename', 'Unknown'),
                            category=c['metadata'].get('document_grade', 'General'),
                            snippet=c['content'][:250] + "..." if len(c['content']) > 250 else c['content'],
                            fullText=c['content']
                        )
                        for j, c in enumerate(context_chunks)
                    ]
                    
                    logger.info(f"Generated answer for question {i}: {answer_text[:100]}...")
                    
                except Exception as e:
                    logger.warning(f"Failed to generate answer for question {i}: {e}")
                    answer_text = "Answer to be generated based on knowledge base."
                    kb_items = []
            else:
                # Fallback to the old method if inference components failed
                kb_items = []
                if not answer_text or answer_text.strip() == '':
                    answer_text = "Answer to be generated based on knowledge base."
            
            question_response = QuestionResponse(
                id=i,
                question=question_text,
                response=answer_text,
                status=QUESTION_STATUS_PENDING,
                assignedTo="AI Assistant",
                knowledgeBase=kb_items
            )
            questions.append(question_response)
        
        # Create metadata from parsed data
        meta_data = rfi_data.get('meta_data', {})
        metadata = MetaData(
            source_document_id=document.id,
            source_filename=fileName,
            document_type=document.document_type or config.DEFAULT_DOCUMENT_TYPE,
            company_name=meta_data.get('company_name', 'Unknown'),
            domain=meta_data.get('category', 'Unknown'),
            question_type="mixed",
            document_grade=document.document_grade or config.DEFAULT_DOCUMENT_GRADE_STANDARD
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
            lastUpdated=document.updated_at,
            section="All Sections",
            progress=100,
            questions=questions,
            metaData=metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating response from parsed data: {str(e)}", exc_info=True)
        # Fallback to processing response
        return create_processing_response(document_id, fileName, document)

def create_processing_response(document_id: str, fileName: str, document: Document) -> FileUploadResponse:
    """Create response for documents still being processed."""
    logger.info(f"Creating processing response for document: {document.id}")
    logger.info(f"Document status: {document.ingestion_status}")
    logger.info(f"Document filename: {document.source_filename}")
    
    # Check if we have any parsed data available
    questions = []
    if document.rfi_json_payload and document.rfi_json_payload.get('qa_pairs'):
        # Use regular RFI format (qa_pairs)
        qa_pairs = document.rfi_json_payload.get('qa_pairs', [])
        
        # Show all questions if document is fully processed, otherwise show first 5
        max_questions = len(qa_pairs) if document.ingestion_status == IngestionStatus.VECTORIZED else min(5, len(qa_pairs))
        
        for i, qa_pair in enumerate(qa_pairs[:max_questions], 1):
            # Use real question and answer from the parsed RFI
            question_text = qa_pair.get('question', '')
            answer_text = qa_pair.get('answer', '')
            
            # If no answer is provided, generate a placeholder
            if not answer_text or answer_text.strip() == '':
                answer_text = "Answer to be generated based on knowledge base."
            
            # Determine status based on ingestion status
            question_status = QUESTION_STATUS_PENDING if document.ingestion_status == IngestionStatus.VECTORIZED else QUESTION_STATUS_PROCESSING
            
            question_response = QuestionResponse(
                id=i,
                question=question_text,
                response=answer_text,
                status=question_status,
                assignedTo="AI Assistant",
                knowledgeBase=[]
            )
            questions.append(question_response)
    else:
        # Placeholder questions while processing
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
    
    # Try to get real metadata from parsed data if available
    if document.rfi_json_payload and document.rfi_json_payload.get('meta_data'):
        meta_data = document.rfi_json_payload.get('meta_data', {})
        metadata = MetaData(
            source_document_id=document.id,
            source_filename=fileName,
            document_type=document.document_type or config.DEFAULT_DOCUMENT_TYPE,
            company_name=meta_data.get('company_name', 'Processing...'),
            domain=meta_data.get('category', 'Processing...'),
            question_type="mixed",
            document_grade=document.document_grade or config.DEFAULT_DOCUMENT_GRADE_PROCESSING
        )
    else:
        metadata = MetaData(
            source_document_id=document.id,
            source_filename=fileName,
            document_type=document.document_type or config.DEFAULT_DOCUMENT_TYPE,
            company_name="Processing...",
            domain="Processing...",
            question_type="processing",
            document_grade=document.document_grade or config.DEFAULT_DOCUMENT_GRADE_PROCESSING
        )
    
    # Calculate progress based on ingestion status
    progress_map = {
        IngestionStatus.PENDING: 0,
        IngestionStatus.MARKDOWN_CONVERTED: 20,
        IngestionStatus.CLASSIFIED: 40,
        IngestionStatus.PARSED: 60,
        IngestionStatus.CHUNKED: 80,
        IngestionStatus.VECTORIZED: 100
    }
    
    progress = progress_map.get(document.ingestion_status, 0)
    
    # Create title from company name or filename
    title = f"Processing {fileName}"
    if document.rfi_json_payload and document.rfi_json_payload.get('meta_data'):
        meta_data = document.rfi_json_payload.get('meta_data', {})
        company_name = meta_data.get('company_name', '')
        if company_name and company_name != 'Unknown':
            title = f"Processing {company_name} RFI"
    
    return FileUploadResponse(
        id=document_id,
        title=title,
        success=True,
        fileName=fileName,
        status=RfiStatus.IN_PROGRESS.value,
        lastUpdated=document.updated_at,
        section="Processing...",
        progress=progress,
        questions=questions,
        metaData=metadata
    )

async def process_document_background(document_id: int) -> None:
    """Background task to process the uploaded document."""
    try:
        logger.info(f"=== BACKGROUND PROCESSING STARTED ===")
        logger.info(f"Processing document ID: {document_id}")
        
        # Run the ingestion pipeline
        logger.info("Initializing ingestion pipeline...")
        pipeline = IngestionPipeline()
        
        logger.info("Running full ingestion pipeline...")
        pipeline.run_full_pipeline()
        
        # Check if the document was processed
        db_session_generator = get_db_session()
        db_session = next(db_session_generator)
        try:
            document = db_session.query(Document).filter(Document.id == document_id).first()
            if document:
                logger.info(f"Document processing status: {document.ingestion_status}")
                logger.info(f"Document has RFI payload: {bool(document.rfi_json_payload)}")
            else:
                logger.warning(f"Document ID {document_id} not found after processing")
        finally:
            db_session.close()
        
        logger.info(f"Background processing completed for document ID: {document_id}")
        logger.info("=== BACKGROUND PROCESSING COMPLETED ===")
        
    except Exception as e:
        logger.error(f"Error processing document background: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")