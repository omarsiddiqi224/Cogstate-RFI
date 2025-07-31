# rfiprocessor/utils/data_access.py

from typing import Dict, List, Any, Optional

class DataAccessUtils:
    """Utility functions for consistent data access patterns."""
    
    @staticmethod
    def get_safe_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Safely get payload with default empty dict."""
        return payload or {}
    
    @staticmethod
    def get_safe_sections(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Safely get saved_sections from payload."""
        safe_payload = DataAccessUtils.get_safe_payload(payload)
        return safe_payload.get("saved_sections", [])
    
    @staticmethod
    def get_safe_qa_pairs(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Safely get qa_pairs from payload."""
        safe_payload = DataAccessUtils.get_safe_payload(payload)
        return safe_payload.get("qa_pairs", [])
    
    @staticmethod
    def get_safe_metadata(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Safely get meta_data from payload."""
        safe_payload = DataAccessUtils.get_safe_payload(payload)
        return safe_payload.get("meta_data", {})
    
    @staticmethod
    def calculate_progress(completed_count: int, total_count: int) -> int:
        """Calculate progress percentage safely."""
        if total_count == 0:
            return 0
        return int((completed_count / total_count) * 100)
    
    @staticmethod
    def get_section_by_id(sections: List[Dict[str, Any]], section_id: str) -> Optional[Dict[str, Any]]:
        """Find section by ID safely."""
        for section in sections:
            if section.get("id") == section_id:
                return section
        return None
    
    @staticmethod
    def get_question_by_id(qa_pairs: List[Dict[str, Any]], question_id: str) -> Optional[Dict[str, Any]]:
        """Find question by ID safely."""
        for qa in qa_pairs:
            if qa.get("questionId") == question_id:
                return qa
        return None