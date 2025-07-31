"""
Unit tests for section management functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from datetime import datetime

from rfiprocessor.api.section_management import (
    find_existing_section,
    update_section_in_document,
    calculate_and_update_progress,
    save_section,
    mark_complete
)
from rfiprocessor.models.data_models import SaveSectionRequest, MarkCompleteRequest
from rfiprocessor.db.db_models import RfiDocument, RfiStatus, QUESTION_STATUS_COMPLETED


class TestSectionManagement:
    """Test cases for section management functions."""

    def test_find_existing_section_in_saved_sections(self, mock_db_session, mock_rfi_document):
        """Test finding section in saved_sections array."""
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        
        doc, section = find_existing_section(mock_db_session, "section-1", "1")
        
        assert doc == mock_rfi_document
        assert section is not None
        assert section["id"] == "section-1"
        assert section["questionId"] == "1"

    def test_find_existing_section_in_questions(self, mock_db_session, mock_rfi_document):
        """Test finding section in questions array."""
        # Remove saved_sections to force questions search
        mock_rfi_document.payload.pop("saved_sections", None)
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        
        doc, section = find_existing_section(mock_db_session, "section-1", "1")
        
        assert doc == mock_rfi_document
        assert section is not None
        assert section["id"] == "1"
        assert section["question"] == "What is your company's experience?"

    def test_find_existing_section_not_found(self, mock_db_session):
        """Test finding section when not found."""
        mock_db_session.query.return_value.all.return_value = []
        
        doc, section = find_existing_section(mock_db_session, "nonexistent", "999")
        
        assert doc is None
        assert section is None

    def test_update_section_in_document(self, mock_rfi_document):
        """Test updating section in document."""
        updated_data = {
            "questionId": "1",
            "question": "Updated question?",
            "response": "Updated response",
            "status": "completed",
            "user": "test_user",
            "saved_at": "2025-01-01T10:00:00Z"
        }
        
        update_section_in_document(mock_rfi_document, "1", updated_data)
        
        # Verify the section was updated
        questions = mock_rfi_document.payload["questions"]
        updated_question = next(q for q in questions if q["id"] == "1")
        assert updated_question["question"] == "Updated question?"
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

    def test_calculate_and_update_progress_zero_progress(self, mock_rfi_document):
        """Test calculating progress when no questions are completed."""
        # Set all questions to pending
        for question in mock_rfi_document.payload["questions"]:
            question["status"] = "pending"
        
        calculate_and_update_progress(mock_rfi_document)
        
        assert mock_rfi_document.progress == 0
        assert mock_rfi_document.status == RfiStatus.IN_PROGRESS

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_save_section_success(self, mock_get_db, mock_db_session, mock_rfi_document):
        """Test saving section successfully."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        
        request = SaveSectionRequest(
            responseId="section-1",
            questionId="1",
            question="What is your company's experience?",
            response="Updated response",
            status="completed",
            user="test_user"
        )
        
        result = save_section(request)
        
        assert result.success is True
        assert "Section saved successfully" in result.message
        assert result.data["response"] == "Updated response"
        assert result.data["status"] == "completed"

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_save_section_not_found(self, mock_get_db, mock_db_session):
        """Test saving section when not found."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = []
        
        request = SaveSectionRequest(
            responseId="nonexistent",
            questionId="999",
            question="Test question?",
            response="Test response",
            status="pending",
            user="test_user"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            save_section(request)
        
        assert exc_info.value.status_code == 404
        assert "Section not found" in exc_info.value.detail

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_mark_complete_success(self, mock_get_db, mock_db_session, mock_rfi_document):
        """Test marking section as complete successfully."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        
        request = MarkCompleteRequest(
            responseId="section-1",
            questionId="1",
            question="What is your company's experience?",
            response="Final response",
            status="completed",
            user="test_user"
        )
        
        result = mark_complete(request)
        
        assert result.success is True
        assert "Section marked as complete successfully" in result.message
        assert result.data["status"] == QUESTION_STATUS_COMPLETED
        assert result.data["user"] == "test_user"

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_mark_complete_not_found(self, mock_get_db, mock_db_session):
        """Test marking section as complete when not found."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = []
        
        request = MarkCompleteRequest(
            responseId="nonexistent",
            questionId="999",
            question="Test question?",
            response="Test response",
            status="completed",
            user="test_user"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            mark_complete(request)
        
        assert exc_info.value.status_code == 404
        assert "Section not found" in exc_info.value.detail

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_save_section_database_error(self, mock_get_db, mock_db_session, mock_rfi_document):
        """Test saving section with database error."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        mock_db_session.commit.side_effect = Exception("Database error")
        
        request = SaveSectionRequest(
            responseId="section-1",
            questionId="1",
            question="Test question?",
            response="Test response",
            status="pending",
            user="test_user"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            save_section(request)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail

    @patch('rfiprocessor.api.section_management.get_db_session')
    def test_mark_complete_database_error(self, mock_get_db, mock_db_session, mock_rfi_document):
        """Test marking section as complete with database error."""
        mock_get_db.return_value = iter([mock_db_session])
        mock_db_session.query.return_value.all.return_value = [mock_rfi_document]
        mock_db_session.commit.side_effect = Exception("Database error")
        
        request = MarkCompleteRequest(
            responseId="section-1",
            questionId="1",
            question="Test question?",
            response="Test response",
            status="completed",
            user="test_user"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            mark_complete(request)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in exc_info.value.detail 