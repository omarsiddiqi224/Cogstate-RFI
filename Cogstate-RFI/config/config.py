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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4-turbo-preview")
    VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "db/chroma_db")

    INCOMING_DATA_PATH = "data/raw/incoming"
    PROCESSED_DATA_PATH = "data/raw/processed"
    INCOMING_MARKDOWN_PATH = "data/markdown/incoming"
    PROCESSED_MARKDOWN_PATH = "data/markdown/processed"

    VALID_FILE_EXTNS = ['.doc', '.docm', '.docx', '.pdf', '.pptx', '.txt', '.xls', '.xlsm', '.xlsx']

    MRKDN_FILE_EXTNS = ['.docx', '.pdf', '.pptx']
    UNSTRD_FILE_EXTNS = ['.doc', '.docm', '.txt', '.xls' , '.xlsx', 'xlsm']

    PROMPTS_DIR = "rfiprocessor/prompts"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    FAST_LLM_MODEL_NAME = "gpt-4-turbo"
    REASONING_LLM_MODEL_NAME = "o3"
    ADVANCED_LLM_MODEL_NAME = "gpt-4o"

    CHUNK_SIZE = 2000
    CHUNK_OVERLAP = 200