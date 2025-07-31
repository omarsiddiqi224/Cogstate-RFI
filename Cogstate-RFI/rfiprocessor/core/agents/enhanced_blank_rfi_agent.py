import asyncio
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import concurrent.futures

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm, get_fast_llm
from rfiprocessor.services.prompt_loader import load_prompt
from rfiprocessor.core.agents.blank_rfi_parser import BlankRfiParserAgent
from rfiprocessor.services.vector_search_service import VectorSearchService
from rfiprocessor.services.answer_synthesis_service import AnswerSynthesisService

logger = get_logger(__name__)

class EnhancedBlankRfiAgent:
    """
    Enhanced agent that processes blank RFI documents by:
    1. Extracting questions
    2. Generating similar question variants
    3. Performing vector search and retrieval
    4. Synthesizing answers with confidence scores and source attribution
    """

    def __init__(self):
        try:
            self.advanced_llm = get_advanced_llm()
            self.fast_llm = get_fast_llm()
            
            # Initialize sub-agents and services
            self.blank_rfi_parser = BlankRfiParserAgent(llm=self.fast_llm)
            self.vector_search_service = VectorSearchService()
            self.answer_synthesis_service = AnswerSynthesisService()
            
            # Load prompts
            question_variant_prompt = load_prompt("question_variant_generator")
            if not question_variant_prompt:
                raise ValueError("Question variant generator prompt could not be loaded.")
            
            self.question_variant_chain = (
                PromptTemplate.from_template(question_variant_prompt) | 
                self.advanced_llm | 
                JsonOutputParser()
            )
            
            logger.info("EnhancedBlankRfiAgent initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedBlankRfiAgent: {e}", exc_info=True)
            raise

    async def process_document(self, markdown_content: str, processing_mode: str = "batch") -> Dict[str, Any]:
        """
        Main method to process a blank RFI document.
        
        Args:
            markdown_content: The markdown content of the blank RFI
            processing_mode: "batch" or "incremental"
            
        Returns:
            Structured response with questions, answers, confidence scores, and source attribution
        """
        logger.info(f"Starting document processing in {processing_mode} mode...")
        
        # Step 1: Extract questions from blank RFI
        parsed_data = self.blank_rfi_parser.parse(markdown_content)
        question_objects = parsed_data.get("questions", [])
        
        # Extract question strings from question objects
        questions = []
        for q in question_objects:
            if isinstance(q, dict) and "question" in q:
                questions.append(q["question"])
            elif isinstance(q, str):
                questions.append(q)
            else:
                logger.warning(f"Unexpected question format: {type(q)} - {q}")
                questions.append(str(q))
        
        if not questions:
            return {
                "status": "completed",
                "total_questions": 0,
                "results": [],
                "metadata": parsed_data.get("meta_data", {})
            }
        
        logger.info(f"Extracted {len(questions)} questions from document")
        
        if processing_mode == "batch":
            return await self._process_batch(questions, parsed_data)
        else:
            return await self._process_incremental(questions, parsed_data)

    async def process_single_question(self, question: str) -> Dict[str, Any]:
        """Process a single question and return answer with attribution."""
        result = await self._process_question_with_variants(question)
        return {
            "question": question,
            "answer": result["answer"],
            "confidence_score": result["confidence_score"],
            "sources": result["sources"],
            "processing_metadata": result["metadata"]
        }

    async def _process_batch(self, questions: List[str], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all questions in parallel."""
        logger.info("Processing all questions in batch mode...")
        
        # Process questions concurrently with controlled concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent processing
        
        async def process_with_semaphore(question):
            async with semaphore:
                return await self._process_question_with_variants(question)
        
        # Execute all questions concurrently
        tasks = [process_with_semaphore(q) for q in questions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format results
        formatted_results = []
        for i, (question, result) in enumerate(zip(questions, results)):
            if isinstance(result, Exception):
                logger.error(f"Error processing question {i+1}: {result}")
                formatted_results.append({
                    "question": question,
                    "answer": "Error processing question",
                    "confidence_score": 0.0,
                    "sources": [],
                    "error": str(result)
                })
            else:
                formatted_results.append({
                    "question": question,
                    "answer": result["answer"],
                    "confidence_score": result["confidence_score"],
                    "sources": result["sources"],
                    "processing_metadata": result["metadata"]
                })
        
        return {
            "status": "completed",
            "total_questions": len(questions),
            "results": formatted_results,
            "metadata": parsed_data.get("meta_data", {}),
            "processing_summary": {
                "successful": len([r for r in results if not isinstance(r, Exception)]),
                "failed": len([r for r in results if isinstance(r, Exception)]),
                "timestamp": datetime.now().isoformat()
            }
        }

    async def _process_incremental(self, questions: List[str], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process questions one by one with progress updates."""
        logger.info("Processing questions incrementally...")
        
        results = []
        for i, question in enumerate(questions):
            try:
                logger.info(f"Processing question {i+1}/{len(questions)}")
                result = await self._process_question_with_variants(question)
                
                formatted_result = {
                    "question": question,
                    "answer": result["answer"],
                    "confidence_score": result["confidence_score"],
                    "sources": result["sources"],
                    "processing_metadata": result["metadata"]
                }
                results.append(formatted_result)
                
                # Yield progress update (for streaming)
                yield {
                    "status": "processing",
                    "progress": {
                        "current": i + 1,
                        "total": len(questions),
                        "percentage": ((i + 1) / len(questions)) * 100
                    },
                    "current_result": formatted_result
                }
                
            except Exception as e:
                logger.error(f"Error processing question {i+1}: {e}")
                error_result = {
                    "question": question,
                    "answer": "Error processing question",
                    "confidence_score": 0.0,
                    "sources": [],
                    "error": str(e)
                }
                results.append(error_result)
        
        # Final result
        yield {
            "status": "completed",
            "total_questions": len(questions),
            "results": results,
            "metadata": parsed_data.get("meta_data", {}),
            "processing_summary": {
                "successful": len([r for r in results if "error" not in r]),
                "failed": len([r for r in results if "error" in r]),
                "timestamp": datetime.now().isoformat()
            }
        }

    async def _process_question_with_variants(self, question: str) -> Dict[str, Any]:
        """
        Process a single question by generating variants, searching, and synthesizing answer.
        """
        # Ensure question is a string
        if not isinstance(question, str):
            question = str(question)
        
        # Step 1: Generate question variants
        variants = await self._generate_question_variants(question)
        all_questions = [question] + variants
        
        # Safe string slicing for logging
        question_preview = question[:100] + "..." if len(question) > 100 else question
        logger.info(f"Generated {len(variants)} variants for question: {question_preview}")
        
        # Step 2: Perform vector search for all question variants
        search_results = await self.vector_search_service.batch_search_and_rerank(all_questions)
        
        # Step 3: Synthesize answer from all retrieved contexts
        synthesis_result = await self.answer_synthesis_service.synthesize_answer(
            original_question=question,
            question_variants=variants,
            search_results=search_results
        )
        
        return synthesis_result

    async def _generate_question_variants(self, question: str) -> List[str]:
        """Generate 5 variant questions for better search coverage."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.question_variant_chain.invoke({"question": question})
            )
            
            variants = response.get("variants", [])
            # Ensure we have exactly 5 variants
            if len(variants) < 5:
                variants.extend([question] * (5 - len(variants)))
            
            return variants[:5]
            
        except Exception as e:
            logger.error(f"Error generating question variants: {e}")
            # Return semantic variations as fallback
            return [
                f"What are the details about {question.lower()}?",
                f"Can you explain {question.lower()}?",
                f"Please describe {question.lower()}",
                f"What information is available regarding {question.lower()}?",
                f"How does your organization handle {question.lower()}?"
            ]