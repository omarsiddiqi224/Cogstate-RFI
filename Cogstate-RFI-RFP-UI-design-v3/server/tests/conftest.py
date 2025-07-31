"""
Pytest configuration and fixtures for RFI Processor tests.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Mock FastAPI dependencies
@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = Mock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.add.return_value = None
    session.commit.return_value = None
    session.close.return_value = None
    session.refresh.return_value = None
    return session

@pytest.fixture
def mock_rfi_document():
    """Mock RFI document for testing."""
    from rfiprocessor.db.db_models import RfiDocument, RfiStatus
    from datetime import datetime
    
    doc = Mock(spec=RfiDocument)
    doc.id = "test-rfi-id-123"
    doc.title = "Test RFI Document"
    doc.status = RfiStatus.IN_PROGRESS
    doc.progress = 50
    doc.payload = {
        "questions": [
            {
                "id": "1",
                "question": "What is your company's experience?",
                "response": "We have 10+ years of experience.",
                "status": "completed",
                "user": "test_user",
                "saved_at": "2025-01-01T10:00:00Z"
            },
            {
                "id": "2", 
                "question": "What are your capabilities?",
                "response": "",
                "status": "pending",
                "user": "test_user"
            }
        ],
        "saved_sections": [
            {
                "id": "section-1",
                "questionId": "1",
                "question": "What is your company's experience?",
                "response": "We have 10+ years of experience.",
                "status": "completed",
                "user": "test_user",
                "saved_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
    doc.created_at = datetime(2025, 1, 1, 10, 0, 0)
    doc.updated_at = datetime(2025, 1, 1, 10, 0, 0)
    return doc

@pytest.fixture
def mock_upload_file():
    """Mock uploaded file for testing."""
    file = Mock()
    file.filename = "test_document.pdf"
    file.content_type = "application/pdf"
    file.size = 1024 * 1024  # 1MB
    file.read.return_value = b"test file content"
    return file

@pytest.fixture
def sample_audit_trail_data():
    """Sample audit trail data for testing."""
    return [
        {
            "id": "at1",
            "timestamp": "2025-01-01T10:00:00Z",
            "actor": "AI (Gemini)",
            "action": "Generated initial draft for question 1.",
            "question": "What is your company's experience?",
            "type": "AI"
        },
        {
            "id": "at2", 
            "timestamp": "2025-01-01T10:05:00Z",
            "actor": "test_user",
            "action": "Created initial response for question 1.",
            "question": "What is your company's experience?",
            "type": "CREATE"
        },
        {
            "id": "at3",
            "timestamp": "2025-01-01T10:10:00Z", 
            "actor": "test_user",
            "action": "Edited response for question 1.",
            "question": "What is your company's experience?",
            "type": "EDIT"
        }
    ]

@pytest.fixture
def sample_knowledge_base_data():
    """Sample knowledge base data for testing."""
    return [
        {
            "id": "kb_1",
            "title": "Company Overview",
            "category": "General",
            "snippet": "Our company has been in business for over 10 years...",
            "fullText": "Our company has been in business for over 10 years providing excellent services to clients worldwide."
        },
        {
            "id": "kb_2",
            "title": "Technical Capabilities", 
            "category": "Technical",
            "snippet": "We offer a wide range of technical services...",
            "fullText": "We offer a wide range of technical services including cloud computing, AI, and data analytics."
        }
    ]

@pytest.fixture
def temp_file_path():
    """Create a temporary file path for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b"Test document content for unit testing")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "questions": [
            {
                "question": "What is your company's experience?",
                "domain": "General",
                "type": "open-ended"
            },
            {
                "question": "What are your technical capabilities?",
                "domain": "Technical", 
                "type": "open-ended"
            }
        ],
        "meta_data": {
            "company_name": "Test Company",
            "category": "RFI",
            "type": "PastResponse"
        }
    }

@pytest.fixture
def mock_vector_store_results():
    """Mock vector store search results."""
    return [
        {
            "content": "Our company has extensive experience in the healthcare industry.",
            "metadata": {
                "source_document_id": "doc1",
                "source_filename": "company_overview.pdf",
                "document_type": "Supporting Document",
                "document_grade": "Standard"
            }
        },
        {
            "content": "We provide comprehensive technical solutions including AI and machine learning.",
            "metadata": {
                "source_document_id": "doc2", 
                "source_filename": "technical_capabilities.pdf",
                "document_type": "Supporting Document",
                "document_grade": "Standard"
            }
        }
    ] 