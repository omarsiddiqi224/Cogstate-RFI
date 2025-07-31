# rfiprocessor/api/controller.py

from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import json
from datetime import datetime

# Import existing services and models
from config.config import Config
from rfiprocessor.db.database import init_db, get_db_session
from rfiprocessor.models.data_models import (
    FileUploadResponse,
    SaveSectionRequest,
    SaveSectionResponse,
    MarkCompleteRequest,
    MarkCompleteResponse,
    ActiveRFIListResponse,
    SpecificRFIRequest,
    SpecificRFIResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    KnowledgeBaseEntryResponse,
    AuditTrailResponse,
    SearchKnowledgeBaseRequest,
    SearchKnowledgeBaseResponse,
    DraftRequest,
    DraftResponse,
    ExportResponse
)
from rfiprocessor.utils.logger import get_logger

# Import API modules
from rfiprocessor.api.file_upload import upload_file
from rfiprocessor.api.document_status import get_document_status
from rfiprocessor.api.section_management import save_section, mark_complete
from rfiprocessor.api.rfi_management import get_active_rfi_list, get_specific_rfi_details, submit_review
from rfiprocessor.api.knowledge_base_management import add_knowledge_base_entry
from rfiprocessor.api.audit_trail_management import get_audit_trail
from rfiprocessor.api.knowledge_base_search import search_knowledge_base
from rfiprocessor.api.draft_generation import generate_draft
from rfiprocessor.api.draft_answers import process_draft_answers, create_response_from_processed_data
from rfiprocessor.api.export_markdown import export_rfi_to_markdown

# Initialize FastAPI app
app = FastAPI(
    title="RFI Processor API",
    description="API for processing RFI/RFP documents and generating draft answers",
    version="1.0.0"
)

# Initialize configuration and logger
config = Config()
logger = get_logger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()
    logger.info("Database initialized successfully")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "RFI Processor API is running", "status": "healthy"}

@app.get("/draft-answers/{document_id}", response_model=FileUploadResponse)
async def get_document_status_endpoint(document_id: str):
    """
    Get the current status and data for a processed document.
    
    Args:
        document_id: The unique document ID returned from the upload endpoint
    
    Returns:
        FileUploadResponse: Current document status and data
    """
    return await get_document_status(document_id)

@app.post("/draft-answers", response_model=FileUploadResponse)
async def upload_file_endpoint(
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
    return await process_draft_answers(background_tasks, file, fileName, fileType, size, user)

@app.post("/saveSection", response_model=SaveSectionResponse)
async def save_section_endpoint(request: SaveSectionRequest):
    """
    Save an updated section/answer for a specific question.
    
    Args:
        request: SaveSectionRequest containing the section data to save
    
    Returns:
        SaveSectionResponse: Success status and saved data
    """
    return await save_section(request)

@app.post("/markComplete", response_model=MarkCompleteResponse)
async def mark_complete_endpoint(request: MarkCompleteRequest):
    """
    Mark a section/question as complete by updating its status.
    
    Args:
        request: MarkCompleteRequest containing the section data to mark as complete
    
    Returns:
        MarkCompleteResponse: Success status and marked complete data
    """
    return await mark_complete(request)

@app.get("/activeRFIList", response_model=ActiveRFIListResponse)
async def get_active_rfi_list_endpoint():
    """
    Retrieve list of all active RFI/RFP documents.
    
    Returns:
        ActiveRFIListResponse: List of active RFI/RFP documents with their details
    """
    return await get_active_rfi_list()

@app.get("/response", response_model=SpecificRFIResponse)
async def get_specific_rfi_details_endpoint(id: str = Query(..., description="RFI response ID")):
    """
    Retrieve details of a specific RFI by responseId.
    
    Args:
        id: The response ID to get details for (query parameter)
    
    Returns:
        SpecificRFIResponse: Detailed information about the specific RFI
    """
    # Create a request object to pass to the existing function
    from rfiprocessor.models.data_models import SpecificRFIRequest
    request = SpecificRFIRequest(responseId=id)
    return await get_specific_rfi_details(request)

@app.post("/submitReview", response_model=SubmitReviewResponse)
async def submit_review_endpoint(request: SubmitReviewRequest):
    """
    Submit the completed RFI/RFP for review.
    
    Args:
        request: SubmitReviewRequest containing the responseId, status, and user
        
    Returns:
        SubmitReviewResponse: Success status and message
    """
    return await submit_review(request)

@app.post("/addKnowledgeBase", response_model=KnowledgeBaseEntryResponse)
async def add_knowledge_base_entry_endpoint(
    entryType: str = Form(...),
    serviceName: Optional[str] = Form(None),
    serviceCategory: Optional[str] = Form(None),
    description: str = Form(...),
    tags: str = Form(...),
    attachments: List[UploadFile] = File([])
):
    """
    Submit new knowledge base entries for approval.
    
    Args:
        entryType: Type of knowledge base entry
        serviceName: Service name for service entries
        serviceCategory: Service category for service entries
        description: Description of the knowledge base entry
        tags: Comma-separated tags
        attachments: List of uploaded files
    
    Returns:
        KnowledgeBaseEntryResponse: Success status and message
    """
    return await add_knowledge_base_entry(entryType, serviceName, serviceCategory, description, tags, attachments)

@app.post("/searchKnowledgeBase", response_model=List[SearchKnowledgeBaseResponse])
async def search_knowledge_base_endpoint(request: SearchKnowledgeBaseRequest):
    """
    Search the knowledge base using vector similarity search.
    
    Args:
        request: SearchKnowledgeBaseRequest containing the search text
    
    Returns:
        List[SearchKnowledgeBaseResponse]: List of knowledge base items matching the search
    """
    return await search_knowledge_base(request)

@app.post("/generateDraft", response_model=DraftResponse)
async def generate_draft_endpoint(request: DraftRequest):
    """
    Generate AI draft responses for RFI/RFP questions.
    
    Args:
        request: DraftRequest containing the responseId, questionId, question, response, status, and user
    
    Returns:
        DraftResponse: Success status and generated draft data
    """
    return await generate_draft(request)

@app.get("/auditTrail", response_model=AuditTrailResponse)
async def get_audit_trail_endpoint(id: str = Query(..., description="Response ID to get audit trail for")):
    """
    Retrieve audit history for a specific response.
    
    Args:
        id: The response ID to get audit trail for (query parameter)
    
    Returns:
        AuditTrailResponse: List of audit trail entries
    """
    return await get_audit_trail(id)

@app.get("/exportRFI/{response_id}", response_model=ExportResponse)
async def export_rfi_to_markdown_endpoint(response_id: str):
    """
    Export an RFI response to a downloadable Markdown file.
    
    Args:
        response_id: The ID of the RFI response to export
    
    Returns:
        ExportResponse: An ExportResponse containing the path to the downloaded file
    """
    return await export_rfi_to_markdown(response_id)

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a file from the temp_exports directory.
    
    Args:
        filename: The name of the file to download
    
    Returns:
        FileResponse: The file as a downloadable response
    """
    file_path = os.path.join(os.getcwd(), "temp_exports", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/markdown'
    )

 