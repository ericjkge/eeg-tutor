from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session

from eeg_service import eeg_service
from database import get_db, init_database, CalibrationSession, CalibrationResponse, EEGData

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

# Calibration Data Models
class CalibrationResponseData(BaseModel):
    testId: str
    question: str
    difficulty: str
    selectedAnswer: str
    correctAnswer: str
    isCorrect: bool
    timestamp: int
    timeSpent: int

class CalibrationSubmission(BaseModel):
    responses: List[CalibrationResponseData]
    sessionData: Optional[dict] = None

# Per-question calibration payload
class CalibrationAnswerData(BaseModel):
    session_id: int
    testId: str
    question: str
    difficulty: str
    selectedAnswer: str
    correctAnswer: str
    isCorrect: bool
    timestamp: int
    timeSpent: int

# Simple in-memory storage for now
decks_data = []
cards_data = []
next_deck_id = 1
next_card_id = 1

# Initialize with sample data
def init_sample_data():
    global next_deck_id, next_card_id, decks_data, cards_data
    
    # Sample deck
    sample_deck = Deck(
        id=next_deck_id,
        name="Spanish Vocabulary",
        description="Basic Spanish words"
    )
    decks_data.append(sample_deck.model_dump())
    next_deck_id += 1
    
    # Sample cards
    sample_cards = [
        Card(id=next_card_id, front="Hello", back="Hola", deck_id=1),
        Card(id=next_card_id + 1, front="Goodbye", back="Adiós", deck_id=1),
        Card(id=next_card_id + 2, front="Thank you", back="Gracias", deck_id=1),
    ]
    
    for card in sample_cards:
        cards_data.append(card.model_dump())
        next_card_id += 1

init_sample_data()

# API Routes
@app.get("/")
async def root():
    return {"message": "Synapse API is running"}

@app.get("/decks", response_model=List[Deck])
async def get_decks():
    # Attach cards to decks
    result = []
    for deck_data in decks_data:
        deck = Deck(**deck_data)
        deck.cards = [Card(**card) for card in cards_data if card["deck_id"] == deck.id]
        result.append(deck)
    return result

@app.get("/decks/{deck_id}", response_model=Deck)
async def get_deck(deck_id: int):
    deck_data = next((d for d in decks_data if d["id"] == deck_id), None)
    if not deck_data:
        return {"error": "Deck not found"}
    
    deck = Deck(**deck_data)
    deck.cards = [Card(**card) for card in cards_data if card["deck_id"] == deck_id]
    return deck

@app.post("/decks", response_model=Deck)
async def create_deck(deck: CreateDeck):
    global next_deck_id
    new_deck = Deck(
        id=next_deck_id,
        name=deck.name,
        description=deck.description,
        cards=[]
    )
    decks_data.append(new_deck.model_dump())
    next_deck_id += 1
    return new_deck

@app.post("/cards", response_model=Card)
async def create_card(card: CreateCard):
    global next_card_id
    new_card = Card(
        id=next_card_id,
        front=card.front,
        back=card.back,
        deck_id=card.deck_id
    )
    cards_data.append(new_card.model_dump())
    next_card_id += 1
    return new_card

@app.get("/cards/{card_id}", response_model=Card)
async def get_card(card_id: int):
    card_data = next((c for c in cards_data if c["id"] == card_id), None)
    if not card_data:
        return {"error": "Card not found"}
    return Card(**card_data)

@app.delete("/cards/{card_id}")
async def delete_card(card_id: int):
    global cards_data
    cards_data = [c for c in cards_data if c["id"] != card_id]
    return {"message": "Card deleted"}

@app.delete("/decks/{deck_id}")
async def delete_deck(deck_id: int):
    global decks_data, cards_data
    decks_data = [d for d in decks_data if d["id"] != deck_id]
    cards_data = [c for c in cards_data if c["deck_id"] != deck_id]
    return {"message": "Deck deleted"}

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

# Calibration Tests Endpoints
@app.get("/calibration/tests")
async def get_calibration_tests():
    """Get calibration test questions"""
    try:
        with open("tests.txt", "r") as f:
            tests = json.load(f)
        return {"tests": tests}
    except FileNotFoundError:
        return {"error": "Tests file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in tests file"}

@app.post("/calibration/start")
async def start_calibration_session(db: Session = Depends(get_db)):
    """Create a new calibration session and return its id"""
    session = CalibrationSession(
        user_id="default_user",
        started_at=datetime.utcnow(),
        total_questions=0,
        correct_answers=0,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"success": True, "session_id": session.id}

@app.post("/calibration/answer")
async def save_calibration_answer(
    answer: CalibrationAnswerData,
    db: Session = Depends(get_db),
):
    """Save a single calibration answer immediately when user clicks Next"""
    # Verify session exists
    session = db.query(CalibrationSession).filter(CalibrationSession.id == answer.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = CalibrationResponse(
        session_id=answer.session_id,
        test_id=answer.testId,
        question=answer.question,
        difficulty=answer.difficulty,
        selected_answer=answer.selectedAnswer,
        correct_answer=answer.correctAnswer,
        is_correct=answer.isCorrect,
        response_time_ms=answer.timeSpent,
        question_shown_at=datetime.fromtimestamp(answer.timestamp / 1000),
        answered_at=datetime.fromtimestamp((answer.timestamp + answer.timeSpent) / 1000),
    )
    db.add(response)

    # Update session counters incrementally
    session.total_questions = (session.total_questions or 0) + 1
    if answer.isCorrect:
        session.correct_answers = (session.correct_answers or 0) + 1

    db.commit()
    db.refresh(response)
    return {"success": True, "response_id": response.id}

@app.post("/calibration/complete")
async def complete_calibration_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Finalize a calibration session (sets completed_at and returns summary)"""
    session = db.query(CalibrationSession).filter(CalibrationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.completed_at:
        session.completed_at = datetime.utcnow()
        db.commit()

    # Recompute counters just in case
    responses = db.query(CalibrationResponse).filter(CalibrationResponse.session_id == session_id).all()
    session.total_questions = len(responses)
    session.correct_answers = sum(1 for r in responses if r.is_correct)
    db.commit()

    return {
        "success": True,
        "session": {
            "id": session.id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "accuracy": round((session.correct_answers or 0) / session.total_questions * 100, 1) if session.total_questions else 0,
        },
    }

@app.post("/calibration/submit")
async def submit_calibration_data(
    calibration_data: CalibrationSubmission,
    db: Session = Depends(get_db)
):
    """Save calibration session data to database"""
    try:
        # Create calibration session
        session = CalibrationSession(
            user_id="default_user",  # TODO: Add user authentication
            started_at=datetime.fromtimestamp(min(r.timestamp for r in calibration_data.responses) / 1000),
            completed_at=datetime.fromtimestamp(max(r.timestamp for r in calibration_data.responses) / 1000),
            total_questions=len(calibration_data.responses),
            correct_answers=sum(1 for r in calibration_data.responses if r.isCorrect)
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Save individual responses
        for response_data in calibration_data.responses:
            response = CalibrationResponse(
                session_id=session.id,
                test_id=response_data.testId,
                question=response_data.question,
                difficulty=response_data.difficulty,
                selected_answer=response_data.selectedAnswer,
                correct_answer=response_data.correctAnswer,
                is_correct=response_data.isCorrect,
                response_time_ms=response_data.timeSpent,
                question_shown_at=datetime.fromtimestamp(response_data.timestamp / 1000),
                answered_at=datetime.fromtimestamp((response_data.timestamp + response_data.timeSpent) / 1000)
            )
            db.add(response)
        
        db.commit()
        
        return {
            "success": True,
            "session_id": session.id,
            "message": f"Calibration data saved! Session {session.id} with {len(calibration_data.responses)} responses"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save calibration data: {str(e)}")

@app.get("/calibration/sessions")
async def get_calibration_sessions(db: Session = Depends(get_db)):
    """Get all calibration sessions"""
    sessions = db.query(CalibrationSession).all()
    return {
        "sessions": [
            {
                "id": session.id,
                "user_id": session.user_id,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "total_questions": session.total_questions,
                "correct_answers": session.correct_answers,
                "accuracy": round(session.correct_answers / session.total_questions * 100, 1) if session.total_questions > 0 else 0
            }
            for session in sessions
        ]
    }

@app.get("/calibration/sessions/{session_id}")
async def get_calibration_session(session_id: int, db: Session = Depends(get_db)):
    """Get detailed calibration session data"""
    session = db.query(CalibrationSession).filter(CalibrationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    responses = db.query(CalibrationResponse).filter(CalibrationResponse.session_id == session_id).all()
    
    return {
        "session": {
            "id": session.id,
            "user_id": session.user_id,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers
        },
        "responses": [
            {
                "id": response.id,
                "test_id": response.test_id,
                "question": response.question,
                "difficulty": response.difficulty,
                "selected_answer": response.selected_answer,
                "correct_answer": response.correct_answer,
                "is_correct": response.is_correct,
                "response_time_ms": response.response_time_ms,
                "answered_at": response.answered_at.isoformat()
            }
            for response in responses
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    # Initialize database
    print("🗄️ Initializing database...")
    init_database()
    
    # Start EEG service automatically
    print("🧠 Starting Synapse Backend...")
    print("🎯 Starting EEG service...")
    eeg_service.start_server()
    
    print("🌐 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
