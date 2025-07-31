from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from config import Config

def check_vector_database():
    """Check if the vector database has any data."""
    
    config = Config()
    
    # Initialize ChromaDB
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=config.OPENAI_API_KEY,
        model_name="text-embedding-3-large"
    )
    
    client = PersistentClient(path=config.VECTOR_DB_PATH)
    
    try:
        collection = client.get_collection(
            name="rfi_chunks",  # This should match your collection name
            embedding_function=openai_ef
        )
        
        # Get collection info
        count = collection.count()
        print(f"Collection 'rfi_chunks' found with {count} documents")
        
        if count > 0:
            # Get a few sample documents
            results = collection.peek(limit=5)
            print(f"\nSample documents:")
            for i, doc in enumerate(results['documents']):
                print(f"{i+1}. {doc[:200]}...")
                if results['metadatas'][i]:
                    print(f"   Metadata: {results['metadatas'][i]}")
                print()
        else:
            print("Collection is empty - no documents indexed!")
            
    except Exception as e:
        print(f"Error accessing collection: {e}")
        print("Collection might not exist or have a different name")
        
        # List all collections
        collections = client.list_collections()
        print(f"\nAvailable collections: {[c.name for c in collections]}")

if __name__ == "__main__":
    check_vector_database()