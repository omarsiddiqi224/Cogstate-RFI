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

class BlankRfiParserAgent:
    """
    An agent that parses markdown content of an RFI/RFP document into a
    structured JSON format, including a summary, Qs (no answers), and metadata.
    """

    def __init__(self, llm=None):
        try:
            self.llm = llm or get_advanced_llm()
            # --- Summary Chain (expects string output) ---
            summary_prompt_content = load_prompt("rfi_parser_summary")
            if not summary_prompt_content:
                raise ValueError("RFI Parser summary prompt could not be loaded.")
            summary_prompt = PromptTemplate.from_template(summary_prompt_content)
            self.summary_chain = summary_prompt | self.llm | StrOutputParser()

            # --- Chunk Parsing Chain (expects JSON output) ---
            chunk_prompt_content = self._get_blank_chunk_prompt()
            chunk_prompt = PromptTemplate.from_template(chunk_prompt_content)
            self.chunk_chain = chunk_prompt | self.llm | JsonOutputParser()

            logger.info("BlankRfiParserAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize BlankRfiParserAgent: {e}", exc_info=True)
            raise

    def _get_blank_chunk_prompt(self):
        # Custom prompt for blank RFI (no answer field)
        return (
            "You are a highly accurate proposal-to-JSON transformation engine. "
            "You will convert the provided markdown-based RFI or RFP response into a structured JSON format.\n\n"
            "You MUST extract the following:\n"
            "1. **summary**: The executive summary provided below (reuse as-is).\n"
            "2. **description**: Descriptive, contextual content in the markdown that is not structured as a question.\n"
            "3. **questions**: Extract all questions. Be comprehensive and look for questions in all possible formats:\n"
            "   - **Standard Q&A**: Paragraphs clearly marked as questions.\n"
            "   - **Tables**: Treat any row in a markdown table as a potential question.\n"
            "   - **Checkbox Grids**: Questions followed by checkbox-style answers (e.g., `[x] Yes`, `[ ] No`).\n"
            "   - **Bulleted/Numbered Lists**: A question might be a top-level bullet or number.\n"
            "   - **Section Headers**: If a section header or bolded/underlined text reads like a question or prompt, treat it as a question.\n"
            "   - **Implicit/Contextual Q**: If a question is implied by context, formatting, or structure, extract it.\n"
            "   For each question you find, extract the following details:\n"
            "   - `question`: The full, cleaned question text.\n"
            "   - `domain`: A relevant business category like 'Security', 'Compliance', 'Support', 'Technology'. Use 'General' if the domain is not clear.\n"
            "   - `type`: Classify the question's nature. Use 'close-ended' for Yes/No, multiple choice, or checkbox questions. Use 'open-ended' for questions requiring a descriptive text answer.\n"
            "   If in doubt, extract as a question.\n"
            "4. **meta_data**:\n"
            "   - `company_name`: The name of the organization receiving the proposal (not the vendor submitting it).\n"
            "   - `date`: A valid ISO-8601 date (YYYY-MM-DD) from the document.\n"
            "   - `category`: Either 'RFI' or 'RFP'.\n"
            "   - `type`: Always 'PastResponse'.\n"
            "Return a single valid JSON object with these keys: summary, description, questions, meta_data. Do not invent or hallucinate content. Only extract what is present in the markdown chunk, but err on the side of extracting more questions rather than fewer. If in doubt, extract as a question.\n\nMarkdown Content:\n{text}\n"
        )

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
            if len(chunk_content) > CHUNK_THRESHOLD_CHARS:
                for j in range(0, len(chunk_content), CHUNK_THRESHOLD_CHARS - CHUNK_OVERLAP):
                    start = max(0, j - CHUNK_OVERLAP)
                    end = j + CHUNK_THRESHOLD_CHARS
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
            logger.warning(f"Chunk processing failed: {e}. Attempting to split.")
            if len(chunk_text) <= MIN_CHUNK_SIZE:
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