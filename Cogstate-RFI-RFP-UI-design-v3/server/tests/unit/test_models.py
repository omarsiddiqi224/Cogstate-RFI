"""
Unit tests for data models.
"""
import pytest
from datetime import datetime, date
from pydantic import ValidationError

from rfiprocessor.models.data_models import (
    QAPair,
    RfiMetadata,
    RFIJson,
    FileUploadRequest,
    KnowledgeBaseItem,
    QuestionResponse,
    MetaData,
    FileUploadResponse,
    KnowledgeBaseEntryRequest,
    KnowledgeBaseEntryResponse,
    SearchKnowledgeBaseRequest,
    SearchKnowledgeBaseResponse,
    SaveSectionRequest,
    SaveSectionResponse,
    MarkCompleteRequest,
    MarkCompleteResponse,
    ActiveRFIUser,
    ActiveRFIItem,
    ActiveRFIListResponse,
    SpecificRFIRequest,
    SpecificRFIResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    AuditTrailItem,
    DraftRequest,
    DraftResponse,
    ExportResponse
)


class TestQAPair:
    """Test cases for QAPair model."""

    def test_valid_qa_pair(self):
        """Test creating a valid QA pair."""
        qa_pair = QAPair(
            question="What is your experience?",
            answer="We have 10+ years of experience."
        )
        assert qa_pair.question == "What is your experience?"
        assert qa_pair.answer == "We have 10+ years of experience."
        assert qa_pair.domain is None
        assert qa_pair.type is None

    def test_qa_pair_with_optional_fields(self):
        """Test creating QA pair with optional fields."""
        qa_pair = QAPair(
            question="What is your experience?",
            answer="We have 10+ years of experience.",
            domain="Technical",
            type="open-ended"
        )
        assert qa_pair.domain == "Technical"
        assert qa_pair.type == "open-ended"

    def test_qa_pair_missing_required_fields(self):
        """Test creating QA pair with missing required fields."""
        with pytest.raises(ValidationError):
            QAPair(question="What is your experience?")  # Missing answer

        with pytest.raises(ValidationError):
            QAPair(answer="We have experience.")  # Missing question


class TestRfiMetadata:
    """Test cases for RfiMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = RfiMetadata(
            company_name="Test Company",
            category="RFI",
            type="PastResponse"
        )
        assert metadata.company_name == "Test Company"
        assert metadata.category == "RFI"
        assert metadata.type == "PastResponse"
        assert metadata.doc_date is None

    def test_metadata_with_date(self):
        """Test creating metadata with date."""
        test_date = date(2025, 1, 1)
        metadata = RfiMetadata(
            company_name="Test Company",
            category="RFP",
            type="PastResponse",
            doc_date=test_date
        )
        assert metadata.doc_date == test_date

    def test_metadata_invalid_category(self):
        """Test creating metadata with invalid category."""
        with pytest.raises(ValidationError):
            RfiMetadata(
                company_name="Test Company",
                category="INVALID",
                type="PastResponse"
            )

    def test_metadata_invalid_type(self):
        """Test creating metadata with invalid type."""
        with pytest.raises(ValidationError):
            RfiMetadata(
                company_name="Test Company",
                category="RFI",
                type="INVALID"
            )


class TestRFIJson:
    """Test cases for RFIJson model."""

    def test_valid_rfi_json(self):
        """Test creating valid RFI JSON."""
        qa_pairs = [
            QAPair(question="Q1?", answer="A1"),
            QAPair(question="Q2?", answer="A2")
        ]
        metadata = RfiMetadata(
            company_name="Test Company",
            category="RFI",
            type="PastResponse"
        )
        
        rfi_json = RFIJson(
            qa_pairs=qa_pairs,
            meta_data=metadata
        )
        
        assert len(rfi_json.qa_pairs) == 2
        assert rfi_json.meta_data.company_name == "Test Company"
        assert rfi_json.summary is None
        assert rfi_json.description is None

    def test_rfi_json_with_summary_and_description(self):
        """Test creating RFI JSON with summary and description."""
        qa_pairs = [QAPair(question="Q1?", answer="A1")]
        metadata = RfiMetadata(
            company_name="Test Company",
            category="RFI",
            type="PastResponse"
        )
        
        rfi_json = RFIJson(
            qa_pairs=qa_pairs,
            meta_data=metadata,
            summary="Test summary",
            description="Test description"
        )
        
        assert rfi_json.summary == "Test summary"
        assert rfi_json.description == "Test description"

    def test_rfi_json_empty_qa_pairs(self):
        """Test creating RFI JSON with empty QA pairs."""
        metadata = RfiMetadata(
            company_name="Test Company",
            category="RFI",
            type="PastResponse"
        )
        
        with pytest.raises(ValidationError):
            RFIJson(qa_pairs=[], meta_data=metadata)


class TestFileUploadRequest:
    """Test cases for FileUploadRequest model."""

    def test_valid_file_upload_request(self):
        """Test creating valid file upload request."""
        request = FileUploadRequest(
            fileName="test.pdf",
            fileType=".pdf",
            size=1024,
            user="test_user"
        )
        assert request.fileName == "test.pdf"
        assert request.fileType == ".pdf"
        assert request.size == 1024
        assert request.user == "test_user"

    def test_file_upload_request_default_user(self):
        """Test creating file upload request with default user."""
        request = FileUploadRequest(
            fileName="test.pdf",
            fileType=".pdf",
            size=1024
        )
        assert request.user == "test"


class TestKnowledgeBaseItem:
    """Test cases for KnowledgeBaseItem model."""

    def test_valid_knowledge_base_item(self):
        """Test creating valid knowledge base item."""
        item = KnowledgeBaseItem(
            id="kb_1",
            title="Test Item",
            category="General",
            snippet="Test snippet...",
            fullText="Full text content"
        )
        assert item.id == "kb_1"
        assert item.title == "Test Item"
        assert item.category == "General"
        assert item.snippet == "Test snippet..."
        assert item.fullText == "Full text content"

    def test_knowledge_base_item_default_full_text(self):
        """Test creating knowledge base item with default full text."""
        item = KnowledgeBaseItem(
            id="kb_1",
            title="Test Item",
            category="General",
            snippet="Test snippet..."
        )
        assert item.fullText == ""


class TestQuestionResponse:
    """Test cases for QuestionResponse model."""

    def test_valid_question_response(self):
        """Test creating valid question response."""
        kb_items = [
            KnowledgeBaseItem(
                id="kb_1",
                title="KB Item 1",
                category="General",
                snippet="Snippet 1"
            )
        ]
        
        response = QuestionResponse(
            id=1,
            question="Test question?",
            response="Test response",
            status="completed",
            assignedTo="test_user",
            knowledgeBase=kb_items
        )
        
        assert response.id == 1
        assert response.question == "Test question?"
        assert response.response == "Test response"
        assert response.status == "completed"
        assert response.assignedTo == "test_user"
        assert len(response.knowledgeBase) == 1

    def test_question_response_default_knowledge_base(self):
        """Test creating question response with default knowledge base."""
        response = QuestionResponse(
            id=1,
            question="Test question?",
            response="Test response",
            status="completed",
            assignedTo="test_user"
        )
        assert response.knowledgeBase == []


class TestMetaData:
    """Test cases for MetaData model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = MetaData(
            source_document_id="doc_1",
            source_filename="test.pdf",
            document_type="RFI/RFP",
            company_name="Test Company",
            domain="Technical",
            question_type="mixed",
            document_grade="Standard"
        )
        
        assert metadata.source_document_id == "doc_1"
        assert metadata.source_filename == "test.pdf"
        assert metadata.document_type == "RFI/RFP"
        assert metadata.company_name == "Test Company"
        assert metadata.domain == "Technical"
        assert metadata.question_type == "mixed"
        assert metadata.document_grade == "Standard"


class TestFileUploadResponse:
    """Test cases for FileUploadResponse model."""

    def test_valid_file_upload_response(self):
        """Test creating valid file upload response."""
        metadata = MetaData(
            source_document_id="doc_1",
            source_filename="test.pdf",
            document_type="RFI/RFP",
            company_name="Test Company",
            domain="Technical",
            question_type="mixed",
            document_grade="Standard"
        )
        
        questions = [
            QuestionResponse(
                id=1,
                question="Test question?",
                response="Test response",
                status="completed",
                assignedTo="test_user"
            )
        ]
        
        response = FileUploadResponse(
            id="doc_1",
            title="Test Document",
            success=True,
            fileName="test.pdf",
            status="IN_PROGRESS",
            lastUpdated=datetime.now(),
            section="Processing...",
            progress=50,
            questions=questions,
            metaData=metadata
        )
        
        assert response.id == "doc_1"
        assert response.title == "Test Document"
        assert response.success is True
        assert response.fileName == "test.pdf"
        assert response.status == "IN_PROGRESS"
        assert response.section == "Processing..."
        assert response.progress == 50
        assert len(response.questions) == 1
        assert response.metaData.company_name == "Test Company"


class TestSaveSectionRequest:
    """Test cases for SaveSectionRequest model."""

    def test_valid_save_section_request(self):
        """Test creating valid save section request."""
        request = SaveSectionRequest(
            responseId="resp_1",
            questionId="q_1",
            question="Test question?",
            response="Test response",
            status="completed",
            user="test_user"
        )
        
        assert request.responseId == "resp_1"
        assert request.questionId == "q_1"
        assert request.question == "Test question?"
        assert request.response == "Test response"
        assert request.status == "completed"
        assert request.user == "test_user"


class TestSaveSectionResponse:
    """Test cases for SaveSectionResponse model."""

    def test_valid_save_section_response(self):
        """Test creating valid save section response."""
        response = SaveSectionResponse(
            success=True,
            data={"responseId": "resp_1", "status": "completed"}
        )
        
        assert response.success is True
        assert response.data["responseId"] == "resp_1"
        assert response.data["status"] == "completed"


class TestMarkCompleteRequest:
    """Test cases for MarkCompleteRequest model."""

    def test_valid_mark_complete_request(self):
        """Test creating valid mark complete request."""
        request = MarkCompleteRequest(
            responseId="resp_1",
            questionId="q_1",
            question="Test question?",
            response="Final response",
            status="completed",
            user="test_user"
        )
        
        assert request.responseId == "resp_1"
        assert request.questionId == "q_1"
        assert request.question == "Test question?"
        assert request.response == "Final response"
        assert request.status == "completed"
        assert request.user == "test_user"


class TestMarkCompleteResponse:
    """Test cases for MarkCompleteResponse model."""

    def test_valid_mark_complete_response(self):
        """Test creating valid mark complete response."""
        response = MarkCompleteResponse(
            success=True,
            data={"responseId": "resp_1", "status": "completed"}
        )
        
        assert response.success is True
        assert response.data["responseId"] == "resp_1"
        assert response.data["status"] == "completed"


class TestAuditTrailItem:
    """Test cases for AuditTrailItem model."""

    def test_valid_audit_trail_item(self):
        """Test creating valid audit trail item."""
        item = AuditTrailItem(
            id="at_1",
            timestamp="2025-01-01T10:00:00Z",
            actor="test_user",
            action="Created response",
            question="Test question?",
            type="CREATE"
        )
        
        assert item.id == "at_1"
        assert item.timestamp == "2025-01-01T10:00:00Z"
        assert item.actor == "test_user"
        assert item.action == "Created response"
        assert item.question == "Test question?"
        assert item.type == "CREATE"


class TestExportResponse:
    """Test cases for ExportResponse model."""

    def test_valid_export_response(self):
        """Test creating valid export response."""
        response = ExportResponse(
            success=True,
            message="Export successful",
            filename="export.md",
            file_path="/path/to/export.md"
        )
        
        assert response.success is True
        assert response.message == "Export successful"
        assert response.filename == "export.md"
        assert response.file_path == "/path/to/export.md" 