import sqlite3
import os
from typing import Dict, Any, Optional, List
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
        
        # 4. Flashcard Decks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        print("✅ Ensured table: decks")
        
        # 5. Flashcards
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id INTEGER NOT NULL,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                difficulty INTEGER DEFAULT 0,
                last_reviewed TEXT,
                next_review TEXT,
                repetition_count INTEGER DEFAULT 0,
                easiness_factor REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE
            )
        """)
        print("✅ Ensured table: cards")
        
        # 6. Study Sessions (day-by-day tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default_user',
                date TEXT NOT NULL,
                deck_id INTEGER NOT NULL,
                cards_studied INTEGER DEFAULT 0,
                total_time_seconds INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (deck_id) REFERENCES decks (id) ON DELETE CASCADE,
                UNIQUE(user_id, date, deck_id)
            )
        """)
        print("✅ Ensured table: study_sessions")
        
        # 7. Card Reviews (individual card study events)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                response_time_seconds REAL,
                difficulty_rating INTEGER,
                reviewed_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards (id) ON DELETE CASCADE
            )
        """)
        print("✅ Ensured table: card_reviews")
        
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

# Deck and Card Database Operations
def create_deck(name: str, description: str = "") -> Optional[int]:
    """Create a new deck and return its ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO decks (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, description, now, now)
            )
            deck_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Created deck: {name} (ID: {deck_id})")
            return deck_id
    except Exception as e:
        print(f"❌ Error creating deck: {e}")
        return None

def get_decks() -> List[Dict[str, Any]]:
    """Get all decks with their cards and next study dates"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all decks
            cursor.execute("SELECT * FROM decks ORDER BY created_at DESC")
            decks = [dict(row) for row in cursor.fetchall()]
            
            # Get cards for each deck and calculate next study date
            for deck in decks:
                cursor.execute("SELECT * FROM cards WHERE deck_id = ? ORDER BY created_at ASC", (deck['id'],))
                deck['cards'] = [dict(row) for row in cursor.fetchall()]
                
                # Find the most recent next_review date for this deck
                cursor.execute("""
                    SELECT next_review 
                    FROM cards 
                    WHERE deck_id = ? AND next_review IS NOT NULL 
                    ORDER BY next_review ASC 
                    LIMIT 1
                """, (deck['id'],))
                
                next_review_row = cursor.fetchone()
                if next_review_row:
                    deck['next_study_date'] = next_review_row['next_review']
                else:
                    # If no cards have next_review set, deck is ready to study
                    deck['next_study_date'] = None
            
            return decks
    except Exception as e:
        print(f"❌ Error getting decks: {e}")
        return []

def get_deck(deck_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific deck with its cards"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get deck
            cursor.execute("SELECT * FROM decks WHERE id = ?", (deck_id,))
            deck_row = cursor.fetchone()
            if not deck_row:
                return None
            
            deck = dict(deck_row)
            
            # Get cards for the deck
            cursor.execute("SELECT * FROM cards WHERE deck_id = ? ORDER BY created_at ASC", (deck_id,))
            deck['cards'] = [dict(row) for row in cursor.fetchall()]
            
            return deck
    except Exception as e:
        print(f"❌ Error getting deck {deck_id}: {e}")
        return None

def delete_deck(deck_id: int) -> bool:
    """Delete a deck and all its cards"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM decks WHERE id = ?", (deck_id,))
            conn.commit()
            print(f"✅ Deleted deck ID: {deck_id}")
            return True
    except Exception as e:
        print(f"❌ Error deleting deck {deck_id}: {e}")
        return False

def create_card(deck_id: int, front: str, back: str) -> Optional[int]:
    """Create a new card and return its ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """INSERT INTO cards 
                   (deck_id, front, back, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (deck_id, front, back, now, now)
            )
            card_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Created card in deck {deck_id} (ID: {card_id})")
            return card_id
    except Exception as e:
        print(f"❌ Error creating card: {e}")
        return None

def get_card(card_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific card"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cards WHERE id = ?", (card_id,))
            card_row = cursor.fetchone()
            return dict(card_row) if card_row else None
    except Exception as e:
        print(f"❌ Error getting card {card_id}: {e}")
        return None

def delete_card(card_id: int) -> bool:
    """Delete a card"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cards WHERE id = ?", (card_id,))
            conn.commit()
            print(f"✅ Deleted card ID: {card_id}")
            return True
    except Exception as e:
        print(f"❌ Error deleting card {card_id}: {e}")
        return False

def update_card_review_data(card_id: int, difficulty: int, repetition_count: int, 
                          easiness_factor: float, interval_days: int, next_review: str) -> bool:
    """Update card review data for spaced repetition"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """UPDATE cards SET 
                   difficulty = ?, repetition_count = ?, easiness_factor = ?, 
                   interval_days = ?, last_reviewed = ?, next_review = ?, updated_at = ?
                   WHERE id = ?""",
                (difficulty, repetition_count, easiness_factor, interval_days, now, next_review, now, card_id)
            )
            conn.commit()
            print(f"✅ Updated card {card_id} review data")
            return True
    except Exception as e:
        print(f"❌ Error updating card {card_id} review data: {e}")
        return False

# Study Session Tracking Functions
def get_or_create_study_session(deck_id: int, user_id: str = "default_user") -> Optional[int]:
    """Get or create a study session for today and the given deck"""
    try:
        today = time.strftime("%Y-%m-%d")
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Try to get existing session for today
            cursor.execute(
                "SELECT id FROM study_sessions WHERE user_id = ? AND date = ? AND deck_id = ?",
                (user_id, today, deck_id)
            )
            session_row = cursor.fetchone()
            
            if session_row:
                session_id = session_row['id']
                print(f"📚 Found existing study session: {session_id}")
                return session_id
            
            # Create new session for today
            cursor.execute(
                """INSERT INTO study_sessions 
                   (user_id, date, deck_id, cards_studied, total_time_seconds, created_at, updated_at)
                   VALUES (?, ?, ?, 0, 0, ?, ?)""",
                (user_id, today, deck_id, now, now)
            )
            session_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Created new study session: {session_id} for deck {deck_id}")
            return session_id
            
    except Exception as e:
        print(f"❌ Error getting/creating study session: {e}")
        return None

def record_card_review(session_id: int, card_id: int, response_time_seconds: Optional[float] = None, 
                      difficulty_rating: Optional[int] = None) -> bool:
    """Record that a card was reviewed in a study session"""
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Insert card review record
            cursor.execute(
                """INSERT INTO card_reviews 
                   (session_id, card_id, response_time_seconds, difficulty_rating, reviewed_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, card_id, response_time_seconds, difficulty_rating, now)
            )
            
            # Update study session counts
            cursor.execute(
                """UPDATE study_sessions SET 
                   cards_studied = cards_studied + 1,
                   total_time_seconds = total_time_seconds + ?,
                   updated_at = ?
                   WHERE id = ?""",
                (response_time_seconds or 0, now, session_id)
            )
            
            # Update card last_reviewed
            cursor.execute(
                "UPDATE cards SET last_reviewed = ?, updated_at = ? WHERE id = ?",
                (now, now, card_id)
            )
            
            conn.commit()
            print(f"✅ Recorded card review: session={session_id}, card={card_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error recording card review: {e}")
        return False

def get_daily_study_stats(date: Optional[str] = None, user_id: str = "default_user") -> Dict[str, Any]:
    """Get study statistics for a specific date (defaults to today)"""
    try:
        if not date:
            date = time.strftime("%Y-%m-%d")
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get total cards studied today
            cursor.execute(
                "SELECT COALESCE(SUM(cards_studied), 0) as total_cards FROM study_sessions WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            total_cards = cursor.fetchone()['total_cards']
            
            # Get total time studied today
            cursor.execute(
                "SELECT COALESCE(SUM(total_time_seconds), 0) as total_time FROM study_sessions WHERE user_id = ? AND date = ?",
                (user_id, date)
            )
            total_time = cursor.fetchone()['total_time']
            
            # Get deck-wise breakdown
            cursor.execute(
                """SELECT d.name as deck_name, s.cards_studied, s.total_time_seconds
                   FROM study_sessions s
                   JOIN decks d ON s.deck_id = d.id
                   WHERE s.user_id = ? AND s.date = ?
                   ORDER BY s.cards_studied DESC""",
                (user_id, date)
            )
            deck_breakdown = [dict(row) for row in cursor.fetchall()]
            
            return {
                "date": date,
                "total_cards_studied": total_cards,
                "total_time_seconds": total_time,
                "deck_breakdown": deck_breakdown
            }
            
    except Exception as e:
        print(f"❌ Error getting daily study stats: {e}")
        return {
            "date": date or time.strftime("%Y-%m-%d"),
            "total_cards_studied": 0,
            "total_time_seconds": 0,
            "deck_breakdown": []
        }

def get_study_history(days: int = 7, user_id: str = "default_user") -> List[Dict[str, Any]]:
    """Get study history for the last N days"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT date, SUM(cards_studied) as total_cards, SUM(total_time_seconds) as total_time
                   FROM study_sessions 
                   WHERE user_id = ? AND date >= date('now', '-{} days')
                   GROUP BY date
                   ORDER BY date DESC""".format(days),
                (user_id,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
            
    except Exception as e:
        print(f"❌ Error getting study history: {e}")
        return []

# Initialize sample data if database is empty
def init_sample_data():
    """Initialize sample data if no decks exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM decks")
            deck_count = cursor.fetchone()['count']
            
            if deck_count == 0:
                print("📚 Initializing sample deck data...")
                
                # Create sample deck
                deck_id = create_deck("Spanish Vocabulary", "Basic Spanish words")
                
                if deck_id:
                    # Create sample cards
                    sample_cards = [
                        ("Hello", "Hola"),
                        ("Goodbye", "Adiós"),
                        ("Thank you", "Gracias"),
                        ("Please", "Por favor"),
                        ("Water", "Agua"),
                        ("Food", "Comida")
                    ]
                    
                    for front, back in sample_cards:
                        create_card(deck_id, front, back)
                
                print("✅ Sample data initialized")
    except Exception as e:
        print(f"❌ Error initializing sample data: {e}")

# Initialize database on import only if run directly
if __name__ == "__main__":
    init_database()
    init_sample_data()