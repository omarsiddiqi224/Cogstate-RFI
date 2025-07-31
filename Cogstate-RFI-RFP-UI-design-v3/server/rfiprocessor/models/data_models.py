# rfiprocessor/models/data_models.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import date, datetime
import uuid

# Define a literal type for the question types for strict validation
QuestionType = Literal["narrative", "open-ended", "close-ended", "check-box"]

class QAPair(BaseModel):
    """Pydantic model for a single Question-Answer pair."""
    question: str = Field(..., description="The question text from the RFI/RFP.")
    answer: str = Field(..., description="The corresponding answer text.")
    domain: Optional[str] = Field(None, description="The business or technical domain of the question.")
    type: Optional[QuestionType] = Field(None, description="The type of the question.")

class RfiMetadata(BaseModel):
    """Pydantic model for the metadata of an RFI/RFP document."""
    company_name: str = Field(..., description="The name of the company the RFI/RFP is for.")
    doc_date: Optional[date] = Field(None, description="The date of the document.")
    category: Literal["RFI", "RFP"] = Field(..., description="The category of the document.")
    type: Literal["PastResponse"] = Field(..., description="The type of the content.")

class RFIJson(BaseModel):
    """
    The main Pydantic model to validate the entire JSON structure
    parsed from an RFI/RFP document.
    """
    summary: Optional[str] = Field(None, description="A brief summary of the RFI/RFP document.")
    description: Optional[str] = Field(None, description="A more detailed description of the document's content.")
    qa_pairs: List[QAPair] = Field(..., description="A list of all question-answer pairs found in the document.")
    meta_data: RfiMetadata = Field(..., description="Metadata associated with the document.")

    @field_validator('qa_pairs')
    @classmethod
    def check_qa_pairs_not_empty(cls, v: List[QAPair]) -> List[QAPair]:
        """Ensures that the qa_pairs list is not empty."""
        if not v:
            raise ValueError('qa_pairs list cannot be empty')
        return v

# API Request Models
class FileUploadRequest(BaseModel):
    """Request model for file upload endpoint."""
    fileName: str = Field(..., description="Original file name")
    fileType: str = Field(..., description="File extension (pdf, docx, doc, xls, xlsx, md)")
    size: int = Field(..., description="File size in bytes")
    user: str = Field(default="test", description="User identifier")

# API Response Models
class KnowledgeBaseItem(BaseModel):
    """Model for knowledge base items in question responses."""
    id: str = Field(..., description="Knowledge base item ID")
    title: str = Field(..., description="Knowledge base item title")
    category: str = Field(..., description="Category of the knowledge base item")
    snippet: str = Field(..., description="Snippet of the knowledge base content")
    fullText: str = Field(default="", description="Full text of the knowledge base item")

class QuestionResponse(BaseModel):
    """Model for individual question responses."""
    id: int = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    response: str = Field(..., description="Response text in markdown format")
    status: str = Field(..., description="Status of the question (completed, pending, etc.)")
    assignedTo: str = Field(..., description="Person assigned to the question")
    knowledgeBase: List[KnowledgeBaseItem] = Field(default=[], description="Related knowledge base items")

class MetaData(BaseModel):
    """Model for document metadata."""
    source_document_id: str = Field(..., description="Source document ID")
    source_filename: str = Field(..., description="Source filename")
    document_type: str = Field(..., description="Type of document")
    company_name: str = Field(..., description="Company name")
    domain: str = Field(..., description="Domain of the document")
    question_type: str = Field(..., description="Type of questions in the document")
    document_grade: str = Field(..., description="Document grade/classification")

class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint."""
    id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    success: bool = Field(..., description="Success status")
    fileName: str = Field(..., description="Original file name")
    status: str = Field(..., description="Processing status")
    lastUpdated: datetime = Field(..., description="Last updated timestamp")
    section: str = Field(..., description="Current section being processed")
    progress: int = Field(..., description="Processing progress percentage")
    questions: List[QuestionResponse] = Field(..., description="List of questions and responses")
    metaData: MetaData = Field(..., description="Document metadata")

# Knowledge Base API Models
class KnowledgeBaseEntryRequest(BaseModel):
    """Request model for knowledge base entry."""
    entryType: str = Field(..., description="Type of knowledge base entry")
    serviceName: Optional[str] = Field(None, description="Service name for service entries")
    serviceCategory: Optional[str] = Field(None, description="Service category for service entries")
    description: str = Field(..., description="Description of the knowledge base entry")
    tags: str = Field(..., description="Comma-separated tags")

class KnowledgeBaseEntryResponse(BaseModel):
    """Response model for knowledge base entry."""
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Success status")

# Search Knowledge Base API Models
class SearchKnowledgeBaseRequest(BaseModel):
    """Request model for searching knowledge base."""
    searchText: str = Field(..., description="Search keyword to find in knowledge base")

class SearchKnowledgeBaseResponse(BaseModel):
    """Response model for search knowledge base endpoint."""
    id: str = Field(..., description="Knowledge base item ID")
    title: str = Field(..., description="Knowledge base item title")
    category: str = Field(..., description="Category of the knowledge base item")
    snippet: str = Field(..., description="Snippet of the knowledge base content")
    fullText: str = Field(default="", description="Full text of the knowledge base item")

# Save Section API Models
class SaveSectionRequest(BaseModel):
    """Request model for saving a section/answer."""
    responseId: str = Field(..., description="Unique response ID")
    questionId: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    response: str = Field(..., description="Updated answer text in markdown format")
    status: str = Field(..., description="Status of the section")
    user: str = Field(..., description="User who is saving the section")

class SaveSectionResponse(BaseModel):
    """Response model for save section endpoint."""
    success: bool = Field(..., description="Success status")
    data: dict = Field(..., description="Saved section data")

# Mark Complete API Models
class MarkCompleteRequest(BaseModel):
    """Request model for marking a section as complete."""
    responseId: str = Field(..., description="Unique response ID")
    questionId: str = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")
    response: str = Field(..., description="Answer text in markdown format")
    status: str = Field(..., description="Status of the section (should be 'completed')")
    user: str = Field(..., description="User who is marking the section as complete")

class MarkCompleteResponse(BaseModel):
    """Response model for mark complete endpoint."""
    success: bool = Field(..., description="Success status")
    data: dict = Field(..., description="Marked complete section data")

# Active RFI List API Models
class ActiveRFIUser(BaseModel):
    """Model for users working on an RFI."""
    name: str = Field(..., description="User name")

class ActiveRFIItem(BaseModel):
    """Model for individual active RFI/RFP item."""
    id: str = Field(..., description="RFI document ID")
    title: str = Field(..., description="RFI title")
    status: str = Field(..., description="Current status")
    updated: str = Field(..., description="Last updated timestamp")
    dueDate: str = Field(..., description="Due date")
    section: str = Field(..., description="Current section being worked on")
    progress: int = Field(..., description="Progress percentage")
    users: List[ActiveRFIUser] = Field(..., description="List of users working on this RFI")

class ActiveRFIListResponse(BaseModel):
    """Response model for active RFI list endpoint."""
    success: bool = Field(..., description="Success status")
    data: List[ActiveRFIItem] = Field(..., description="List of active RFI/RFP documents (double array as per spec)")

# Specific RFI Details API Models
class SpecificRFIRequest(BaseModel):
    """Request model for getting specific RFI details."""
    responseId: str = Field(..., description="RFI response ID")

class SpecificRFIResponse(BaseModel):
    """Response model for specific RFI details endpoint."""
    id: str = Field(..., description="RFI document ID")
    title: str = Field(..., description="RFI title")
    success: bool = Field(..., description="Success status")
    fileName: str = Field(..., description="Source filename")
    status: str = Field(..., description="Current status")
    lastUpdated: str = Field(..., description="Last updated timestamp")
    section: str = Field(..., description="Current section")
    progress: int = Field(..., description="Progress percentage")
    questions: List[QuestionResponse] = Field(..., description="List of questions and responses")
    metaData: MetaData = Field(..., description="Document metadata")

# Submit Review API Models
class SubmitReviewRequest(BaseModel):
    """Request model for submitting RFI/RFP for review."""
    responseId: str = Field(..., description="Unique response ID")
    status: str = Field(..., description="Status (should be 'submitReview')")
    user: str = Field(..., description="User submitting for review")

class SubmitReviewResponse(BaseModel):
    """Response model for submit review endpoint."""
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Success status")

# Audit Trail API Models
class AuditTrailItem(BaseModel):
    """Model for individual audit trail entry."""
    id: str = Field(..., description="Audit trail entry ID")
    timestamp: str = Field(..., description="Timestamp of the action")
    actor: str = Field(..., description="User or system that performed the action")
    action: str = Field(..., description="Description of the action performed")
    question: str = Field(..., description="Question text related to the action")
    type: str = Field(..., description="Type of action (AI, EDIT, COMPLETE, etc.)")

# Audit Trail Response - Changed to return array directly as per spec
AuditTrailResponse = List[AuditTrailItem]

# Draft Generation API Models
class DraftRequest(BaseModel):
    """Request model for generating draft answers."""
    responseId: str = Field(..., description="RFI response ID")
    questionId: Union[int, str] = Field(..., description="Question ID (can be int or string)")
    question: str = Field(..., description="Question text")
    response: str = Field(..., description="User's draft response")
    status: str = Field(..., description="Status of the question")
    user: str = Field(..., description="User identifier")

class DraftResponse(BaseModel):
    """Response model for draft generation endpoint."""
    success: bool = Field(..., description="Success status")
    data: dict = Field(..., description="Generated draft data")

class ExportResponse(BaseModel):
    """Response model for export endpoint."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    filename: str = Field(..., description="Generated filename")
    file_path: str = Field(..., description="Path to the generated file")