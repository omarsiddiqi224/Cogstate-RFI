# rfiprocessor/services/inference_pipeline.py

import os
from typing import Dict, Any

# --- Core Application Imports ---
from rfiprocessor.utils.logger import get_logger
from rfiprocessor.services.markdown_converter import MarkdownConverter
from rfiprocessor.core.agents.blank_rfi_parser import BlankRfiParserAgent
from rfiprocessor.core.agents.answer_generator import AnswerGeneratorAgent
from rfiprocessor.services.vector_store_service import VectorStoreService
from rfiprocessor.services.llm_provider import get_advanced_llm

# --- Database Imports ---
from rfiprocessor.db.database import get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import RfiDocument, RfiStatus

logger = get_logger(__name__)

def run_inference_for_rfi(rfi_doc_id: str, temp_file_path: str, user: str) -> None:
    """
    The main function that orchestrates the entire RAG inference pipeline for a new RFI.
    """
    logger.info(f"Inference pipeline started for RFI ID: {rfi_doc_id}")
    
    db_session_gen = get_db_session()
    db = next(db_session_gen)
    try:
        db_handler = DatabaseHandler(db)
        
        converter = MarkdownConverter()
        llm_instance = get_advanced_llm()
        blank_parser = BlankRfiParserAgent(llm=llm_instance)
        vector_handler = VectorStoreService()
        answer_generator = AnswerGeneratorAgent()

        md_content, _ = converter.convert_to_markdown(temp_file_path)
        parsed_json = blank_parser.parse(md_content)
        questions = parsed_json.get("questions", [])

        total_questions = len(questions)
        
        if not questions:
            raise ValueError("No questions were extracted from the document.")

        # Fetch the RFI document object once to work with it
        rfi_doc = db_handler.get_document_by_id(rfi_doc_id, model_class=RfiDocument)
        if not rfi_doc:
            raise ValueError(f"RfiDocument with ID {rfi_doc_id} not found in the database.")

        initial_payload = {
            "id": rfi_doc_id,
            "title": parsed_json.get("meta_data", {}).get("company_name", os.path.splitext(os.path.basename(temp_file_path))[0]),
            "fileName": os.path.basename(temp_file_path),
            "status": RfiStatus.IN_PROGRESS.value,
            "lastUpdated": rfi_doc.updated_at.isoformat(),
            "progress": 5,
            "questions": [{"id": i+1, "question": q.get("question"), "response": "", "status": "pending", "assignedTo": user, "knowledgeBase": []} for i, q in enumerate(questions)],
            "metaData": parsed_json.get("meta_data", {})
        }
        
        db_handler.update_record(rfi_doc_id, {"payload": initial_payload, "progress": 5, "updated_by_user": "system", "number_of_questions": total_questions }, model_class=RfiDocument)
        logger.info(f"[{rfi_doc_id}] Initial payload created with {len(questions)} questions.")

        total_questions = len(questions)
        for i, q_data in enumerate(initial_payload["questions"]):
            question_text = q_data["question"]
            logger.info(f"[{rfi_doc_id}] Processing question {i+1}/{total_questions}: '{question_text[:70]}...'")
            
            context_chunks = vector_handler.search_similar_chunks(question_text, k=5)
            draft_answer = answer_generator.generate_answer(question_text, context_chunks)
            
            # Modify the in-memory payload dictionary
            q_data["response"] = draft_answer
            q_data["status"] = "pending"
            q_data["knowledgeBase"] = [
                {"id": f"kb_{c['metadata'].get('source_document_id', 0)}_{j}", "title": c['metadata'].get('source_filename', 'Unknown'), "category": c['metadata'].get('document_grade', 'General'), "snippet": c['content'][:250] + "..."}
                for j, c in enumerate(context_chunks)
            ]
            
            progress = int(5 + ((i + 1) / total_questions) * 95)
            
            # This ensures the progressively filled payload is saved
            db_handler.update_record(rfi_doc_id, {"payload": initial_payload, "progress": progress, "updated_by_user": "system"}, model_class=RfiDocument)

        db_handler.update_record(rfi_doc_id, {"status": RfiStatus.REVIEW_READY, "progress": 100}, model_class=RfiDocument)
        logger.info(f"Successfully processed RFI ID: {rfi_doc_id}. Status set to REVIEW_READY.")

    except Exception as e:
        logger.error(f"Error running inference for RFI: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"Cleaned up temporary file: {temp_file_path}")