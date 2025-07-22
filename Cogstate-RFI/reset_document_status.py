import sqlite3
import os

# Path to your SQLite database
DB_PATH = os.path.join('data', 'db', 'rfi_processor.db')

RESET_STATUSES = ['FAILED', 'CLASSIFIED', 'PARSED']  # You can modify this list as needed


def reset_statuses(db_path, statuses=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        if statuses:
            placeholders = ','.join('?' for _ in statuses)
            sql = f"""
                UPDATE documents
                SET ingestion_status = 'PENDING', error_message = NULL
                WHERE ingestion_status IN ({placeholders})
            """
            cursor.execute(sql, statuses)
        else:
            sql = "UPDATE documents SET ingestion_status = 'PENDING', error_message = NULL"
            cursor.execute(sql)
        conn.commit()
        print(f"Reset statuses to PENDING for documents with statuses: {statuses if statuses else 'ALL'}.")
    except Exception as e:
        print(f"Error resetting statuses: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # To reset only certain statuses, pass RESET_STATUSES; to reset all, pass None
    reset_statuses(DB_PATH, RESET_STATUSES) 