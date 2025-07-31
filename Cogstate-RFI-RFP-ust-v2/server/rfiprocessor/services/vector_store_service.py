import os
from typing import Any, List, Dict
from chromadb import PersistentClient
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma
from config import Config
from rfiprocessor.db.database import get_db_session
from rfiprocessor.db.db_models import Chunk
from rfiprocessor.utils.logger import get_logger
 
config = Config()
logger = get_logger(__name__)
 
# Define the path for the persistent ChromaDB store
CHROMA_PATH = config.CHROMA_PATH
COLLECTION_NAME = config.COLLECTION_NAME
 
class VectorStoreService:
    def __init__(self):
        """Initializes the VectorStoreService with OpenAI embeddings and ChromaDB."""
        # Validate OpenAI API key
        self.api_key = config.OPENAI_API_KEY
        self.embedding_model = config.EMBEDDING_MODEL
        if not self.api_key:
            logger.error("OPENAI_API_KEY not set in environment!")
            raise ValueError("Set your OPENAI_API_KEY in the environment!")
 
        self.client = PersistentClient(path=CHROMA_PATH)
        self.embedding_function = self._get_embedding_function()
        self.collection_name = COLLECTION_NAME
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=None  # LangChain's wrapper handles embeddings
        )
        
        self.langchain_chroma = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
        )
        logger.info(f"ChromaDB service initialized. Collection '{self.collection_name}' at {CHROMA_PATH}")
 
    def _get_embedding_function(self):
        """Initializes and returns the OpenAI embedding function."""
        logger.info(f"Loading OpenAI embedding model: {self.embedding_model}")
        return OpenAIEmbeddings(
            api_key=self.api_key,
            model=self.embedding_model
        )
 
    def add_documents(self, batch_size: int = 100) -> List[str]:
        """
        Loads chunks from the database and adds only NEW chunks to the Chroma vector store in batches.
        Checks for existing chunks first to avoid duplicates.
        Args:
            batch_size: Number of chunks to process per batch (default: 100).
        Returns:
            A list of vector IDs for the newly added documents.
        """
        logger.info("Loading chunks from database...")
        try:
            db_session_generator = get_db_session()
            db_session = next(db_session_generator)
            chunks = db_session.query(Chunk).all()
            logger.info(f"Loaded {len(chunks)} chunks from database.")
 
            if not chunks:
                logger.warning("No chunks found in database.")
                return []
 
            # Get existing vector IDs from ChromaDB to avoid duplicates
            existing_ids = set()
            try:
                # Get all existing IDs from the collection
                collection_data = self.collection.get()
                if collection_data and 'ids' in collection_data:
                    existing_ids = set(collection_data['ids'])
                    logger.info(f"Found {len(existing_ids)} existing chunks in vector store")
            except Exception as e:
                logger.warning(f"Could not retrieve existing IDs from vector store: {e}")
                # If we can't get existing IDs, we'll proceed and let ChromaDB handle duplicates
 
            # Filter out chunks that already exist in the vector store
            new_chunks = []
            for chunk in chunks:
                chunk_id = str(chunk.id)
                if chunk_id not in existing_ids:
                    new_chunks.append(chunk)
                else:
                    logger.debug(f"Chunk {chunk_id} already exists in vector store, skipping")
 
            if not new_chunks:
                logger.info("No new chunks to add to vector store")
                return []
 
            logger.info(f"Found {len(new_chunks)} new chunks to add out of {len(chunks)} total chunks")
 
            vector_ids = []
            for i in range(0, len(new_chunks), batch_size):
                batch = new_chunks[i:i + batch_size]
                documents = [
                    Document(
                        page_content=c.chunk_text,
                        metadata=c.chunk_metadata,
                        id=str(c.id)
                    ) for c in batch
                ]
                logger.info(f"Adding batch {i // batch_size + 1} ({len(documents)} new chunks)...")
                batch_ids = self.langchain_chroma.add_documents(documents)
                vector_ids.extend(batch_ids)
                logger.info(f"Added batch {i // batch_size + 1} ({len(documents)} new chunks)")
            
            logger.info(f"Successfully added {len(vector_ids)} new chunks to ChromaDB.")
            return vector_ids
 
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}", exc_info=True)
            raise
        finally:
            db_session.close()
 
    def get_retriever(self, search_kwargs={'k': 5}):
        """Returns a LangChain retriever for the vector store."""
        return self.langchain_chroma.as_retriever(search_type="mmr", search_kwargs=search_kwargs)
    
    def chunk_exists(self, chunk_id: str) -> bool:
        """
        Check if a chunk with the given ID already exists in the vector store.
        
        Args:
            chunk_id (str): The ID of the chunk to check.
            
        Returns:
            bool: True if the chunk exists, False otherwise.
        """
        try:
            # Try to get the chunk from the collection
            result = self.collection.get(ids=[chunk_id])
            return len(result['ids']) > 0 if result and 'ids' in result else False
        except Exception as e:
            logger.warning(f"Error checking if chunk {chunk_id} exists: {e}")
            return False
 
    def add_single_chunk(self, chunk_id: str, chunk_text: str, chunk_metadata: Dict[str, Any]) -> str:
        """
        Add a single chunk to the vector store if it doesn't already exist.
        
        Args:
            chunk_id (str): The ID of the chunk.
            chunk_text (str): The text content of the chunk.
            chunk_metadata (Dict[str, Any]): The metadata for the chunk.
            
        Returns:
            str: The vector ID of the added chunk, or empty string if already exists.
        """
        if self.chunk_exists(chunk_id):
            logger.debug(f"Chunk {chunk_id} already exists in vector store, skipping")
            return ""
        
        try:
            document = Document(
                page_content=chunk_text,
                metadata=chunk_metadata,
                id=chunk_id
            )
            vector_id = self.langchain_chroma.add_documents([document])
            logger.info(f"Added chunk {chunk_id} to vector store")
            return vector_id[0] if vector_id else ""
        except Exception as e:
            logger.error(f"Error adding chunk {chunk_id} to vector store: {e}")
            return ""
 
    def search_similar_chunks(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the vector store for the most similar chunks to a given query.
 
        Args:
            query (str): The question text to search for.
            k (int): The number of similar chunks to retrieve.
 
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary
                                  contains the chunk's content and metadata.
        """
        logger.info(f"Performing similarity search for query: '{query[:50]}...'")
        try:
            # Use the similarity_search method provided by the LangChain vector store wrapper
            results = self.langchain_chroma.similarity_search_with_score(query, k=k)
            
            # Format the results into a clean list
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            logger.info(f"Found {len(formatted_results)} relevant chunks for the query.")
            return formatted_results
 
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}", exc_info=True)
            return []
 
# Singleton instance
vector_store_service = VectorStoreService()