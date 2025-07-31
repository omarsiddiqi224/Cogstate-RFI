import re
from datetime import date
from typing import Dict, Any, List
import concurrent.futures

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.prompt_loader import load_prompt
from config.config import Config

logger = get_logger(__name__)

# Initialize config
config = Config()

class BlankRfiParserAgent:
    """
    An agent that parses markdown content of an RFI/RFP document into a
    structured JSON format, including a summary, Qs (no answers), and metadata.
    """

    def __init__(self, llm):
        try:
            self.llm = llm
            # --- Summary Chain (expects string output) ---
            summary_prompt_content = load_prompt("rfi_parser_summary")
            if not summary_prompt_content:
                raise ValueError("RFI Parser summary prompt could not be loaded.")
            summary_prompt = PromptTemplate.from_template(summary_prompt_content)

            def llm_chain_wrapper(input):
                prompt = input.get("text") if isinstance(input, dict) else input
                return self.llm.invoke(prompt)

            self.summary_chain = summary_prompt | llm_chain_wrapper | StrOutputParser()

            # --- Chunk Parsing Chain (expects JSON output) ---
            chunk_prompt_content = load_prompt("blank_rfi_parser")
            if not chunk_prompt_content:
                raise ValueError("Blank RFI Parser prompt could not be loaded.")
            chunk_prompt = PromptTemplate.from_template(chunk_prompt_content)
            self.chunk_chain = chunk_prompt | llm_chain_wrapper | JsonOutputParser()

            logger.info("BlankRfiParserAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing BlankRfiParserAgent: {str(e)}", exc_info=True)
            raise

    def _extract_company_name_from_summary(self, summary: str) -> str:
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
        sections = text.split('\n## ')
        chunks = []
        for i, sec in enumerate(sections):
            chunk_content = f"## {sec}" if i > 0 else sec
            if len(chunk_content) > config.BLANK_RFI_CHUNK_THRESHOLD_CHARS:
                for j in range(0, len(chunk_content), config.BLANK_RFI_CHUNK_THRESHOLD_CHARS - config.BLANK_RFI_CHUNK_OVERLAP):
                    start = max(0, j - config.BLANK_RFI_CHUNK_OVERLAP)
                    end = j + config.BLANK_RFI_CHUNK_THRESHOLD_CHARS
                    chunks.append(chunk_content[start:end])
            else:
                chunks.append(chunk_content)
        return chunks

    def _deduplicate_questions(self, questions):
        seen = set()
        deduped = []
        for q in questions:
            key = (q.get('question', '').strip().lower(), q.get('domain', '').strip().lower())
            if key not in seen:
                seen.add(key)
                deduped.append(q)
        return deduped

    def _safe_convert_chunk(self, chunk_text: str) -> Dict[str, Any]:
        try:
            logger.info("\n--- CHUNK SENT TO LLM ---\n" + chunk_text[:1000] + ("..." if len(chunk_text) > 1000 else "") + "\n--- END OF CHUNK ---\n")
            response = self.chunk_chain.invoke({"text": chunk_text})
            logger.info(f"\n--- LLM RESPONSE FOR CHUNK ---\n{response}\n--- END OF LLM RESPONSE ---\n")
            return response
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}", exc_info=True)
            if len(chunk_text) <= config.BLANK_RFI_MIN_CHUNK_SIZE:
                logger.error(f"Chunk is too small to split further ({len(chunk_text)} chars). Skipping.")
                return {"questions": [], "narrative_content": ""}
            mid = len(chunk_text) // 2
            left_half, right_half = chunk_text[:mid], chunk_text[mid:]
            left_data = self._safe_convert_chunk(left_half)
            right_data = self._safe_convert_chunk(right_half)
            merged_qs = (left_data.get("questions", []) or []) + (right_data.get("questions", []) or [])
            merged_narrative = f"{left_data.get('narrative_content', '')}\n\n{right_data.get('narrative_content', '')}".strip()
            return {"questions": merged_qs, "narrative_content": merged_narrative}

    def parse(self, markdown_content: str) -> Dict[str, Any]:
        if not markdown_content.strip():
            raise ValueError("Input markdown content cannot be empty.")
        logger.info("Generating executive summary...")
        summary = self.summary_chain.invoke({"text": markdown_content})
        logger.info("Splitting document into processable chunks...")
        chunks = self._section_based_chunks(markdown_content)
        all_questions = []
        all_descriptions = []
        meta_data = None
        logger.info(f"Processing {len(chunks)} chunks concurrently...")
        def process_one_chunk(chunk):
            try:
                chunk_data = self._safe_convert_chunk(chunk)
                return chunk_data
            except Exception as exc:
                logger.error(f"A chunk generated an exception: {exc}", exc_info=True)
                return {"questions": [], "description": ""}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(process_one_chunk, chunks))
        for i, chunk_data in enumerate(results):
            if meta_data is None and isinstance(chunk_data, dict) and "meta_data" in chunk_data:
                meta_data = chunk_data["meta_data"]
            if chunk_data.get("questions"):
                all_questions.extend(chunk_data["questions"])
            desc = chunk_data.get("description") or chunk_data.get("narrative_content")
            if desc:
                if isinstance(desc, list):
                    desc = "\n".join(str(x) for x in desc)
                all_descriptions.append(str(desc).strip())
        all_questions = self._deduplicate_questions(all_questions)
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
            "questions": all_questions,
            "meta_data": meta_data
        }
        logger.info(f"Successfully parsed document. Found {len(all_questions)} questions.")
        return final_data 