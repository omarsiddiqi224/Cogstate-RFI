# rfiprocessor/agents/rfi_parser.py

import re
from datetime import date
from typing import Dict, Any, List
import concurrent.futures

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.prompt_loader import load_prompt

logger = get_logger(__name__)

# Constants for chunking logic
CHUNK_THRESHOLD_CHARS = 4000  # Reduced chunk size
CHUNK_OVERLAP = 500  # Overlap between chunks
MIN_CHUNK_SIZE = 2000

class RfiParserAgent:
    """
    An agent that parses markdown content of an RFI/RFP document into a
    structured JSON format, including a summary, Q&A pairs, and metadata.
    """

    def __init__(self):
        """
        Initializes the agent by setting up the LLM, loading prompts,
        and creating the processing chains.
        """
        try:
            self.llm = get_advanced_llm()
            
            # --- Summary Chain (expects string output) ---
            summary_prompt_content = load_prompt("rfi_parser_summary")
            if not summary_prompt_content:
                raise ValueError("RFI Parser summary prompt could not be loaded.")
            summary_prompt = PromptTemplate.from_template(summary_prompt_content)
            self.summary_chain = summary_prompt | self.llm | StrOutputParser()

            # --- Chunk Parsing Chain (expects JSON output) ---
            chunk_prompt_content = load_prompt("rfi_parser_chunking")
            if not chunk_prompt_content:
                raise ValueError("RFI Parser chunk prompt could not be loaded.")
            chunk_prompt = PromptTemplate.from_template(chunk_prompt_content)
            # We use a JsonOutputParser which is more robust than manual json.loads
            self.chunk_chain = chunk_prompt | self.llm | JsonOutputParser()

            logger.info("RfiParserAgent initialized successfully.")

        except Exception as e:
            logger.error(f"Error initializing RfiParserAgent: {str(e)}", exc_info=True)
            raise

    def _extract_company_name_from_summary(self, summary: str) -> str:
        """Extracts company name from the summary text using regex patterns."""
        patterns = [
            r"Company Name:\s*(.+)", r"Client:\s*(.+)", r"For:\s*(.+)", r"Recipient:\s*(.+)",
            r"questionnaire is for\s*([A-Z][A-Za-z0-9 &,.\-']+)",
            r"for the company\s*([A-Z][A-Za-z0-9 &,.\-']+)",
        ]
        for pat in patterns:
            match = re.search(pat, summary, re.IGNORECASE)
            if match:
                return match.group(1).strip().splitlines()[0]
        return "Unknown"

    def _section_based_chunks(self, text: str) -> List[str]:
        """Splits text by '## ' headings, handling large sections, with overlap."""
        sections = text.split('\n## ')
        chunks = []
        for i, sec in enumerate(sections):
            chunk_content = f"## {sec}" if i > 0 else sec
            if len(chunk_content) > CHUNK_THRESHOLD_CHARS:
                for j in range(0, len(chunk_content), CHUNK_THRESHOLD_CHARS - CHUNK_OVERLAP):
                    start = max(0, j - CHUNK_OVERLAP)
                    end = j + CHUNK_THRESHOLD_CHARS
                    chunks.append(chunk_content[start:end])
            else:
                chunks.append(chunk_content)
        return chunks

    def _deduplicate_qa_pairs(self, qa_pairs):
        seen = set()
        deduped = []
        for qa in qa_pairs:
            key = (qa.get('question', '').strip().lower(), qa.get('answer', '').strip().lower())
            if key not in seen:
                seen.add(key)
                deduped.append(qa)
        return deduped

    def _safe_convert_chunk(self, chunk_text: str) -> Dict[str, Any]:
        """
        Safely processes a chunk, with a recursive split-and-retry mechanism
        for handling errors, especially JSON parsing failures.
        """
        try:
            # Chunk-level logging: print the chunk sent to the LLM
            # logger.debug(f"Chunk passed to LLM: {chunk_text[:1000]}")
            # Use the LangChain chain to process the chunk
            response = self.chunk_chain.invoke({"text": chunk_text})
            # Chunk-level logging: print the LLM's response
            # logger.debug(f"LLM response: {response}")
            return response
        except Exception as e:
            logger.warning(f"Chunk processing failed: {e}. Attempting to split.")
            if len(chunk_text) <= MIN_CHUNK_SIZE:
                logger.error(f"Chunk is too small to split further ({len(chunk_text)} chars). Skipping.")
                return {"qa_pairs": [], "narrative_content": ""}

            mid = len(chunk_text) // 2
            left_half, right_half = chunk_text[:mid], chunk_text[mid:]
            
            # Process halves recursively
            left_data = self._safe_convert_chunk(left_half)
            right_data = self._safe_convert_chunk(right_half)

            # Merge results
            merged_qa = (left_data.get("qa_pairs", []) or []) + (right_data.get("qa_pairs", []) or [])
            merged_narrative = f"{left_data.get('narrative_content', '')}\n\n{right_data.get('narrative_content', '')}".strip()
            
            return {"qa_pairs": merged_qa, "narrative_content": merged_narrative}

    def parse(self, markdown_content: str) -> Dict[str, Any]:
        """
        Main method to parse a full markdown document into a structured dictionary.
        Improved to robustly aggregate meta_data, handle chunk errors, and always output the correct structure.
        """
        if not markdown_content.strip():
            raise ValueError("Input markdown content cannot be empty.")

        logger.info("Generating executive summary...")
        summary = self.summary_chain.invoke({"text": markdown_content})

        logger.info("Splitting document into processable chunks...")
        chunks = self._section_based_chunks(markdown_content)

        all_qa_pairs = []
        all_descriptions = []
        meta_data = None

        logger.info(f"Processing {len(chunks)} chunks concurrently...")
        def process_one_chunk(chunk: str) -> Dict[str, Any]:
            try:
                chunk_data = self._safe_convert_chunk(chunk)
                return chunk_data
            except Exception as exc:
                logger.error(f"A chunk generated an exception: {exc}", exc_info=True)
                return {"qa_pairs": [], "description": ""}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_one_chunk, chunks))

        for i, chunk_data in enumerate(results):
            # Prefer meta_data from the first chunk that provides it
            if meta_data is None and isinstance(chunk_data, dict) and "meta_data" in chunk_data:
                meta_data = chunk_data["meta_data"]
            # Aggregate Q&A pairs
            if chunk_data.get("qa_pairs"):
                all_qa_pairs.extend(chunk_data["qa_pairs"])
            # Aggregate descriptions (use 'description' if present, else fallback to 'narrative_content' for backward compatibility)
            desc = chunk_data.get("description") or chunk_data.get("narrative_content")
            if desc:
                if isinstance(desc, list):
                    desc = "\n".join(str(x) for x in desc)
                all_descriptions.append(str(desc).strip())

        # Deduplicate Q&A pairs
        all_qa_pairs = self._deduplicate_qa_pairs(all_qa_pairs)

        # Fallback meta_data extraction from summary if not found in chunks
        if not meta_data:
            company_name = self._extract_company_name_from_summary(summary)
            from datetime import date
            meta_data = {
                "company_name": company_name,
                "date": str(date.today()),
                "category": "RFI",
                "type": "PastResponse"
            }

        final_data = {
            "summary": summary,
            "description": "\n\n".join(filter(None, all_descriptions)).strip(),
            "qa_pairs": all_qa_pairs,
            "meta_data": meta_data
        }
        logger.info(f"Successfully parsed document. Found {len(all_qa_pairs)} Q&A pairs.")
        return final_data