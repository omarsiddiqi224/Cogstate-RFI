from rfiprocessor.db.database import get_db_session
from rfiprocessor.services.db_handler import DatabaseHandler
from rfiprocessor.db.db_models import IngestionStatus, Document

def reset_all_documents_to_pending():
    db_session_generator = get_db_session()
    db_session = next(db_session_generator)
    try:
        db_handler = DatabaseHandler(db_session)
        docs = db_session.query(Document).all()  # <-- Updated line
        for doc in docs:
            db_handler.update_document(doc.id, {
                "ingestion_status": IngestionStatus.PENDING,
                "error_message": None
            })
        print(f"Reset {len(docs)} documents to PENDING.")
    finally:
        db_session.close()

if __name__ == "__main__":
    reset_all_documents_to_pending()