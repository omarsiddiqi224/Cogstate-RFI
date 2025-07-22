# rfiprocessor/models/data_models.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union
from datetime import date

# Define a literal type for the question types for strict validation
QuestionType = Literal["narrative", "open-ended", "close-ended", "check-box"]

class QAPair(BaseModel):
    """Pydantic model for a single Question-Answer pair."""
    question: str = Field(..., description="The question text from the RFI/RFP.")
    answer: str = Field(..., description="The corresponding answer text.")
    domain: Optional[str] = Field(None, description="The business or technical domain of the question.")
    type: Optional[QuestionType] = Field(None, description="The type of the question.")

class RfiMetadata(BaseModel):
    """Pydantic model for the metadata of an RFI/RFP document."""
    company_name: str = Field(..., description="The name of the company the RFI/RFP is for.")
    doc_date: Optional[date] = Field(None, description="The date of the document.")
    category: Literal["RFI", "RFP"] = Field(..., description="The category of the document.")
    type: Literal["PastResponse"] = Field(..., description="The type of the content.")

class RFIJson(BaseModel):
    """
    The main Pydantic model to validate the entire JSON structure
    parsed from an RFI/RFP document.
    """
    summary: Optional[str] = Field(None, description="A brief summary of the RFI/RFP document.")
    description: Optional[str] = Field(None, description="A more detailed description of the document's content.")
    qa_pairs: List[QAPair] = Field(..., description="A list of all question-answer pairs found in the document.")
    meta_data: RfiMetadata = Field(..., description="Metadata associated with the document.")

    @field_validator('qa_pairs')
    @classmethod
    def check_qa_pairs_not_empty(cls, v):
        """Ensures that the qa_pairs list is not empty."""
        if not v:
            raise ValueError('qa_pairs list cannot be empty')
        return v