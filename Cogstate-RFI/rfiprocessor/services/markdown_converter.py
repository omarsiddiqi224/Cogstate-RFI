from pathlib import Path
from datetime import datetime
import logging
from enum import Enum
from typing import Tuple

from markitdown import MarkItDown
from unstructured.partition.auto import partition

from config import Config
from rfiprocessor.utils.logger import get_logger

logger = get_logger(__name__)
config = Config()

class ProcessorType(Enum):
    MARKITDOWN = "markitdown"
    UNSTRUCTURED = "unstructured"

class MarkdownConverter:
    """Converts input files to markdown using specified processor"""
    
    def __init__(self):
        self.markitdown = MarkItDown()
    
    def convert_to_markdown(
        self,
        file_path: str,
        processor: ProcessorType = ProcessorType.MARKITDOWN
    ) -> Tuple[str, str]:
        """
        Convert input file to markdown and save to output directory
        Args:
            file_path: Path to input file
            processor: Conversion method (MARKITDOWN or UNSTRUCTURED)
        Returns:
            Tuple of (markdown_content, markdown_file_path)
        """
        logger.info(f"Converting file: {file_path} with {processor.value}")
        
        try:
            # Process based on specified method
            if processor == ProcessorType.MARKITDOWN:
                markdown_content = self._process_with_markitdown(file_path)
            elif processor == ProcessorType.UNSTRUCTURED:
                markdown_content = self._process_with_unstructured(file_path)
            else:
                raise ValueError(f"Unsupported processor: {processor}")
            
            # Save markdown file
            markdown_path = self._save_markdown(
                content=markdown_content,
                original_path=file_path
            )
            
            return markdown_content, markdown_path
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}")
            raise
    
    def _process_with_markitdown(self, file_path: str) -> str:
        """Process document with MarkItDown"""
        try:
            result = self.markitdown.convert(file_path)
            return result.text_content
        except Exception as e:
            logger.error(f"MarkItDown processing failed: {e}")
            raise
    
    def _process_with_unstructured(self, file_path: str) -> str:
        """Process document with Unstructured"""
        try:
            elements = partition(file_path)
            
            # Convert elements to markdown
            markdown_lines = []
            for element in elements:
                if hasattr(element, 'category'):
                    if element.category == "Title":
                        markdown_lines.append(f"# {element.text}")
                    elif element.category == "NarrativeText":
                        markdown_lines.append(element.text)
                    elif element.category == "ListItem":
                        markdown_lines.append(f"- {element.text}")
                    else:
                        markdown_lines.append(element.text)
                else:
                    markdown_lines.append(str(element))
            
            return "\n\n".join(markdown_lines)
        except Exception as e:
            logger.error(f"Unstructured processing failed: {e}")
            raise
    
    def _save_markdown(self, content: str, original_path: str) -> str:
        """Save markdown content to output directory"""
        output_dir = Path(config.INCOMING_MARKDOWN_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp
        original_name = Path(original_path).stem
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{original_name}.md"
        
        # Save file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved markdown to: {output_path}")
        return str(output_path)