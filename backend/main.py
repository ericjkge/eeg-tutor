from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from eeg_service import eeg_service

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

if __name__ == "__main__":
    import uvicorn
    
    # Start EEG service automatically
    print("🧠 Starting Synapse Backend...")
    print("🎯 Starting EEG service...")
    eeg_service.start_server()
    
    print("🌐 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
