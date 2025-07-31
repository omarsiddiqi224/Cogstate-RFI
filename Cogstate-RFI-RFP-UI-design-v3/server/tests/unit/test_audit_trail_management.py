"""
Unit tests for audit trail management functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from rfiprocessor.api.audit_trail_management import (
    sanitize_response_id,
    validate_response_id,
    format_timestamp,
    create_audit_entry,
    get_audit_trail
)
from rfiprocessor.api.section_management import (
    find_existing_section,
    update_section_in_document,
    calculate_and_update_progress
)
from rfiprocessor.models.data_models import AuditTrailItem
from rfiprocessor.db.db_models import RfiDocument, RfiStatus, QUESTION_STATUS_COMPLETED


class TestAuditTrailManagement:
    """Test cases for audit trail management functions."""

    def test_sanitize_response_id_valid(self):
        """Test sanitizing a valid response ID."""
        result = sanitize_response_id("test-123_abc")
        assert result == "test-123_abc"

    def test_sanitize_response_id_with_special_chars(self):
        """Test sanitizing response ID with special characters."""
        result = sanitize_response_id("test@#$%^&*()")
        assert result == "test"

    def test_sanitize_response_id_with_spaces(self):
        """Test sanitizing response ID with spaces."""
        result = sanitize_response_id("  test-id  ")
        assert result == "test-id"

    def test_validate_response_id_valid(self):
        """Test validating a valid response ID."""
        valid_id = "12345678-1234-1234-1234-123456789012"
        validate_response_id(valid_id)  # Should not raise exception

    def test_validate_response_id_empty(self):
        """Test validating empty response ID."""
        with pytest.raises(HTTPException) as exc_info:
            validate_response_id("")
        assert exc_info.value.status_code == 400
        assert "Response ID is required" in exc_info.value.detail

    def test_validate_response_id_not_string(self):
        """Test validating non-string response ID."""
        with pytest.raises(HTTPException) as exc_info:
            validate_response_id(123)
        assert exc_info.value.status_code == 400
        assert "Response ID must be a string" in exc_info.value.detail

    def test_validate_response_id_invalid_format(self):
        """Test validating response ID with invalid format."""
        with pytest.raises(HTTPException) as exc_info:
            validate_response_id("invalid-format")
        assert exc_info.value.status_code == 400
        assert "Invalid response ID format" in exc_info.value.detail

    def test_validate_response_id_dangerous_pattern(self):
        """Test validating response ID with dangerous patterns."""
        with pytest.raises(HTTPException) as exc_info:
            validate_response_id("12345678-1234-1234-1234-123456789012; DROP TABLE users;")
        assert exc_info.value.status_code == 400
        assert "Invalid response ID" in exc_info.value.detail

    def test_format_timestamp_string(self):
        """Test formatting timestamp string."""
        result = format_timestamp("2025-01-01T10:00:00")
        assert result == "2025-01-01T10:00:00Z"

    def test_format_timestamp_string_with_z(self):
        """Test formatting timestamp string that already has Z."""
        result = format_timestamp("2025-01-01T10:00:00Z")
        assert result == "2025-01-01T10:00:00Z"

    def test_format_timestamp_datetime(self):
        """Test formatting datetime object."""
        dt = datetime(2025, 1, 1, 10, 0, 0)
        result = format_timestamp(dt)
        assert result == "2025-01-01T10:00:00Z"

    def test_create_audit_entry(self):
        """Test creating an audit entry."""
        entry = create_audit_entry(
            entry_counter=1,
            timestamp="2025-01-01T10:00:00Z",
            actor="test_user",
            action="Test action",
            question="Test question?",
            entry_type="TEST"
        )
        
        assert isinstance(entry, AuditTrailItem)
        assert entry.id == "at1"
        assert entry.timestamp == "2025-01-01T10:00:00Z"
        assert entry.actor == "test_user"
        assert entry.action == "Test action"
        assert entry.question == "Test question?"
        assert entry.type == "TEST"

    def test_find_existing_section_found(self, mock_db_session, mock_rfi_document):
        """Test finding existing section successfully."""
        # Mock the database query
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        
        doc, section = find_existing_section(
            mock_db_session, 
            "section-1", 
            "1"
        )
        
        assert doc == mock_rfi_document
        assert section is not None
        assert section["id"] == "section-1"

    def test_find_existing_section_not_found(self, mock_db_session):
        """Test finding section when not found."""
        mock_db_session.query.return_value.all.return_value = []
        
        doc, section = find_existing_section(
            mock_db_session, 
            "nonexistent", 
            "999"
        )
        
        assert doc is None
        assert section is None

    def test_update_section_in_document(self, mock_rfi_document):
        """Test updating section in document."""
        updated_data = {
            "response": "Updated response",
            "status": "completed",
            "user": "test_user"
        }
        
        update_section_in_document(mock_rfi_document, "1", updated_data)
        
        # Verify the section was updated
        questions = mock_rfi_document.payload["questions"]
        updated_question = next(q for q in questions if q["id"] == "1")
        assert updated_question["response"] == "Updated response"
        assert updated_question["status"] == "completed"
        assert updated_question["user"] == "test_user"

    def test_calculate_and_update_progress_questions_workflow(self, mock_rfi_document):
        """Test calculating progress for questions workflow."""
        calculate_and_update_progress(mock_rfi_document)
        
        # Should be 50% (1 completed out of 2 questions)
        assert mock_rfi_document.progress == 50
        assert mock_rfi_document.status == RfiStatus.IN_REVIEW

    def test_calculate_and_update_progress_saved_sections_workflow(self, mock_rfi_document):
        """Test calculating progress for saved_sections workflow."""
        # Remove questions to force saved_sections workflow
        mock_rfi_document.payload.pop("questions", None)
        
        calculate_and_update_progress(mock_rfi_document)
        
        # Should be 100% (1 completed out of 1 section)
        assert mock_rfi_document.progress == 100
        assert mock_rfi_document.status == RfiStatus.COMPLETED

    @patch('rfiprocessor.api.audit_trail_management.get_db_session')
    @patch('rfiprocessor.api.audit_trail_management.find_rfi_document_by_id')
    @patch('rfiprocessor.api.audit_trail_management.find_rfi_document_by_section_id')
    def test_get_audit_trail_success(
        self, 
        mock_find_by_section, 
        mock_find_by_id, 
        mock_get_db, 
        mock_rfi_document,
        sample_audit_trail_data
    ):
        """Test getting audit trail successfully."""
        # Mock database session
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        mock_session.query.return_value.all.return_value = [mock_rfi_document]
        
        # Mock document finding
        mock_find_by_id.return_value = mock_rfi_document
        mock_find_by_section.return_value = (None, None)
        
        # Mock audit trail generation
        with patch('rfiprocessor.api.audit_trail_management.generate_audit_entries_for_section') as mock_generate:
            mock_generate.return_value = [(AuditTrailItem(**data), 2) for data in sample_audit_trail_data]
            
            result = get_audit_trail("test-rfi-id-123")
            
            assert len(result) == 3
            assert all(isinstance(item, AuditTrailItem) for item in result)
            assert result[0].actor == "AI (Gemini)"
            assert result[1].actor == "test_user"

    def test_get_audit_trail_invalid_id(self):
        """Test getting audit trail with invalid ID."""
        with pytest.raises(HTTPException) as exc_info:
            get_audit_trail("invalid-id")
        assert exc_info.value.status_code == 400

    @patch('rfiprocessor.api.audit_trail_management.get_db_session')
    def test_get_audit_trail_not_found(self, mock_get_db):
        """Test getting audit trail when document not found."""
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        mock_session.query.return_value.all.return_value = []
        
        with pytest.raises(HTTPException) as exc_info:
            get_audit_trail("12345678-1234-1234-1234-123456789012")
        assert exc_info.value.status_code == 404
        assert "Audit trail not found" in exc_info.value.detail 