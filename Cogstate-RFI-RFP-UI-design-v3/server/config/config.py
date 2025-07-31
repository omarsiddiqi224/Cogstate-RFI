# rfi_responder/config.py

import os
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    """
    Central configuration class for the RFI Responder application.
    It holds all settings as class attributes.
    """
    # --- Logger Configuration ---
    # This is the name of the top-level logger. All other loggers will be its children.
    APP_LOGGER_NAME = "rfi-processor"
    LOG_FORMAT = "%(asctime)s - %(name)-30s - %(levelname)-8s - [%(filename)s:%(lineno)d] - %(message)s"
    
    # Log levels
    CONSOLE_LOG_LEVEL = logging.DEBUG
    FILE_LOG_LEVEL = logging.DEBUG
    
    # File handler settings
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_FILE_PATH = f"logs/app_{timestamp}.log"
    MAX_LOG_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT = 5

    # --- Project Specific Configuration ---
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "db/chroma_db")

    INCOMING_DATA_PATH = "data/raw/incoming"
    PROCESSED_DATA_PATH = "data/raw/processed"
    PARSED_JSON_PATH = "data/json"
    INCOMING_MARKDOWN_PATH = "data/markdown/incoming"
    PROCESSED_MARKDOWN_PATH = "data/markdown/processed"

    CHROMA_PATH = "data/vector_store/chroma_db"
    COLLECTION_NAME = "chunks"

    VALID_FILE_EXTNS = ['.doc', '.docm', '.docx', '.pdf', '.pptx', '.txt', '.xls', '.xlsm', '.xlsx']

    MRKDN_FILE_EXTNS = ['.docx', '.pdf', '.pptx']
    UNSTRD_FILE_EXTNS = ['.doc', '.docm', '.txt', '.xls' , '.xlsx', 'xlsm']

    PROMPTS_DIR = "rfiprocessor/prompts"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY",  "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    EMBEDDING_MODEL = "text-embedding-3-large"
    LLM_MODEL_NAME = "gemini-2.5-pro"
    FAST_LLM_MODEL_NAME = "gpt-4-turbo"
    REASONING_LLM_MODEL_NAME = "o3"
    ADVANCED_LLM_MODEL_NAME = "gpt-4o"

    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200
    
    # Blank RFI Parser Configuration
    BLANK_RFI_CHUNK_THRESHOLD_CHARS = 4000
    BLANK_RFI_CHUNK_OVERLAP = 500
    BLANK_RFI_MIN_CHUNK_SIZE = 2000
    
    # File Upload Configuration (shared across all APIs)
    VALID_FILE_EXTENSIONS = ['.pdf', '.docx', '.doc', '.xls', '.xlsx', '.md']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_FILE_EXTENSION = ".txt"
    
    # Knowledge Base Configuration
    KNOWLEDGE_BASE_ENTRY_TYPES = [
        "organizational_fact", "hr_detail", "financial", "service", 
        "sop", "policy", "past_response"
    ]
    
    KNOWLEDGE_BASE_SERVICE_CATEGORIES = [
        "clinical_Operations", "data_Management", "regulatory_Affairs"
    ]
    
    KNOWLEDGE_BASE_BATCH_SIZE = 100
    KNOWLEDGE_BASE_DOCUMENT_TYPE = "Knowledge Base"
    
    # Document Type Defaults
    DEFAULT_DOCUMENT_TYPE = "RFI/RFP"
    DEFAULT_DOCUMENT_GRADE_STANDARD = "Standard"
    DEFAULT_DOCUMENT_GRADE_PROCESSING = "Processing"
    
    # API Default Values (keeping user mocked as requested)
    DEFAULT_USER = "test"
    DEFAULT_DUE_DAYS = 90
    
    # Question Status Values
    QUESTION_STATUS_PENDING = "pending"
    QUESTION_STATUS_COMPLETED = "completed"
    QUESTION_STATUS_DRAFT = "draft"
    QUESTION_STATUS_IN_PROGRESS = "Inprogress"