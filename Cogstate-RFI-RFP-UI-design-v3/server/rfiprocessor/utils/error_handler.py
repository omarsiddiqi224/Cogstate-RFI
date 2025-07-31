# rfiprocessor/utils/error_handler.py

from fastapi import HTTPException
from typing import Optional

class APIErrorHandler:
    """Standardized error handling for API responses."""
    
    @staticmethod
    def not_found(entity: str, identifier: str, identifier_type: str = "id") -> HTTPException:
        """Generate standardized 404 error."""
        return HTTPException(
            status_code=404, 
            detail=f"{entity} with {identifier_type} '{identifier}' not found"
        )
    
    @staticmethod
    def bad_request(message: str) -> HTTPException:
        """Generate standardized 400 error."""
        return HTTPException(status_code=400, detail=message)
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> HTTPException:
        """Generate standardized 500 error."""
        return HTTPException(status_code=500, detail="Internal server error")
    
    @staticmethod
    def validation_error(field: str, message: str) -> HTTPException:
        """Generate standardized validation error."""
        return HTTPException(
            status_code=422, 
            detail=f"Validation error for field '{field}': {message}"
        )
    
    @staticmethod
    def forbidden(message: str = "Access denied") -> HTTPException:
        """Generate standardized 403 error."""
        return HTTPException(status_code=403, detail=message)
    
    @staticmethod
    def conflict(message: str) -> HTTPException:
        """Generate standardized 409 error."""
        return HTTPException(status_code=409, detail=message)