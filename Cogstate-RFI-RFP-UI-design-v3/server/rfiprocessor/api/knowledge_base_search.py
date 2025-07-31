# rfiprocessor/api/knowledge_base_search.py
 
from typing import List
from fastapi import HTTPException
 
from rfiprocessor.models.data_models import SearchKnowledgeBaseRequest, SearchKnowledgeBaseResponse
from rfiprocessor.services.vector_store_service import vector_store_service
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.utils.error_handler import APIErrorHandler
 
logger = get_logger(__name__)
 
async def search_knowledge_base(request: SearchKnowledgeBaseRequest) -> List[SearchKnowledgeBaseResponse]:
    """
    Search the knowledge base using vector similarity search.
    
    Args:
        request: SearchKnowledgeBaseRequest containing the search text
    
    Returns:
        List[SearchKnowledgeBaseResponse]: List of knowledge base items matching the search
    """
    logger.info(f"=== KNOWLEDGE BASE SEARCH STARTED ===")
    logger.info(f"Search text: '{request.searchText}'")
    
    try:
        # Validate search text
        if not request.searchText or not request.searchText.strip():
            logger.warning("Empty search text provided")
            return []
        
        search_text = request.searchText.strip()
        logger.info(f"Processing search for: '{search_text}'")
        
        # Use the vector store service to search for similar chunks
        similar_chunks = vector_store_service.search_similar_chunks(
            search_text,
            k=10
        )
        
        logger.info(f"Found {len(similar_chunks)} similar chunks")
        
        # Convert chunks to knowledge base response format
        knowledge_base_items = []
        for i, chunk in enumerate(similar_chunks):
            try:
                # Extract metadata from the chunk
                metadata = chunk.get('metadata', {})
                content = chunk.get('content', '')
                score = chunk.get('score', 0)
                
                # Create a unique ID for the knowledge base item
                kb_id = f"kb_{metadata.get('source_document_id', 'unknown')}_{i}"
                
                # Use real title from metadata or generate from content
                title = metadata.get('title', '')
                if not title:
                    # Extract title from content if not in metadata
                    title = content.split('\n')[0][:50] if content else 'Knowledge Base Item'
                
                # Use real category from metadata
                category = metadata.get('category', metadata.get('document_grade', 'General'))
                
                # Create snippet from content (first 250 characters)
                snippet = content[:250] + "..." if len(content) > 250 else content
                
                # Create knowledge base item
                kb_item = SearchKnowledgeBaseResponse(
                    id=kb_id,
                    title=title,
                    category=category,
                    snippet=snippet,
                    fullText=content
                )
                
                knowledge_base_items.append(kb_item)
                logger.debug(f"Created KB item {kb_id}: {title}")
                
            except Exception as e:
                logger.warning(f"Error processing chunk {i}: {str(e)}")
                continue
        
        logger.info(f"Successfully created {len(knowledge_base_items)} knowledge base items")
        logger.info("=== KNOWLEDGE BASE SEARCH COMPLETED ===")
        
        return knowledge_base_items
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}", exc_info=True)
        raise APIErrorHandler.internal_error(f"Error searching knowledge base: {str(e)}")