# rfiprocessor/services/file_upload_service.py

import os
import shutil
import uuid
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from config.config import Config
from rfiprocessor.utils.logger import get_logger

config = Config()
logger = get_logger(__name__)

class FileUploadService:
    """Shared service for file upload operations to eliminate repetition."""
    
    def __init__(self):
        self.allowed_extensions = config.VALID_FILE_EXTENSIONS
        self.max_file_size = config.MAX_FILE_SIZE
    
    def validate_file_size(self, size: int) -> None:
        """Validate file size."""
        if size > self.max_file_size:
            max_size_mb = self.max_file_size // (1024 * 1024)
            raise HTTPException(status_code=400, detail=f"File size exceeds {max_size_mb}MB limit")
    
    def validate_file_extension(self, filename: str, file_type: str = None, content_type: str = None) -> None:
        """Validate file extension."""
        # Check filename
        file_has_valid_extension = any(filename.lower().endswith(ext) for ext in self.allowed_extensions)
        
        # Check file_type parameter if provided
        type_has_valid_extension = False
        if file_type:
            type_has_valid_extension = any(file_type.lower().endswith(ext) for ext in self.allowed_extensions)
            type_matches_allowed = file_type.lower() in [ext.lower() for ext in self.allowed_extensions]
        else:
            type_matches_allowed = False
        
        # Check content type as fallback
        content_type_allowed = False
        if content_type:
            content_type_allowed = any(
                allowed_type in content_type.lower() 
                for allowed_type in ['pdf', 'word', 'excel', 'text']
            )
        
        if not file_has_valid_extension and not type_has_valid_extension and not type_matches_allowed and not content_type_allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(self.allowed_extensions)}. Received: filename='{filename}', file_type='{file_type}', content_type='{content_type}'")
    
    async def save_file(self, file: UploadFile, filename: str = None) -> str:
        """Save uploaded file and return the file path."""
        # Use provided filename or file's original filename
        actual_filename = filename or file.filename
        
        # Generate unique filename if needed
        if not actual_filename:
            file_id = str(uuid.uuid4())
            file_extension = config.DEFAULT_FILE_EXTENSION
            actual_filename = f"{file_id}{file_extension}"
        
        # Save to incoming directory
        incoming_path = os.path.join(config.INCOMING_DATA_PATH, actual_filename)
        os.makedirs(os.path.dirname(incoming_path), exist_ok=True)
        
        # Ensure file stream is at the beginning
        await file.seek(0)
        
        # Read the file content and save it
        content = await file.read()
        with open(incoming_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File saved successfully: {incoming_path}")
        return incoming_path
    
    def generate_document_id(self) -> str:
        """Generate unique document ID."""
        return str(uuid.uuid4()) 