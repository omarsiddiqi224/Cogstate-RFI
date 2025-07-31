"""
Unit tests for database handler functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import Document, Chunk, IngestionStatus


class TestDatabaseHandler:
    """Test cases for database handler functions."""

    def test_init(self, mock_db_session):
        """Test database handler initialization."""
        handler = DatabaseHandler(mock_db_session)
        assert handler.db == mock_db_session

    def test_add_or_get_document_new(self, mock_db_session):
        """Test adding a new document."""
        # Mock no existing document found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock document creation
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_doc.source_filename = "test.pdf"
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.add_or_get_document("/path/to/test.pdf")
        
        # Verify document was added
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result is not None

    def test_add_or_get_document_existing(self, mock_db_session):
        """Test getting existing document."""
        # Mock existing document found
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_doc.source_filename = "test.pdf"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.add_or_get_document("/path/to/test.pdf")
        
        # Verify no new document was added
        mock_db_session.add.assert_not_called()
        mock_db_session.commit.assert_not_called()
        assert result == mock_doc

    def test_get_documents_by_status(self, mock_db_session):
        """Test getting documents by status."""
        # Mock documents
        mock_docs = [
            Mock(spec=Document, id=1, source_filename="doc1.pdf"),
            Mock(spec=Document, id=2, source_filename="doc2.pdf")
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_docs
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.get_documents_by_status(IngestionStatus.PENDING)
        
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_update_document_success(self, mock_db_session):
        """Test updating document successfully."""
        # Mock existing document
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_doc.source_filename = "test.pdf"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        handler = DatabaseHandler(mock_db_session)
        updates = {"source_filename": "updated.pdf", "ingestion_status": IngestionStatus.COMPLETED}
        result = handler.update_document(1, updates)
        
        # Verify document was updated
        assert mock_doc.source_filename == "updated.pdf"
        assert mock_doc.ingestion_status == IngestionStatus.COMPLETED
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result == mock_doc

    def test_update_document_not_found(self, mock_db_session):
        """Test updating non-existent document."""
        # Mock no document found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.update_document(999, {"source_filename": "updated.pdf"})
        
        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_update_document_invalid_attribute(self, mock_db_session):
        """Test updating document with invalid attribute."""
        # Mock existing document
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        handler = DatabaseHandler(mock_db_session)
        updates = {"invalid_attribute": "value"}
        result = handler.update_document(1, updates)
        
        # Should still succeed but log warning
        mock_db_session.commit.assert_called_once()
        assert result == mock_doc

    def test_get_document_by_id_success(self, mock_db_session):
        """Test getting document by ID successfully."""
        # Mock document
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.get_document_by_id(1)
        
        assert result == mock_doc

    def test_get_document_by_id_not_found(self, mock_db_session):
        """Test getting document by ID when not found."""
        # Mock no document found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.get_document_by_id(999)
        
        assert result is None

    def test_update_record_success(self, mock_db_session):
        """Test updating record successfully."""
        # Mock existing record
        mock_record = Mock(spec=Document)
        mock_record.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_record
        
        handler = DatabaseHandler(mock_db_session)
        updates = {"source_filename": "updated.pdf"}
        result = handler.update_record(1, updates, Document)
        
        # Verify record was updated
        assert mock_record.source_filename == "updated.pdf"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        assert result == mock_record

    def test_update_record_not_found(self, mock_db_session):
        """Test updating non-existent record."""
        # Mock no record found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        result = handler.update_record(999, {"source_filename": "updated.pdf"}, Document)
        
        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_add_chunks_to_document_success(self, mock_db_session):
        """Test adding chunks to document successfully."""
        # Mock existing document
        mock_doc = Mock(spec=Document)
        mock_doc.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_doc
        
        # Mock chunks
        mock_chunks = [
            Mock(spec=Chunk, id=1, document_id=1),
            Mock(spec=Chunk, id=2, document_id=1)
        ]
        
        handler = DatabaseHandler(mock_db_session)
        chunks_data = [
            {"chunk_text": "Chunk 1", "chunk_metadata": {"key": "value1"}},
            {"chunk_text": "Chunk 2", "chunk_metadata": {"key": "value2"}}
        ]
        
        with patch('rfiprocessor.services.db_handler.Chunk') as mock_chunk_class:
            mock_chunk_class.side_effect = mock_chunks
            result = handler.add_chunks_to_document(1, chunks_data)
        
        # Verify chunks were added
        mock_db_session.add_all.assert_called_once()
        mock_db_session.commit.assert_called_once()
        assert len(result) == 2

    def test_add_chunks_to_document_not_found(self, mock_db_session):
        """Test adding chunks to non-existent document."""
        # Mock no document found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        chunks_data = [{"chunk_text": "Chunk 1", "chunk_metadata": {}}]
        
        with pytest.raises(ValueError) as exc_info:
            handler.add_chunks_to_document(999, chunks_data)
        
        assert "Document with ID 999 not found" in str(exc_info.value)

    def test_update_chunk_success(self, mock_db_session):
        """Test updating chunk successfully."""
        # Mock existing chunk
        mock_chunk = Mock(spec=Chunk)
        mock_chunk.id = 1
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_chunk
        
        handler = DatabaseHandler(mock_db_session)
        updates = {"chunk_text": "Updated chunk text"}
        handler.update_chunk(1, updates)
        
        # Verify chunk was updated
        assert mock_chunk.chunk_text == "Updated chunk text"
        mock_db_session.commit.assert_called_once()

    def test_update_chunk_not_found(self, mock_db_session):
        """Test updating non-existent chunk."""
        # Mock no chunk found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        handler = DatabaseHandler(mock_db_session)
        
        with pytest.raises(ValueError) as exc_info:
            handler.update_chunk(999, {"chunk_text": "Updated"})
        
        assert "Chunk with ID 999 not found" in str(exc_info.value)

    def test_update_chunk_vector_ids(self, mock_db_session):
        """Test updating chunk vector IDs."""
        # Mock chunks
        mock_chunks = [
            Mock(spec=Chunk, id=1, vector_id=None),
            Mock(spec=Chunk, id=2, vector_id=None)
        ]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_chunks
        
        handler = DatabaseHandler(mock_db_session)
        chunk_vector_map = {1: "vec_1", 2: "vec_2"}
        handler.update_chunk_vector_ids(chunk_vector_map)
        
        # Verify vector IDs were updated
        assert mock_chunks[0].vector_id == "vec_1"
        assert mock_chunks[1].vector_id == "vec_2"
        mock_db_session.commit.assert_called_once() 