# Synapse

A flashcard application that uses EEG data to determine confusion levels and optimize learning.

## Quick Start

### Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Backend will run on http://localhost:8000

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Frontend will run on http://localhost:5173

## Features

### Current
- ✅ Create and manage decks
- ✅ Add cards to decks
- ✅ Study cards with flip functionality
- ✅ Basic statistics
- ✅ Navigation between cards
- ✅ Difficulty rating buttons (ready for EEG integration)

### Planned
- 🔄 EEG integration for automatic confusion detection
- 🔄 Spaced repetition algorithm
- 🔄 Training UI for confusion level calibration
- 🔄 Real-time brainwave visualization
- 🔄 Persistent data storage

## API Endpoints

- `GET /decks` - Get all decks with cards
- `POST /decks` - Create new deck
- `GET /decks/{deck_id}` - Get specific deck
- `DELETE /decks/{deck_id}` - Delete deck
- `POST /cards` - Create new card
- `GET /cards/{card_id}` - Get specific card
- `DELETE /cards/{card_id}` - Delete card

## Project Structure

```
eeg-tutor/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── requirements.txt  # Python dependencies
│   └── venv/            # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main React component
│   │   └── App.css      # Styles
│   ├── package.json
│   └── node_modules/
└── README.md
```

## Integration Points for EEG

The app is designed to integrate with EEG processing scripts:

1. **Confusion Detection**: The difficulty buttons in study mode are ready to be replaced with automatic EEG-based confusion detection
2. **Real-time Data**: WebSocket support can be added for live EEG streaming
3. **Training Mode**: Structure is ready for the training UI where users manually indicate confusion levels
4. **Visualization**: Placeholder exists in study mode for brainwave visualization

## Development Notes

- CORS is configured for localhost development
- Data is currently stored in memory (will reset on server restart)
- Sample data is automatically created on startup
- Frontend automatically connects to backend on port 8000
