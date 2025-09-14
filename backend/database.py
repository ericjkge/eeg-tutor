import sqlite3
import os
from typing import Dict, Any, Optional
import time
from contextlib import contextmanager

DATABASE_PATH = "synapse.db"

def init_database():
    """Initialize the synapse database with required tables"""
    db_abs = os.path.abspath(DATABASE_PATH)
    print(f"🗄️ Initializing database at: {db_abs}")
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # 1. Calibration Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                started_at TEXT NOT NULL,
                completed_at TEXT,
                total_questions INTEGER,
                correct_answers INTEGER
            )
        """)
        print("✅ Ensured table: calibration_sessions")
        
        # 2. Calibration Responses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                test_id TEXT NOT NULL,
                question TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                selected_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                response_time_ms INTEGER NOT NULL,
                question_shown_at TEXT NOT NULL,
                answered_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES calibration_sessions (id)
            )
        """)
        print("✅ Ensured table: calibration_responses")
        
        # 3. EEG Samples (averaged snapshot data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eeg_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                tp9 REAL,
                af7 REAL,
                af8 REAL,
                tp10 REAL,
                samples_averaged INTEGER DEFAULT 1,
                created_at REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES calibration_sessions (id)
            )
        """)
        print("✅ Ensured table: eeg_samples")
        
        conn.commit()
        print("🎉 Database initialization complete")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
    finally:
        conn.close()

def save_eeg_sample(session_id: str, question_id: str, sample: Dict[str, Any]) -> bool:
    """Save a single EEG sample (latest point)."""
    try:
        if not sample:
            print("⚠️ save_eeg_sample called with empty sample")
            return False
        samples_count = sample.get('samples_averaged', 1)
        print(f"🧪 Attempting to save EEG snapshot: session={session_id} question={question_id} ts={sample.get('timestamp')} tp9={sample.get('tp9'):.3f} af7={sample.get('af7'):.3f} af8={sample.get('af8'):.3f} tp10={sample.get('tp10'):.3f} (avg of {samples_count} samples)")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO eeg_samples (session_id, question_id, timestamp, tp9, af7, af8, tp10, samples_averaged, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(session_id),
                question_id,
                float(sample.get('timestamp') or sample.get('ts') or 0.0),
                float(sample.get('tp9') or 0.0),
                float(sample.get('af7') or 0.0),
                float(sample.get('af8') or 0.0),
                float(sample.get('tp10') or 0.0),
                int(samples_count),
                time.time()
            ))
            conn.commit()
            print("✅ Saved EEG snapshot row")
            return True
    except Exception as e:
        print(f"❌ Error saving EEG sample: {e}")
        return False

# Initialize database on import only if run directly
if __name__ == "__main__":
    init_database()