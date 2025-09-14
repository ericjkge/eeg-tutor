from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from eeg_service import eeg_service
from database import (
    get_db_connection, save_eeg_sample, init_database, init_sample_data,
    create_deck, get_decks, get_deck, delete_deck,
    create_card, get_card, delete_card, update_card_review_data,
    get_or_create_study_session, record_card_review, get_daily_study_stats, get_study_history
)
from ml_service import cognitive_load_predictor
import uuid
import time

app = FastAPI(title="Synapse API")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Card(BaseModel):
    id: int
    front: str
    back: str
    deck_id: int
    difficulty: Optional[int] = 0
    last_reviewed: Optional[str] = None
    next_review: Optional[str] = None

class Deck(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    cards: List[Card] = []

class CreateCard(BaseModel):
    front: str
    back: str
    deck_id: int

class CreateDeck(BaseModel):
    name: str
    description: Optional[str] = ""

class CardReview(BaseModel):
    card_id: int
    deck_id: int
    response_time_seconds: Optional[float] = None
    difficulty_rating: Optional[int] = None

# Initialize database and sample data
init_database()
init_sample_data()

# API Routes
@app.get("/")
async def root():
    return {"message": "Synapse API is running"}

@app.get("/decks", response_model=List[Deck])
async def get_decks_endpoint():
    """Get all decks with their cards"""
    try:
        decks_data = get_decks()
        result = []
        for deck_data in decks_data:
            # Convert to Pydantic model
            deck = Deck(**deck_data)
            # Cards are already included in deck_data from database function
            result.append(deck)
        return result
    except Exception as e:
        print(f"❌ Error in get_decks endpoint: {e}")
        return []

@app.get("/decks/{deck_id}", response_model=Deck)
async def get_deck_endpoint(deck_id: int):
    """Get a specific deck with its cards"""
    try:
        deck_data = get_deck(deck_id)
        if not deck_data:
            return {"error": "Deck not found"}
        
        return Deck(**deck_data)
    except Exception as e:
        print(f"❌ Error in get_deck endpoint: {e}")
        return {"error": "Failed to get deck"}

@app.post("/decks", response_model=Deck)
async def create_deck_endpoint(deck: CreateDeck):
    """Create a new deck"""
    try:
        deck_id = create_deck(deck.name, deck.description)
        if not deck_id:
            return {"error": "Failed to create deck"}
        
        # Get the created deck with empty cards list
        new_deck = Deck(
            id=deck_id,
            name=deck.name,
            description=deck.description,
            cards=[]
        )
        return new_deck
    except Exception as e:
        print(f"❌ Error in create_deck endpoint: {e}")
        return {"error": "Failed to create deck"}

@app.post("/cards", response_model=Card)
async def create_card_endpoint(card: CreateCard):
    """Create a new card"""
    try:
        card_id = create_card(card.deck_id, card.front, card.back)
        if not card_id:
            return {"error": "Failed to create card"}
        
        # Get the created card
        card_data = get_card(card_id)
        if not card_data:
            return {"error": "Failed to retrieve created card"}
        
        return Card(**card_data)
    except Exception as e:
        print(f"❌ Error in create_card endpoint: {e}")
        return {"error": "Failed to create card"}

@app.get("/cards/{card_id}", response_model=Card)
async def get_card_endpoint(card_id: int):
    """Get a specific card"""
    try:
        card_data = get_card(card_id)
        if not card_data:
            return {"error": "Card not found"}
        return Card(**card_data)
    except Exception as e:
        print(f"❌ Error in get_card endpoint: {e}")
        return {"error": "Failed to get card"}

@app.delete("/cards/{card_id}")
async def delete_card_endpoint(card_id: int):
    """Delete a card"""
    try:
        success = delete_card(card_id)
        if success:
            return {"message": "Card deleted"}
        else:
            return {"error": "Failed to delete card"}
    except Exception as e:
        print(f"❌ Error in delete_card endpoint: {e}")
        return {"error": "Failed to delete card"}

@app.delete("/decks/{deck_id}")
async def delete_deck_endpoint(deck_id: int):
    """Delete a deck and all its cards"""
    try:
        success = delete_deck(deck_id)
        if success:
            return {"message": "Deck deleted"}
        else:
            return {"error": "Failed to delete deck"}
    except Exception as e:
        print(f"❌ Error in delete_deck endpoint: {e}")
        return {"error": "Failed to delete deck"}

# Study Session Tracking Endpoints
@app.post("/study/start")
async def start_study_session(deck_id: int):
    """Start or get existing study session for a deck"""
    try:
        session_id = get_or_create_study_session(deck_id)
        if session_id:
            return {
                "success": True,
                "session_id": session_id,
                "message": "Study session ready"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create study session"
            }
    except Exception as e:
        print(f"❌ Error starting study session: {e}")
        return {
            "success": False,
            "error": "Failed to start study session"
        }

@app.post("/study/review")
async def record_review(review: CardReview):
    """Record that a card was reviewed"""
    try:
        # Get or create study session for the deck
        session_id = get_or_create_study_session(review.deck_id)
        if not session_id:
            return {
                "success": False,
                "error": "Failed to get study session"
            }
        
        # Record the card review
        success = record_card_review(
            session_id, 
            review.card_id, 
            review.response_time_seconds, 
            review.difficulty_rating
        )
        
        if success:
            return {
                "success": True,
                "message": "Card review recorded"
            }
        else:
            return {
                "success": False,
                "error": "Failed to record card review"
            }
            
    except Exception as e:
        print(f"❌ Error recording card review: {e}")
        return {
            "success": False,
            "error": "Failed to record card review"
        }

@app.get("/study/stats")
async def get_study_stats(date: Optional[str] = None):
    """Get study statistics for a date (defaults to today)"""
    try:
        stats = get_daily_study_stats(date)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        print(f"❌ Error getting study stats: {e}")
        return {
            "success": False,
            "error": "Failed to get study stats"
        }

@app.get("/study/history")
async def get_study_history_endpoint(days: int = 7):
    """Get study history for the last N days"""
    try:
        history = get_study_history(days)
        return {
            "success": True,
            "history": history
        }
    except Exception as e:
        print(f"❌ Error getting study history: {e}")
        return {
            "success": False,
            "error": "Failed to get study history"
        }

# Calibration Endpoints
@app.get("/calibration/tests")
async def get_calibration_tests():
    """Get calibration test questions from backend/tests.txt"""
    try:
        tests_path = os.path.join(os.path.dirname(__file__), "tests.txt")
        with open(tests_path, "r") as f:
            raw = f.read()
        source_tests = json.loads(raw)
        difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
        tests = [
            {
                "id": t.get("id"),
                "question": t.get("question"),
                "choices": t.get("choices", []),
                "answer": t.get("answer"),
                "difficulty": difficulty_map.get(str(t.get("difficulty")).lower(), 2)
            }
            for t in source_tests
            if t
        ]
        return {"tests": tests}
    except Exception as e:
        return {"tests": [], "error": str(e)}

@app.post("/calibration/start")
async def start_calibration_session():
    """Start a new calibration session (legacy schema compatible)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            print("📥 Creating calibration session (legacy schema)")
            cursor.execute(
                "INSERT INTO calibration_sessions (user_id, started_at) VALUES (?, ?)",
                ("default_user", time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            session_id = cursor.lastrowid
            conn.commit()
            print(f"✅ Calibration session created: {session_id}")
        return {"success": True, "session_id": session_id, "message": "Calibration session started"}
    except Exception as e:
        print(f"❌ Failed to create calibration session: {e}")
        return {"success": False, "error": str(e)}

class CalibrationAnswer(BaseModel):
    session_id: int
    testId: str
    question: str
    difficulty: int
    selectedAnswer: str
    correctAnswer: str
    isCorrect: bool
    timestamp: float
    timeSpent: int

@app.post("/calibration/answer")
async def save_calibration_answer(answer: CalibrationAnswer):
    """Save a single calibration answer (legacy schema compatible)"""
    try:
        # Map numeric difficulty back to label expected by legacy schema
        diff_map = {1: "easy", 2: "medium", 3: "hard"}
        try:
            diff_label = diff_map.get(int(answer.difficulty), str(answer.difficulty))
        except Exception:
            diff_label = str(answer.difficulty)
        # Convert timestamps (ms from frontend) to DATETIME strings
        answered_at_ts = float(answer.timestamp) / 1000.0
        shown_at_ts = max(0.0, answered_at_ts - (float(answer.timeSpent) / 1000.0))
        answered_at_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answered_at_ts))
        shown_at_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(shown_at_ts))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            print(
                f"📥 Saving answer: session={answer.session_id} test={answer.testId} diff={diff_label} correct={answer.isCorrect} time_spent_ms={answer.timeSpent}"
            )
            cursor.execute(
                """
                INSERT INTO calibration_responses 
                (session_id, test_id, question, difficulty, selected_answer, 
                 correct_answer, is_correct, response_time_ms, question_shown_at, answered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    answer.session_id,
                    answer.testId,
                    answer.question,
                    diff_label,
                    answer.selectedAnswer,
                    answer.correctAnswer,
                    bool(answer.isCorrect),
                    int(answer.timeSpent),
                    shown_at_str,
                    answered_at_str,
                ),
            )
            conn.commit()
            print("✅ Saved calibration answer row")

        return {"success": True, "message": "Answer saved successfully"}
    except Exception as e:
        print(f"❌ Failed to save calibration answer: {e}")
        return {"success": False, "error": str(e)}

class CalibrationSubmission(BaseModel):
    responses: List[dict]
    sessionData: dict

@app.post("/calibration/submit")
async def submit_calibration_data(submission: CalibrationSubmission):
    """Submit all calibration data (legacy endpoint)"""
    return {
        "success": True,
        "message": "Calibration data submitted successfully"
    }

@app.post("/calibration/complete")
async def complete_calibration_session(session_id: int):
    """Complete a calibration session (legacy schema compatible)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            print(f"📥 Completing session: {session_id}")
            cursor.execute(
                "UPDATE calibration_sessions SET completed_at = ? WHERE id = ?",
                (time.strftime("%Y-%m-%d %H:%M:%S"), session_id),
            )
            conn.commit()
            print("✅ Session marked completed")
        return {"success": True, "message": "Calibration session completed"}
    except Exception as e:
        print(f"❌ Failed to complete session: {e}")
        return {"success": False, "error": str(e)}

# EEG Connection Endpoints
@app.get("/eeg/status")
async def get_eeg_status():
    """Get EEG device connection status"""
    return eeg_service.get_connection_status()

@app.get("/eeg/data")
async def get_eeg_data(seconds: float = 1.0):
    """Get live EEG data from the last N seconds"""
    return {
        "data": eeg_service.get_live_data(seconds),
        "status": eeg_service.get_connection_status()
    }

@app.get("/eeg/fft")
async def get_eeg_fft(window_seconds: float = 1.0):
    """Get FFT-processed EEG data for frequency visualization"""
    return eeg_service.get_fft_data(window_seconds)

@app.post("/eeg/start")
async def start_eeg_service():
    """Start the EEG OSC server"""
    success = eeg_service.start_server()
    return {
        "success": success,
        "message": "EEG service started" if success else "Failed to start EEG service",
        "status": eeg_service.get_connection_status()
    }

@app.post("/eeg/stop")
async def stop_eeg_service():
    """Stop the EEG OSC server"""
    eeg_service.stop_server()
    return {
        "success": True,
        "message": "EEG service stopped",
        "status": eeg_service.get_connection_status()
    }

@app.post("/eeg/snapshot")
async def save_eeg_snapshot(session_id: int, question_id: str):
    """Save the most recent EEG sample for the given session/question"""
    sample = eeg_service.get_latest_sample()
    print(f"📸 Snapshot request: session={session_id} question={question_id} has_sample={bool(sample)}")
    if not sample:
        return {"success": False, "message": "No EEG data available"}
    ok = save_eeg_sample(str(session_id), question_id, sample)
    print(f"{'✅' if ok else '❌'} Snapshot save {'ok' if ok else 'failed'}")
    return {"success": ok, "message": "Saved" if ok else "Failed to save"}

# ML Model Endpoints
@app.get("/ml/status")
async def get_ml_model_status():
    """Get ML model status and information"""
    try:
        info = cognitive_load_predictor.get_model_info()
        return {
            "success": True,
            "model_info": clean_metrics_for_json(info)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/ml/training-data")
async def get_training_data_preview():
    """Get a preview of available training data"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get calibration session count
            cursor.execute("SELECT COUNT(*) as count FROM calibration_sessions")
            session_count = cursor.fetchone()['count']
            
            # Get response count by difficulty
            cursor.execute("""
                SELECT difficulty, COUNT(*) as count 
                FROM calibration_responses 
                GROUP BY difficulty
            """)
            difficulty_counts = {row['difficulty']: row['count'] for row in cursor.fetchall()}
            
            # Get EEG sample count
            cursor.execute("SELECT COUNT(*) as count FROM eeg_samples")
            eeg_count = cursor.fetchone()['count']
            
            # Get recent samples with joined data
            cursor.execute("""
                SELECT 
                    e.session_id,
                    e.question_id,
                    e.tp9, e.af7, e.af8, e.tp10,
                    r.difficulty,
                    r.is_correct,
                    r.response_time_ms
                FROM eeg_samples e
                INNER JOIN calibration_responses r 
                    ON e.session_id = r.session_id AND e.question_id = r.test_id
                ORDER BY e.created_at DESC
                LIMIT 10
            """)
            recent_samples = [dict(row) for row in cursor.fetchall()]
            
        return {
            "success": True,
            "summary": {
                "total_sessions": session_count,
                "total_eeg_samples": eeg_count,
                "difficulty_distribution": difficulty_counts,
                "total_training_pairs": len(recent_samples) if recent_samples else 0
            },
            "recent_samples": recent_samples[:5]  # Show first 5 for preview
        }
    except Exception as e:
        print(f"❌ Error getting training data preview: {e}")
        return {
            "success": False,
            "error": str(e)
        }

class TrainModelRequest(BaseModel):
    validation_split: Optional[float] = 0.2
    save_as_new_version: Optional[bool] = True

def clean_metrics_for_json(metrics):
    """Clean metrics by replacing NaN and infinity values with None"""
    import math
    
    def clean_value(value):
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        elif isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [clean_value(v) for v in value]
        return value
    
    return clean_value(metrics)

@app.post("/ml/train")
async def train_model(request: TrainModelRequest = TrainModelRequest()):
    """Train the cognitive load prediction model"""
    try:
        print("🧠 Training model request received")
        
        # Train the model
        training_result = cognitive_load_predictor.train_model(
            validation_split=request.validation_split
        )
        
        if not training_result.get('success', False):
            return {
                "success": False,
                "error": training_result.get('error', 'Training failed'),
                "metrics": clean_metrics_for_json(training_result)
            }
        
        # Save the trained model
        save_success = cognitive_load_predictor.save_model(
            save_as_new_version=request.save_as_new_version
        )
        
        if not save_success:
            print("⚠️ Model training succeeded but saving failed")
        
        print(f"✅ Model training completed. Samples: {training_result['n_samples']}, R²: {training_result.get('test_r2', 'N/A')}")
        
        return {
            "success": True,
            "message": "Model trained successfully",
            "training_metrics": clean_metrics_for_json(training_result),
            "model_saved": save_success,
            "model_version": cognitive_load_predictor.model_version
        }
        
    except Exception as e:
        print(f"❌ Error training model: {e}")
        return {
            "success": False,
            "error": str(e)
        }

class PredictRequest(BaseModel):
    eeg_data: List[dict]  # List of EEG samples with tp9, af7, af8, tp10

@app.post("/ml/predict")
async def predict_cognitive_load(request: PredictRequest):
    """Predict cognitive load from EEG data"""
    try:
        if not cognitive_load_predictor.is_trained:
            return {
                "success": False,
                "error": "Model not trained yet. Please train the model first."
            }
        
        # Make prediction
        prediction_result = cognitive_load_predictor.predict(request.eeg_data)
        
        return {
            "success": True,
            "prediction": prediction_result
        }
        
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        return {
            "success": False,
            "error": str(e)
        }

class PredictSingleRequest(BaseModel):
    tp9: float
    af7: float
    af8: float
    tp10: float

@app.post("/ml/predict-single")
async def predict_single_sample(request: PredictSingleRequest):
    """Predict cognitive load from a single EEG sample"""
    try:
        if not cognitive_load_predictor.is_trained:
            return {
                "success": False,
                "error": "Model not trained yet. Please train the model first."
            }
        
        # Make single prediction
        prediction_result = cognitive_load_predictor.predict_single(
            request.tp9, request.af7, request.af8, request.tp10
        )
        
        if 'error' in prediction_result:
            return {
                "success": False,
                "error": prediction_result['error']
            }
        
        return {
            "success": True,
            "prediction": prediction_result
        }
        
    except Exception as e:
        print(f"❌ Error making single prediction: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/ml/models")
async def list_model_versions():
    """List all available model versions"""
    try:
        models = cognitive_load_predictor.list_available_models()
        return {
            "success": True,
            "models": models,
            "current_version": cognitive_load_predictor.model_version
        }
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return {
            "success": False,
            "error": str(e)
        }

class LoadModelRequest(BaseModel):
    version: int

@app.post("/ml/load-model")
async def load_model_version(request: LoadModelRequest):
    """Load a specific model version"""
    try:
        success = cognitive_load_predictor.load_model(version=request.version)
        
        if success:
            return {
                "success": True,
                "message": f"Model v{request.version} loaded successfully",
                "current_version": cognitive_load_predictor.model_version
            }
        else:
            return {
                "success": False,
                "error": f"Failed to load model v{request.version}"
            }
            
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    # Start EEG service automatically
    print("🧠 Starting Synapse Backend...")
    print("🎯 Starting EEG service...")
    eeg_service.start_server()
    
    print("🌐 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
