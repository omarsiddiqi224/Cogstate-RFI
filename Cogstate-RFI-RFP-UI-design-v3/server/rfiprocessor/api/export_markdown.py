import os
import tempfile
import json
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import RfiDocument
from rfiprocessor.models.data_models import ExportResponse
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)

async def export_rfi_to_markdown(response_id: str) -> ExportResponse:
    """
    Export an RFI response to a downloadable Markdown file.
    
    Args:
        response_id: The ID of the RFI response to export
    
    Returns:
        FileUploadResponse: A FileUploadResponse containing the path to the downloaded file
    """
    logger.info(f"=== EXPORTING RFI TO MARKDOWN ===")
    logger.info(f"Exporting RFI with response ID: {response_id}")
    
    db_session = next(get_db_session())
    
    try:
        # Find the RFI document by ID directly (same as get_specific_rfi_details)
        rfi_document = db_session.query(RfiDocument).filter(RfiDocument.id == response_id).first()
        
        if not rfi_document:
            # Fallback: try to find by searching through saved_sections (for regular RFI workflow)
            logger.info(f"Direct lookup failed, searching through saved_sections...")
            all_rfi_documents = db_session.query(RfiDocument).all()
            for doc in all_rfi_documents:
                if doc.payload and doc.payload.get("saved_sections"):
                    for section in doc.payload["saved_sections"]:
                        if section.get("id") == response_id:
                            rfi_document = doc
                            break
                    if rfi_document:
                        break
        
        if not rfi_document:
            raise HTTPException(status_code=404, detail=f"RFI document not found with response ID: {response_id}")
        
        logger.info(f"Found RFI document: {rfi_document.title}")
        
        # Convert JSON payload to Markdown
        markdown_content = convert_json_to_markdown(rfi_document.payload, rfi_document.title)
        
        # Create temporary file
        # Clean the title for filename (remove special characters, replace spaces with underscores)
        clean_title = rfi_document.title.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
        filename = f"{clean_title}.md"
        
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.getcwd(), "temp_exports")
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, filename)
        
        # Write markdown content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Markdown file created: {file_path}")
        
        return ExportResponse(
            success=True,
            message=f"RFI exported successfully to {filename}",
            filename=filename,
            file_path=file_path
        )
        
    except Exception as e:
        logger.error(f"Error exporting RFI to markdown: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        db_session.close()

def convert_json_to_markdown(payload: dict, title: str) -> str:
    """
    Convert RFI JSON payload to Markdown format with only questions and responses.
    
    Args:
        payload: The RFI JSON payload
        title: The RFI title
    
    Returns:
        str: The markdown content
    """
    markdown_lines = []
    
    # Header
    markdown_lines.append(f"# {title}")
    markdown_lines.append("")
    
    # Metadata section
    if payload.get("meta_data"):
        markdown_lines.append("## Metadata")
        markdown_lines.append("")
        meta_data = payload["meta_data"]
        for key, value in meta_data.items():
            if value:
                markdown_lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        markdown_lines.append("")
    
    # Questions and Answers section
    if payload.get("questions"):
        # Draft answers workflow
        questions = payload.get("questions", [])
        for i, question_data in enumerate(questions, 1):
            question_text = question_data.get("question", "")
            response_text = question_data.get("response", "")
            
            markdown_lines.append(f"## {i}. {question_text}")
            markdown_lines.append("")
            
            if response_text:
                markdown_lines.append(response_text)
            else:
                markdown_lines.append("*No response provided*")
            
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
    
    elif payload.get("saved_sections"):
        # Regular RFI workflow
        saved_sections = payload.get("saved_sections", [])
        for i, section_data in enumerate(saved_sections, 1):
            question_text = section_data.get("question", "")
            response_text = section_data.get("response", "")
            
            markdown_lines.append(f"## {i}. {question_text}")
            markdown_lines.append("")
            
            if response_text:
                markdown_lines.append(response_text)
            else:
                markdown_lines.append("*No response provided*")
            
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
    
    return "\n".join(markdown_lines) 