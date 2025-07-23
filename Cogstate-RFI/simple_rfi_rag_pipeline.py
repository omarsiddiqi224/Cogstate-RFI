import os
from rfiprocessor.services.markdown_converter import MarkdownConverter, ProcessorType
from rfiprocessor.core.agents.blank_rfi_parser import BlankRfiParserAgent
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
import openai

# --- CONFIG ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "Set your OPENAI_API_KEY in the environment!"
VECTOR_DB_PATH = "data/vector_store/chroma_db"
COLLECTION_NAME = "chunks"
TOP_K = 5
LLM_MODEL = "gpt-4o"

# --- 1. Convert file to markdown ---
def convert_to_markdown(file_path: str) -> str:
    converter = MarkdownConverter()
    ext = os.path.splitext(file_path)[1].lower()
    processor = ProcessorType.UNSTRUCTURED if ext in [".xls", ".xlsx", ".doc", ".docm"] else ProcessorType.MARKITDOWN
    markdown_content, _ = converter.convert_to_markdown(file_path, processor=processor)
    return markdown_content

# --- 2. Parse questions from markdown ---
def extract_questions(markdown_content: str):
    parser = BlankRfiParserAgent()
    parsed = parser.parse(markdown_content)
    questions = [q["question"] for q in parsed.get("questions", [])]
    return questions

# --- 3. Setup ChromaDB and embedding function ---
def get_chroma_collection():
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-large"
    )
    client = PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=openai_ef)
    return collection

# --- 4. Retrieve similar chunks ---
def retrieve_context(collection, question, top_k=TOP_K):
    results = collection.query(query_texts=[question], n_results=top_k)
    return results['documents'][0]

# --- 5. Generate answer with LLM ---
def generate_answer(question, context, model=LLM_MODEL):
    openai.api_key = OPENAI_API_KEY
    context_str = "\n\n".join(context)
    prompt = f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        api_key=OPENAI_API_KEY
    )
    return response.choices[0].message.content.strip()

# --- 6. Main pipeline ---
def simple_rag_pipeline_from_file(file_path):
    markdown_content = convert_to_markdown(file_path)
    questions = extract_questions(markdown_content)
    collection = get_chroma_collection()
    for question in questions:
        context = retrieve_context(collection, question)
        answer = generate_answer(question, context)
        print(f"Q: {question}\nA: {answer}\n---\nContext used:\n{''.join(context)[:500]}...\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simple RFI RAG Pipeline from File")
    parser.add_argument("file", help="Path to blank RFI file (PDF, DOCX, XLSX, etc.)")
    args = parser.parse_args()
    simple_rag_pipeline_from_file(args.file) 