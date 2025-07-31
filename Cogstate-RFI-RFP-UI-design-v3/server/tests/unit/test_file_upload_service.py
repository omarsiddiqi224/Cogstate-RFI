"""
Unit tests for file upload service functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException

from rfiprocessor.services.file_upload_service import FileUploadService


class TestFileUploadService:
    """Test cases for file upload service functions."""

    def test_init(self):
        """Test file upload service initialization."""
        service = FileUploadService()
        assert service.allowed_extensions == ['.pdf', '.docx', '.doc', '.xls', '.xlsx', '.md']
        assert service.max_file_size == 10 * 1024 * 1024  # 10MB

    def test_validate_file_size_valid(self):
        """Test validating valid file size."""
        service = FileUploadService()
        service.validate_file_size(1024 * 1024)  # 1MB - should not raise exception

    def test_validate_file_size_too_large(self):
        """Test validating file size that's too large."""
        service = FileUploadService()
        with pytest.raises(HTTPException) as exc_info:
            service.validate_file_size(20 * 1024 * 1024)  # 20MB
        assert exc_info.value.status_code == 400
        assert "File size exceeds 10MB limit" in exc_info.value.detail

    def test_validate_file_extension_valid_filename(self):
        """Test validating file with valid extension in filename."""
        service = FileUploadService()
        service.validate_file_extension("document.pdf")  # Should not raise exception

    def test_validate_file_extension_invalid_filename(self):
        """Test validating file with invalid extension in filename."""
        service = FileUploadService()
        with pytest.raises(HTTPException) as exc_info:
            service.validate_file_extension("document.exe")
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    def test_validate_file_extension_valid_file_type(self):
        """Test validating file with valid file_type parameter."""
        service = FileUploadService()
        service.validate_file_extension("document", file_type=".pdf")

    def test_validate_file_extension_valid_content_type(self):
        """Test validating file with valid content type."""
        service = FileUploadService()
        service.validate_file_extension("document", content_type="application/pdf")

    def test_validate_file_extension_all_valid(self):
        """Test validating file with all valid parameters."""
        service = FileUploadService()
        service.validate_file_extension(
            "document.pdf", 
            file_type=".pdf", 
            content_type="application/pdf"
        )

    def test_validate_file_extension_all_invalid(self):
        """Test validating file with all invalid parameters."""
        service = FileUploadService()
        with pytest.raises(HTTPException) as exc_info:
            service.validate_file_extension(
                "document.exe", 
                file_type=".exe", 
                content_type="application/exe"
            )
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    @patch('rfiprocessor.services.file_upload_service.config')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_save_file_with_filename(self, mock_open, mock_makedirs, mock_config):
        """Test saving file with provided filename."""
        # Mock config
        mock_config.INCOMING_DATA_PATH = "data/incoming"
        mock_config.DEFAULT_FILE_EXTENSION = ".txt"
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        service = FileUploadService()
        mock_upload_file = Mock()
        mock_upload_file.filename = "test.pdf"
        mock_upload_file.read.return_value = b"test content"
        
        result = service.save_file(mock_upload_file, "custom_name.pdf")
        
        assert result == "data/incoming/custom_name.pdf"
        mock_makedirs.assert_called_once_with("data/incoming", exist_ok=True)
        mock_file.write.assert_called_once_with(b"test content")

    @patch('rfiprocessor.services.file_upload_service.config')
    @patch('os.makedirs')
    @patch('builtins.open')
    @patch('uuid.uuid4')
    def test_save_file_without_filename(self, mock_uuid, mock_open, mock_makedirs, mock_config):
        """Test saving file without filename (generates UUID)."""
        # Mock config
        mock_config.INCOMING_DATA_PATH = "data/incoming"
        mock_config.DEFAULT_FILE_EXTENSION = ".txt"
        
        # Mock UUID
        mock_uuid.return_value = "test-uuid-123"
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        service = FileUploadService()
        mock_upload_file = Mock()
        mock_upload_file.filename = None
        mock_upload_file.read.return_value = b"test content"
        
        result = service.save_file(mock_upload_file)
        
        assert result == "data/incoming/test-uuid-123.txt"
        mock_makedirs.assert_called_once_with("data/incoming", exist_ok=True)
        mock_file.write.assert_called_once_with(b"test content")

    @patch('rfiprocessor.services.file_upload_service.config')
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_save_file_with_upload_file_filename(self, mock_open, mock_makedirs, mock_config):
        """Test saving file using upload file's filename."""
        # Mock config
        mock_config.INCOMING_DATA_PATH = "data/incoming"
        mock_config.DEFAULT_FILE_EXTENSION = ".txt"
        
        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        service = FileUploadService()
        mock_upload_file = Mock()
        mock_upload_file.filename = "original_name.docx"
        mock_upload_file.read.return_value = b"test content"
        
        result = service.save_file(mock_upload_file)
        
        assert result == "data/incoming/original_name.docx"
        mock_makedirs.assert_called_once_with("data/incoming", exist_ok=True)
        mock_file.write.assert_called_once_with(b"test content")

    def test_generate_document_id(self):
        """Test generating document ID."""
        service = FileUploadService()
        doc_id = service.generate_document_id()
        
        # Should be a string and not empty
        assert isinstance(doc_id, str)
        assert len(doc_id) > 0

    def test_generate_document_id_unique(self):
        """Test that generated document IDs are unique."""
        service = FileUploadService()
        doc_id1 = service.generate_document_id()
        doc_id2 = service.generate_document_id()
        
        assert doc_id1 != doc_id2

    @patch('rfiprocessor.services.file_upload_service.config')
    def test_validate_file_extension_case_insensitive(self, mock_config):
        """Test that file extension validation is case insensitive."""
        service = FileUploadService()
        
        # Test uppercase extensions
        service.validate_file_extension("document.PDF")
        service.validate_file_extension("document.DOCX")
        service.validate_file_extension("document.XLSX")

    @patch('rfiprocessor.services.file_upload_service.config')
    def test_validate_file_extension_mixed_case(self, mock_config):
        """Test file extension validation with mixed case."""
        service = FileUploadService()
        
        # Test mixed case extensions
        service.validate_file_extension("document.Pdf")
        service.validate_file_extension("document.Docx")
        service.validate_file_extension("document.Xlsx")

    def test_validate_file_size_zero(self):
        """Test validating zero file size."""
        service = FileUploadService()
        service.validate_file_size(0)  # Should not raise exception

    def test_validate_file_size_exact_limit(self):
        """Test validating file size at exact limit."""
        service = FileUploadService()
        service.validate_file_size(10 * 1024 * 1024)  # Exactly 10MB - should not raise exception 