import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime
from langchain_core.prompts import PromptTemplate

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_advanced_llm
from rfiprocessor.services.prompt_loader import load_prompt

logger = get_logger(__name__)

def serialize_datetime(obj):
    """Helper function to serialize datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    else:
        return obj

class AnswerSynthesisService:
    """
    Service for synthesizing comprehensive answers from multiple search results.
    """
    
    def __init__(self):
        self.llm = get_advanced_llm()
        
        # Load synthesis prompt
        synthesis_prompt_content = load_prompt("answer_synthesis")
        if not synthesis_prompt_content:
            raise ValueError("Answer synthesis prompt could not be loaded.")
        
        self.synthesis_prompt = PromptTemplate.from_template(synthesis_prompt_content)
        
        logger.info("AnswerSynthesisService initialized successfully.")

    async def synthesize_answer(
        self, 
        original_question: str,
        question_variants: List[str],
        search_results: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Synthesize a comprehensive answer from multiple search results.
        
        Args:
            original_question: The original question
            question_variants: List of question variants
            search_results: Search results for each question variant
            
        Returns:
            Synthesized answer with confidence score and source attribution
        """
        logger.info(f"Synthesizing answer for question: {original_question[:100]}...")
        
        # Aggregate and deduplicate sources
        all_sources = []
        seen_sources = set()
        
        for question, results in search_results.items():
            for result in results:
                # Safe access to source attribution
                source_attr = result.get("source_attribution", {})
                document_name = source_attr.get("document_name", "Unknown")
                chunk_preview = source_attr.get("chunk_preview", "")
                
                # Create source key for deduplication
                source_key = (document_name, chunk_preview[:100])
                
                if source_key not in seen_sources:
                    seen_sources.add(source_key)
                    all_sources.append(result)
        
        # Sort sources by confidence score
        all_sources.sort(key=lambda x: x.get("confidence_score", 0.0), reverse=True)
        
        # Take top sources for synthesis
        top_sources = all_sources[:8]  # Use top 8 sources
        
        if not top_sources:
            return {
                "answer": "No relevant information found to answer this question.",
                "confidence_score": 0.0,
                "sources": [],
                "metadata": {
                    "total_sources_found": 0,
                    "synthesis_method": "no_sources"
                }
            }
        
        # Prepare context for synthesis
        context_items = []
        for i, source in enumerate(top_sources, 1):
            source_attr = source.get("source_attribution", {})
            context_items.append(
                f"Source {i} (Confidence: {source.get('confidence_score', 0.0):.2f}):\n"
                f"Document: {source_attr.get('document_name', 'Unknown')}\n"
                f"Content: {source.get('content', '')}\n"
                f"Company: {source_attr.get('company_name', 'Unknown')}\n"
                f"Domain: {source_attr.get('domain', 'General')}\n"
            )
        
        context = "\n\n".join(context_items)
        
        # Generate synthesized answer
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.synthesis_prompt | self.llm,
                {
                    "question": original_question,
                    "context": context,
                    "num_sources": len(top_sources)
                }
            )
            
            synthesized_answer = response.invoke({
                "question": original_question,
                "context": context,
                "num_sources": len(top_sources)
            }).content
            
        except Exception as e:
            logger.error(f"Error synthesizing answer: {e}")
            synthesized_answer = "Error occurred while synthesizing answer from available sources."
        
        # Calculate overall confidence score
        overall_confidence = self._calculate_overall_confidence(top_sources)
        
        # Prepare source attribution with datetime serialization
        source_attribution = []
        for source in top_sources:
            source_attr = source.get("source_attribution", {})
            
            # Serialize datetime objects
            clean_attr = {
                "document_name": source_attr.get("document_name", "Unknown"),
                "chunk_preview": source_attr.get("chunk_preview", ""),
                "confidence_score": source.get("confidence_score", 0.0),
                "company_name": source_attr.get("company_name", "Unknown"),
                "document_date": self._serialize_datetime(source_attr.get("document_date")),
                "domain": source_attr.get("domain", "General"),
                "question_type": source_attr.get("question_type", "Unknown"),
                "document_type": source_attr.get("document_type", "Unknown")
            }
            
            source_attribution.append(clean_attr)
        
        return {
            "answer": synthesized_answer,
            "confidence_score": overall_confidence,
            "sources": source_attribution,
            "metadata": {
                "total_sources_found": len(all_sources),
                "sources_used_for_synthesis": len(top_sources),
                "question_variants_processed": len(question_variants),
                "synthesis_method": "multi_source_synthesis"
            }
        }

    def _serialize_datetime(self, dt_obj):
        """Serialize datetime object to string."""
        if dt_obj is None:
            return None
        elif isinstance(dt_obj, datetime):
            return dt_obj.isoformat()
        elif isinstance(dt_obj, str):
            return dt_obj
        else:
            return str(dt_obj)

    def _calculate_overall_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score from multiple sources."""
        if not sources:
            return 0.0
        
        # Weighted average with higher weight for top sources
        weights = [1.0 / (i + 1) for i in range(len(sources))]  # 1.0, 0.5, 0.33, 0.25, ...
        total_weight = sum(weights)
        
        weighted_scores = [
            source.get("confidence_score", 0.0) * weight 
            for source, weight in zip(sources, weights)
        ]
        
        overall_confidence = sum(weighted_scores) / total_weight
        return min(overall_confidence, 1.0)  # Cap at 1.0