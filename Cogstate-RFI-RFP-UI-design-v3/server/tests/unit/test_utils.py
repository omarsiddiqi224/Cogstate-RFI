"""
Unit tests for utility functions.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from rfiprocessor.utils.wlak_dir import list_all_file_paths
from rfiprocessor.utils.data_access import DataAccessUtils
from rfiprocessor.utils.error_handler import APIErrorHandler
from rfiprocessor.utils.logger import get_logger


class TestWlakDir:
    """Test cases for wlak_dir utility functions."""

    @patch('os.walk')
    def test_list_all_file_paths_success(self, mock_walk):
        """Test listing all file paths successfully."""
        # Mock os.walk to return test directory structure
        mock_walk.return_value = [
            ('/test/dir', ['subdir'], ['file1.txt', 'file2.pdf']),
            ('/test/dir/subdir', [], ['file3.docx'])
        ]
        
        result = list_all_file_paths('/test/dir')
        
        expected_paths = [
            '/test/dir/file1.txt',
            '/test/dir/file2.pdf',
            '/test/dir/subdir/file3.docx'
        ]
        assert result == expected_paths

    @patch('os.walk')
    def test_list_all_file_paths_empty_directory(self, mock_walk):
        """Test listing file paths from empty directory."""
        mock_walk.return_value = [('/test/dir', [], [])]
        
        result = list_all_file_paths('/test/dir')
        
        assert result == []

    @patch('os.walk')
    def test_list_all_file_paths_file_not_found(self, mock_walk):
        """Test listing file paths when directory doesn't exist."""
        mock_walk.side_effect = FileNotFoundError("Directory not found")
        
        result = list_all_file_paths('/nonexistent/dir')
        
        assert result == []

    @patch('os.walk')
    def test_list_all_file_paths_permission_error(self, mock_walk):
        """Test listing file paths with permission error."""
        mock_walk.side_effect = PermissionError("Permission denied")
        
        result = list_all_file_paths('/restricted/dir')
        
        assert result == []

    @patch('os.walk')
    def test_list_all_file_paths_general_error(self, mock_walk):
        """Test listing file paths with general error."""
        mock_walk.side_effect = Exception("Unexpected error")
        
        result = list_all_file_paths('/test/dir')
        
        assert result == []


class TestDataAccessUtils:
    """Test cases for data access utility functions."""

    def test_get_safe_payload_with_payload(self):
        """Test getting safe payload with existing payload."""
        payload = {"key": "value", "nested": {"data": "test"}}
        result = DataAccessUtils.get_safe_payload(payload)
        assert result == payload

    def test_get_safe_payload_with_none(self):
        """Test getting safe payload with None."""
        result = DataAccessUtils.get_safe_payload(None)
        assert result == {}

    def test_get_safe_payload_with_empty_dict(self):
        """Test getting safe payload with empty dict."""
        result = DataAccessUtils.get_safe_payload({})
        assert result == {}

    def test_get_safe_sections_with_sections(self):
        """Test getting safe sections with existing sections."""
        payload = {"saved_sections": [{"id": "1", "question": "test"}]}
        result = DataAccessUtils.get_safe_sections(payload)
        assert result == [{"id": "1", "question": "test"}]

    def test_get_safe_sections_without_sections(self):
        """Test getting safe sections without sections."""
        payload = {"other_key": "value"}
        result = DataAccessUtils.get_safe_sections(payload)
        assert result == []

    def test_get_safe_sections_with_none_payload(self):
        """Test getting safe sections with None payload."""
        result = DataAccessUtils.get_safe_sections(None)
        assert result == []

    def test_get_safe_qa_pairs_with_pairs(self):
        """Test getting safe QA pairs with existing pairs."""
        payload = {"qa_pairs": [{"question": "test?", "answer": "test"}]}
        result = DataAccessUtils.get_safe_qa_pairs(payload)
        assert result == [{"question": "test?", "answer": "test"}]

    def test_get_safe_qa_pairs_without_pairs(self):
        """Test getting safe QA pairs without pairs."""
        payload = {"other_key": "value"}
        result = DataAccessUtils.get_safe_qa_pairs(payload)
        assert result == []

    def test_get_safe_metadata_with_metadata(self):
        """Test getting safe metadata with existing metadata."""
        payload = {"meta_data": {"company": "test", "date": "2025-01-01"}}
        result = DataAccessUtils.get_safe_metadata(payload)
        assert result == {"company": "test", "date": "2025-01-01"}

    def test_get_safe_metadata_without_metadata(self):
        """Test getting safe metadata without metadata."""
        payload = {"other_key": "value"}
        result = DataAccessUtils.get_safe_metadata(payload)
        assert result == {}

    def test_calculate_progress_normal(self):
        """Test calculating progress with normal values."""
        result = DataAccessUtils.calculate_progress(5, 10)
        assert result == 50

    def test_calculate_progress_complete(self):
        """Test calculating progress when complete."""
        result = DataAccessUtils.calculate_progress(10, 10)
        assert result == 100

    def test_calculate_progress_zero_total(self):
        """Test calculating progress with zero total."""
        result = DataAccessUtils.calculate_progress(5, 0)
        assert result == 0

    def test_calculate_progress_zero_completed(self):
        """Test calculating progress with zero completed."""
        result = DataAccessUtils.calculate_progress(0, 10)
        assert result == 0

    def test_get_section_by_id_found(self):
        """Test finding section by ID when found."""
        sections = [
            {"id": "1", "question": "test1"},
            {"id": "2", "question": "test2"}
        ]
        result = DataAccessUtils.get_section_by_id(sections, "1")
        assert result == {"id": "1", "question": "test1"}

    def test_get_section_by_id_not_found(self):
        """Test finding section by ID when not found."""
        sections = [
            {"id": "1", "question": "test1"},
            {"id": "2", "question": "test2"}
        ]
        result = DataAccessUtils.get_section_by_id(sections, "3")
        assert result is None

    def test_get_question_by_id_found(self):
        """Test finding question by ID when found."""
        qa_pairs = [
            {"questionId": "1", "question": "test1?"},
            {"questionId": "2", "question": "test2?"}
        ]
        result = DataAccessUtils.get_question_by_id(qa_pairs, "1")
        assert result == {"questionId": "1", "question": "test1?"}

    def test_get_question_by_id_not_found(self):
        """Test finding question by ID when not found."""
        qa_pairs = [
            {"questionId": "1", "question": "test1?"},
            {"questionId": "2", "question": "test2?"}
        ]
        result = DataAccessUtils.get_question_by_id(qa_pairs, "3")
        assert result is None


class TestAPIErrorHandler:
    """Test cases for API error handler functions."""

    def test_not_found_error(self):
        """Test generating not found error."""
        error = APIErrorHandler.not_found("Document", "123")
        assert error.status_code == 404
        assert "Document with id '123' not found" in error.detail

    def test_not_found_error_custom_identifier(self):
        """Test generating not found error with custom identifier."""
        error = APIErrorHandler.not_found("User", "john_doe", "username")
        assert error.status_code == 404
        assert "User with username 'john_doe' not found" in error.detail

    def test_bad_request_error(self):
        """Test generating bad request error."""
        error = APIErrorHandler.bad_request("Invalid input data")
        assert error.status_code == 400
        assert error.detail == "Invalid input data"

    def test_internal_error(self):
        """Test generating internal error."""
        error = APIErrorHandler.internal_error()
        assert error.status_code == 500
        assert error.detail == "Internal server error"

    def test_validation_error(self):
        """Test generating validation error."""
        error = APIErrorHandler.validation_error("email", "Invalid email format")
        assert error.status_code == 422
        assert "Validation error for field 'email': Invalid email format" in error.detail

    def test_forbidden_error_default(self):
        """Test generating forbidden error with default message."""
        error = APIErrorHandler.forbidden()
        assert error.status_code == 403
        assert error.detail == "Access denied"

    def test_forbidden_error_custom(self):
        """Test generating forbidden error with custom message."""
        error = APIErrorHandler.forbidden("Insufficient permissions")
        assert error.status_code == 403
        assert error.detail == "Insufficient permissions"

    def test_conflict_error(self):
        """Test generating conflict error."""
        error = APIErrorHandler.conflict("Resource already exists")
        assert error.status_code == 409
        assert error.detail == "Resource already exists"


class TestLogger:
    """Test cases for logger utility functions."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')

    def test_get_logger_same_name_returns_same_logger(self):
        """Test that get_logger returns the same logger for the same name."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2

    def test_get_logger_different_names_returns_different_loggers(self):
        """Test that get_logger returns different loggers for different names."""
        logger1 = get_logger("test_module_1")
        logger2 = get_logger("test_module_2")
        assert logger1 is not logger2

    def test_get_logger_with_custom_log_file(self):
        """Test get_logger with custom log file."""
        logger = get_logger("test_module", "custom.log")
        assert logger is not None 