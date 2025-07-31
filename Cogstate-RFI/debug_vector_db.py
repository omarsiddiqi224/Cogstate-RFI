import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from config import Config

def debug_vector_database():
    """Debug vector database connection and find the correct collection."""
    
    config = Config()
    
    print(f"Config VECTOR_DB_PATH: {config.VECTOR_DB_PATH}")
    print(f"Actual folder exists: {os.path.exists(config.VECTOR_DB_PATH)}")
    
    # Check the actual path you showed in the image
    actual_path = "data/vector_store/chroma_db"
    print(f"\nActual path '{actual_path}' exists: {os.path.exists(actual_path)}")
    
    # List contents of the vector store directory
    if os.path.exists(actual_path):
        print(f"\nContents of {actual_path}:")
        for item in os.listdir(actual_path):
            item_path = os.path.join(actual_path, item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                # List contents of subdirectories
                for subitem in os.listdir(item_path):
                    print(f"    📄 {subitem}")
            else:
                print(f"  📄 {item}")
    
    # Try connecting to the actual path
    print(f"\n" + "="*50)
    print("TRYING ACTUAL PATH:")
    try:
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY,
            model_name="text-embedding-3-large"
        )
        
        client = PersistentClient(path=actual_path)
        collections = client.list_collections()
        
        print(f"Found {len(collections)} collections:")
        for collection in collections:
            print(f"  - {collection.name}")
            
            # Get collection and check count
            coll = client.get_collection(collection.name, embedding_function=openai_ef)
            count = coll.count()
            print(f"    Documents: {count}")
            
            if count > 0:
                # Show sample
                try:
                    results = coll.peek(limit=2)
                    print(f"    Sample documents:")
                    for i, doc in enumerate(results['documents']):
                        print(f"      {i+1}. {doc[:100]}...")
                        if results['metadatas'] and results['metadatas'][i]:
                            print(f"         Metadata: {results['metadatas'][i]}")
                except Exception as e:
                    print(f"    Error getting samples: {e}")
            print()
    
    except Exception as e:
        print(f"Error accessing actual path: {e}")
    
    # Try connecting to config path
    print(f"\n" + "="*50)
    print("TRYING CONFIG PATH:")
    try:
        client_config = PersistentClient(path=config.VECTOR_DB_PATH)
        collections_config = client_config.list_collections()
        
        print(f"Found {len(collections_config)} collections in config path:")
        for collection in collections_config:
            print(f"  - {collection.name}")
            
    except Exception as e:
        print(f"Error accessing config path: {e}")

def fix_config_path():
    """Update the config to point to the correct path."""
    
    config_file = "config.py"
    
    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Show current vector DB path setting
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'VECTOR_DB_PATH' in line and not line.strip().startswith('#'):
            print(f"Current setting (line {i+1}): {line.strip()}")
    
    print("\nTo fix this, update your config.py file:")
    print('VECTOR_DB_PATH = "data/vector_store/chroma_db"')

if __name__ == "__main__":
    debug_vector_database()
    print("\n" + "="*50)
    fix_config_path()