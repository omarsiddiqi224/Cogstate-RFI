import os
import asyncio
import logging
from typing import List, Dict, Any
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
TOP_K = 5  # Number of similar chunks to retrieve
LLM_MODEL = "gpt-4o"
BATCH_SIZE = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blank_rfi_rag_pipeline")

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
    return questions, parsed

# --- 2a. Paraphrase and deduplicate questions ---
async def async_paraphrase_questions(questions: List[str], model: str = LLM_MODEL) -> List[str]:
    import openai
    openai.api_key = OPENAI_API_KEY
    prompts = [f"Paraphrase this question in 2-3 different ways, separated by newlines:\n{q}" for q in questions]
    sem = asyncio.Semaphore(5)
    async def call_llm(prompt):
        async with sem:
            try:
                response = await openai.AsyncOpenAI().chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content.strip()
                return [qq.strip() for qq in content.split('\n') if qq.strip()]
            except Exception as e:
                logger.error(f"Paraphrase LLM call failed: {e}")
                return []
    results = await asyncio.gather(*(call_llm(p) for p in prompts))
    # Flatten and deduplicate
    all_questions = set()
    for orig, para_list in zip(questions, results):
        all_questions.add(orig)
        all_questions.update(para_list)
    return list(all_questions)

def deduplicate_questions(questions: List[str]) -> List[str]:
    seen = set()
    deduped = []
    for q in questions:
        norm = q.strip().lower()
        if norm not in seen:
            seen.add(norm)
            deduped.append(q)
    return deduped

# --- 3. Setup ChromaDB and embedding function ---
def get_chroma_collection():
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-3-large"
    )
    client = PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME, embedding_function=openai_ef)
    return collection

# --- 4. Batch embed and retrieve ---
def batch_retrieve(collection, questions: List[str], top_k: int = TOP_K) -> List[List[str]]:
    results = collection.query(query_texts=questions, n_results=top_k)
    # results['documents'] is a list of lists (one per question)
    return results['documents']

# --- 5. Rerank using OpenAI LLM ---
async def async_rerank(question: str, chunks: List[str], model: str = LLM_MODEL) -> List[str]:
    openai.api_key = OPENAI_API_KEY
    prompts = [
        f"Question: {question}\nChunk: {chunk}\nHow relevant is this chunk to the question? Reply with a number from 1 (not relevant) to 5 (highly relevant)."
        for chunk in chunks
    ]
    sem = asyncio.Semaphore(5)
    scores = [0] * len(prompts)
    async def call_llm(idx, prompt):
        async with sem:
            try:
                response = await openai.AsyncOpenAI().chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = response.choices[0].message.content.strip()
                # Extract the first number from the response
                import re
                match = re.search(r"[1-5]", content)
                score = int(match.group(0)) if match else 1
                scores[idx] = score
            except Exception as e:
                logger.error(f"Rerank LLM call failed for chunk {idx}: {e}")
                scores[idx] = 1
    await asyncio.gather(*(call_llm(i, p) for i, p in enumerate(prompts)))
    # Sort chunks by score descending, return top-k
    chunk_score_pairs = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    reranked_chunks = [c for c, s in chunk_score_pairs][:TOP_K]
    return reranked_chunks

# --- 6. Async batch LLM generation ---
async def async_llm_generate(prompts: List[str], model: str = LLM_MODEL) -> List[str]:
    import openai
    openai.api_key = OPENAI_API_KEY
    results = [None] * len(prompts)
    sem = asyncio.Semaphore(5)  # Limit concurrency
    async def call_llm(idx, prompt):
        async with sem:
            try:
                response = await openai.AsyncOpenAI().chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                results[idx] = response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"LLM call failed for prompt {idx}: {e}")
                results[idx] = "[LLM call failed]"
    await asyncio.gather(*(call_llm(i, p) for i, p in enumerate(prompts)))
    return results

# --- 7. Main pipeline function ---
def build_prompts(questions: List[str], contexts: List[List[str]]) -> List[str]:
    prompts = []
    for q, ctxs in zip(questions, contexts):
        context = "\n\n".join(ctxs)
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {q}\n"
            f"Answer:"
        )
        prompts.append(prompt)
    return prompts

def rerank_all(questions: List[str], retrieved: List[List[str]]) -> List[List[str]]:
    # Rerank all questions' retrieved chunks in parallel
    async def batch_rerank():
        tasks = [async_rerank(q, ctxs) for q, ctxs in zip(questions, retrieved)]
        return await asyncio.gather(*tasks)
    return asyncio.run(batch_rerank())

def rag_pipeline(file_path: str) -> Dict[str, Any]:
    logger.info(f"Converting {file_path} to markdown...")
    markdown_content = convert_to_markdown(file_path)
    logger.info("Parsing questions...")
    questions, parsed = extract_questions(markdown_content)
    logger.info(f"Extracted {len(questions)} questions.")
    # Paraphrase and deduplicate questions
    questions = asyncio.run(async_paraphrase_questions(questions, model=LLM_MODEL))
    questions = deduplicate_questions(questions)
    logger.info(f"After paraphrasing and deduplication: {len(questions)} unique questions.")
    if not questions:
        return {"questions": [], "parsed": parsed}
    logger.info("Retrieving similar chunks from vector DB...")
    collection = get_chroma_collection()
    retrieved = batch_retrieve(collection, questions, top_k=TOP_K)
    logger.info("Reranking retrieved chunks with LLM...")
    reranked_contexts = rerank_all(questions, retrieved)
    logger.info("Building prompts for LLM...")
    prompts = build_prompts(questions, reranked_contexts)
    logger.info("Generating answers with LLM (async batch)...")
    answers = asyncio.run(async_llm_generate(prompts, model=LLM_MODEL))
    filled = [{"question": q, "answer": a, "context": c} for q, a, c in zip(questions, answers, ["\n\n".join(ctxs) for ctxs in reranked_contexts])]
    return {"questions": filled, "parsed": parsed}

# --- CLI usage ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Blank RFI RAG Pipeline")
    parser.add_argument("file", help="Path to blank RFI file (PDF, DOCX, XLSX, etc.)")
    parser.add_argument("--output", help="Path to save filled RFI as JSON", default=None)
    args = parser.parse_args()
    result = rag_pipeline(args.file)
    for qa in result["questions"]:
        print(f"\nQ: {qa['question']}\nA: {qa['answer']}\n---\nContext used:\n{qa['context'][:500]}...\n")
    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(result["questions"], f, indent=2)
        print(f"Filled RFI saved to {args.output}") 