import asyncio
from typing import List, Dict, Any, Tuple
from datetime import datetime
import numpy as np
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.llm_provider import get_fast_llm
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Chunk
from config import Config

logger = get_logger(__name__)

class VectorSearchService:
    """
    Service for performing vector similarity search and reranking of results.
    """
    
    def __init__(self):
        self.config = Config()
        self.llm = get_fast_llm()
        
        # Initialize ChromaDB
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.config.OPENAI_API_KEY,
            model_name="text-embedding-3-large"
        )
        
        self.client = PersistentClient(path=self.config.VECTOR_DB_PATH)
        
        # Use the correct collection name
        collection_name = getattr(self.config, 'COLLECTION_NAME', 'chunks')
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.openai_ef
        )
        
        logger.info(f"VectorSearchService initialized with collection: {collection_name}")

    def _serialize_datetime(self, obj):
        """Helper function to serialize datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        else:
            return obj

    async def batch_search_and_rerank(self, questions: List[str], top_k: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform batch vector search for multiple questions and rerank results.
        
        Args:
            questions: List of questions to search for
            top_k: Number of top results to retrieve per question
            
        Returns:
            Dictionary mapping each question to its reranked results
        """
        logger.info(f"Performing batch search for {len(questions)} questions...")
        
        # Step 1: Batch vector search
        search_results = self.collection.query(
            query_texts=questions,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Step 2: Rerank results for each question
        reranked_results = {}
        for i, question in enumerate(questions):
            question_results = {
                "documents": search_results["documents"][i],
                "metadatas": search_results["metadatas"][i] if search_results["metadatas"] else [], 
                "distances": search_results["distances"][i] if search_results["distances"] else []
            }
            
            reranked = await self._rerank_results(question, question_results)
            reranked_results[question] = reranked
        
        return reranked_results

    async def _rerank_results(self, question: str, search_results: Dict[str, List]) -> List[Dict[str, Any]]:
        """
        Rerank search results using LLM-based relevance scoring.
        """
        documents = search_results["documents"]
        metadatas = search_results["metadatas"]
        distances = search_results["distances"]
        
        if not documents:
            return []
        
        # Create reranking prompts
        rerank_prompts = []
        for doc in documents:
            prompt = f"""
            Question: {question}
            
            Document Content: {doc[:500]}...
            
            On a scale of 1-10, how relevant is this document to answering the question?
            Consider:
            - Direct relevance to the question topic
            - Quality and completeness of information
            - Specificity to the question being asked
            
            Respond with only a number between 1 and 10.
            """
            rerank_prompts.append(prompt)
        
        # Get relevance scores from LLM
        relevance_scores = await self._batch_score_relevance(rerank_prompts)
        
        # Combine with vector similarity scores
        combined_results = []
        for i, (doc, distance, relevance_score) in enumerate(
            zip(documents, distances, relevance_scores)
        ):
            # Get metadata safely
            metadata = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
            
            # Get full metadata from database if needed
            chunk_id = metadata.get("chunk_id")
            if chunk_id:
                full_metadata = await self._get_chunk_metadata(chunk_id)
                metadata.update(full_metadata)
            
            # Calculate combined confidence score
            vector_similarity = 1 - distance  # Convert distance to similarity
            combined_score = (relevance_score * 0.7) + (vector_similarity * 0.3)
            
            # Serialize datetime objects in metadata
            clean_metadata = self._serialize_datetime(metadata)
            
            result = {
                "content": doc,
                "confidence_score": combined_score / 10.0,  # Normalize to 0-1
                "relevance_score": relevance_score,
                "vector_similarity": vector_similarity,
                "source_attribution": {
                    "document_name": clean_metadata.get("source_filename", "Unknown"),
                    "chunk_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                    "company_name": clean_metadata.get("company_name", "Unknown"),
                    "document_date": clean_metadata.get("document_date"),
                    "domain": clean_metadata.get("domain", "General"),
                    "question_type": clean_metadata.get("question_type", "Unknown"),
                    "document_type": clean_metadata.get("document_type", "Unknown")
                }
            }
            combined_results.append(result)
        
        # Sort by combined confidence score
        combined_results.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return combined_results[:5]  # Return top 5 reranked results

    async def _batch_score_relevance(self, prompts: List[str]) -> List[float]:
        """Score relevance for multiple prompts in parallel."""
        semaphore = asyncio.Semaphore(3)  # Limit concurrent LLM calls
        
        async def score_single(prompt):
            async with semaphore:
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.llm.invoke(prompt).content
                    )
                    # Extract numeric score
                    import re
                    match = re.search(r'\b([1-9]|10)\b', response)
                    return float(match.group(1)) if match else 5.0
                except Exception as e:
                    logger.error(f"Error scoring relevance: {e}")
                    return 5.0
        
        scores = await asyncio.gather(*[score_single(p) for p in prompts])
        return scores

    async def _get_chunk_metadata(self, chunk_id: str) -> Dict[str, Any]:
        """Retrieve full metadata for a chunk from the database."""
        try:
            db_session_generator = get_db_session()
            db_session = next(db_session_generator)
            
            chunk = db_session.query(Chunk).filter(Chunk.vector_id == chunk_id).first()
            
            if chunk:
                metadata = chunk.chunk_metadata or {}
                # Add document metadata
                if chunk.document:
                    metadata.update({
                        "source_filename": chunk.document.source_filename,
                        "document_date": chunk.document.created_at,
                        "document_type": chunk.document.document_type
                    })
                
                # Serialize datetime objects
                return self._serialize_datetime(metadata)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving chunk metadata: {e}")
            return {}
        finally:
            if 'db_session' in locals():
                db_session.close()