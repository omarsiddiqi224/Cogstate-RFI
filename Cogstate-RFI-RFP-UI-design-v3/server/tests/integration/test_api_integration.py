"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from rfiprocessor.api.controller import app


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response."""
        response = client.get("/")
        assert response.status_code == 200
        assert "RFI Processor API" in response.json()["message"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @patch('rfiprocessor.api.audit_trail_management.get_audit_trail')
    def test_audit_trail_endpoint_success(self, mock_get_audit_trail, client):
        """Test audit trail endpoint with successful response."""
        # Mock audit trail data
        mock_audit_data = [
            {
                "id": "at1",
                "timestamp": "2025-01-01T10:00:00Z",
                "actor": "test_user",
                "action": "Created response",
                "question": "Test question?",
                "type": "CREATE"
            }
        ]
        mock_get_audit_trail.return_value = mock_audit_data
        
        response = client.get("/auditTrail?id=12345678-1234-1234-1234-123456789012")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["actor"] == "test_user"

    def test_audit_trail_endpoint_invalid_id(self, client):
        """Test audit trail endpoint with invalid ID."""
        response = client.get("/auditTrail?id=invalid-id")
        assert response.status_code == 400

    @patch('rfiprocessor.api.section_management.save_section')
    def test_save_section_endpoint_success(self, mock_save_section, client):
        """Test save section endpoint with successful response."""
        # Mock save section response
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Section saved successfully"
        mock_response.data = {"responseId": "resp_1", "status": "completed"}
        mock_save_section.return_value = mock_response
        
        request_data = {
            "responseId": "resp_1",
            "questionId": "q_1",
            "question": "Test question?",
            "response": "Test response",
            "status": "completed",
            "user": "test_user"
        }
        
        response = client.post("/saveSection", json=request_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_save_section_endpoint_invalid_data(self, client):
        """Test save section endpoint with invalid data."""
        request_data = {
            "responseId": "resp_1",
            # Missing required fields
        }
        
        response = client.post("/saveSection", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch('rfiprocessor.api.section_management.mark_complete')
    def test_mark_complete_endpoint_success(self, mock_mark_complete, client):
        """Test mark complete endpoint with successful response."""
        # Mock mark complete response
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Section marked as complete successfully"
        mock_response.data = {"responseId": "resp_1", "status": "completed"}
        mock_mark_complete.return_value = mock_response
        
        request_data = {
            "responseId": "resp_1",
            "questionId": "q_1",
            "question": "Test question?",
            "response": "Final response",
            "status": "completed",
            "user": "test_user"
        }
        
        response = client.post("/markComplete", json=request_data)
        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch('rfiprocessor.api.export_markdown.export_rfi_to_markdown')
    def test_export_rfi_endpoint_success(self, mock_export, client):
        """Test export RFI endpoint with successful response."""
        # Mock export response
        mock_response = Mock()
        mock_response.success = True
        mock_response.message = "Export successful"
        mock_response.filename = "export.md"
        mock_response.file_path = "/path/to/export.md"
        mock_export.return_value = mock_response
        
        response = client.get("/exportRFI/12345678-1234-1234-1234-123456789012")
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["filename"] == "export.md"

    def test_export_rfi_endpoint_invalid_id(self, client):
        """Test export RFI endpoint with invalid ID."""
        response = client.get("/exportRFI/invalid-id")
        assert response.status_code == 400

    @patch('rfiprocessor.api.rfi_management.get_active_rfi_list')
    def test_get_active_rfi_list_endpoint(self, mock_get_list, client):
        """Test get active RFI list endpoint."""
        # Mock RFI list response
        mock_rfi_list = [
            {
                "id": "rfi_1",
                "title": "Test RFI 1",
                "status": "IN_PROGRESS",
                "progress": 50,
                "lastUpdated": "2025-01-01T10:00:00Z"
            }
        ]
        mock_get_list.return_value = mock_rfi_list
        
        response = client.get("/getActiveRFIList")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test RFI 1"

    @patch('rfiprocessor.api.rfi_management.get_specific_rfi')
    def test_get_specific_rfi_endpoint(self, mock_get_rfi, client):
        """Test get specific RFI endpoint."""
        # Mock RFI response
        mock_rfi = {
            "id": "rfi_1",
            "title": "Test RFI",
            "status": "IN_PROGRESS",
            "progress": 50,
            "payload": {
                "questions": [
                    {
                        "id": "1",
                        "question": "Test question?",
                        "response": "Test response",
                        "status": "completed"
                    }
                ]
            }
        }
        mock_get_rfi.return_value = mock_rfi
        
        response = client.get("/response?id=12345678-1234-1234-1234-123456789012")
        assert response.status_code == 200
        assert response.json()["title"] == "Test RFI"
        assert len(response.json()["payload"]["questions"]) == 1

    def test_get_specific_rfi_endpoint_invalid_id(self, client):
        """Test get specific RFI endpoint with invalid ID."""
        response = client.get("/response?id=invalid-id")
        assert response.status_code == 400

    @patch('rfiprocessor.api.knowledge_base_management.get_knowledge_base_list')
    def test_knowledge_base_list_endpoint(self, mock_get_kb, client):
        """Test knowledge base list endpoint."""
        # Mock knowledge base response
        mock_kb_list = [
            {
                "id": "kb_1",
                "title": "Test KB Item",
                "category": "General",
                "snippet": "Test snippet...",
                "fullText": "Full text content"
            }
        ]
        mock_get_kb.return_value = mock_kb_list
        
        response = client.get("/getKnowledgeBaseList")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test KB Item"

    @patch('rfiprocessor.api.knowledge_base_search.search_knowledge_base')
    def test_search_knowledge_base_endpoint(self, mock_search, client):
        """Test search knowledge base endpoint."""
        # Mock search response
        mock_search_results = [
            {
                "id": "kb_1",
                "title": "Test KB Item",
                "category": "General",
                "snippet": "Test snippet...",
                "fullText": "Full text content",
                "score": 0.95
            }
        ]
        mock_search.return_value = mock_search_results
        
        request_data = {
            "query": "test query",
            "top_k": 5
        }
        
        response = client.post("/searchKnowledgeBase", json=request_data)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test KB Item"
        assert response.json()[0]["score"] == 0.95

    def test_search_knowledge_base_endpoint_invalid_data(self, client):
        """Test search knowledge base endpoint with invalid data."""
        request_data = {
            "query": "",  # Empty query
            "top_k": 5
        }
        
        response = client.post("/searchKnowledgeBase", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_404_endpoint(self, client):
        """Test 404 response for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404 