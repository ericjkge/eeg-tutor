# Synapse

An intelligent flashcard application that uses EEG data to determine cognitive load and optimize learning through adaptive spaced repetition.

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

### EEG Setup
1. Install Muse Direct app on your device
2. Connect your Muse EEG headband
3. Configure OSC streaming to `localhost:8001`

## Features

### ✅ Current Features
- **Flashcard System**: Create and manage decks with cards
- **Study Mode**: Interactive card studying with flip functionality
- **EEG Integration**: Real-time EEG data collection via OSC protocol
- **Machine Learning**: Cognitive load prediction using scikit-learn
- **Training Wizard**: Calibration system for EEG-cognitive load correlation
- **Real-time Visualization**: Live EEG data charts and frequency analysis
- **Persistent Storage**: SQLite database with comprehensive schema
- **Spaced Repetition**: Adaptive scheduling based on performance
- **Study Analytics**: Detailed statistics and review history
- **Modern UI**: Beautiful interface with Radix UI and animations

### 🔄 In Development
- Advanced ML models for better cognitive load prediction
- Automated difficulty adjustment based on EEG feedback
- Enhanced visualization with more EEG metrics
- Multi-user support and cloud synchronization

## API Endpoints

### Flashcard Management
- `GET /decks` - Get all decks with cards
- `POST /decks` - Create new deck
- `GET /decks/{deck_id}` - Get specific deck
- `DELETE /decks/{deck_id}` - Delete deck
- `POST /cards` - Create new card
- `GET /cards/{card_id}` - Get specific card
- `DELETE /cards/{card_id}` - Delete card
- `POST /cards/update-schedule` - Update spaced repetition schedule

### Study System
- `POST /study/start` - Start a study session
- `POST /study/review` - Record card review with performance
- `GET /study/stats` - Get study statistics
- `GET /study/history` - Get detailed study history

### EEG Integration
- `GET /eeg/status` - Check EEG connection status
- `GET /eeg/data` - Get latest EEG readings
- `GET /eeg/fft` - Get frequency domain analysis
- `POST /eeg/start` - Start EEG data collection
- `POST /eeg/stop` - Stop EEG data collection
- `POST /eeg/snapshot` - Save EEG snapshot for calibration
- `POST /eeg/predict-cognitive-load` - Get cognitive load prediction

### Calibration System
- `GET /calibration/tests` - Get available calibration questions
- `POST /calibration/start` - Start calibration session
- `POST /calibration/answer` - Submit calibration answer
- `POST /calibration/submit` - Submit calibration session
- `POST /calibration/complete` - Complete calibration process

### Machine Learning
- `GET /ml/status` - Get ML model status and metrics
- `GET /ml/training-data` - Get available training data summary
- `POST /ml/train` - Train ML model on calibration data
- `POST /ml/predict` - Predict cognitive load from EEG data
- `POST /ml/predict-single` - Single EEG sample prediction
- `GET /ml/models` - List available trained models
- `POST /ml/load-model` - Load specific model version

## Project Structure

```
eeg-tutor/
├── backend/                    # Python FastAPI Backend
│   ├── main.py                # FastAPI server with all endpoints
│   ├── database.py            # SQLite database operations
│   ├── eeg_service.py         # EEG data collection via OSC
│   ├── ml_service.py          # Machine learning cognitive load predictor
│   ├── requirements.txt       # Python dependencies
│   ├── synapse.db            # SQLite database file
│   ├── models/               # Trained ML models
│   │   └── ml_model_*.pkl    # Scikit-learn model files
│   ├── tests.txt             # Calibration questions
│   └── venv/                 # Python virtual environment
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx           # Main React application
│   │   ├── components/
│   │   │   ├── Welcome.jsx           # Landing page component
│   │   │   ├── TrainingWizard.jsx    # EEG calibration wizard
│   │   │   ├── EEGVisualization.jsx  # Real-time EEG charts
│   │   │   └── AuroraText.jsx        # Animated text component
│   │   ├── utils/
│   │   │   └── cn.js         # Utility functions
│   │   └── assets/           # Static assets
│   ├── package.json          # Node.js dependencies
│   └── node_modules/         # Node.js packages
├── examples/                   # Example implementations
│   ├── adaptive_learning_app.py      # Flask-based learning system
│   ├── adaptive_learning_backend.py  # Alternative backend implementation
│   └── muse_terminal_receiver.py     # Terminal EEG data receiver
├── architecture.mmd           # System architecture diagram
└── README.md                  # This file
```

## Database Schema

The application uses SQLite with the following main tables:

- **`decks`** - Flashcard deck metadata
- **`cards`** - Individual flashcards with spaced repetition data
- **`calibration_sessions`** - EEG calibration session tracking
- **`calibration_responses`** - User answers during calibration
- **`eeg_samples`** - EEG data snapshots linked to questions
- **`study_sessions`** - Daily study session tracking
- **`card_reviews`** - Individual card review history

## EEG Integration

### Hardware Requirements
- **Muse EEG Headband** (Muse 2, Muse S, or compatible 4-channel device)
- **Muse Direct App** for data streaming
- **Computer** with WiFi for OSC data reception

### Data Flow
1. **EEG Collection**: Muse headband captures 4-channel EEG (TP9, AF7, AF8, TP10)
2. **OSC Streaming**: Muse Direct streams data via OSC protocol to port 8001
3. **Feature Extraction**: Backend processes raw EEG into frequency domain features
4. **Calibration**: User answers questions while EEG data is collected
5. **Model Training**: Machine learning model learns EEG-cognitive load correlation
6. **Real-time Prediction**: Trained model predicts cognitive load during study sessions

### Machine Learning Pipeline
- **Algorithm**: Linear Regression with StandardScaler preprocessing
- **Features**: Raw EEG channels + derived ratios and averages
- **Training**: Cross-validated on calibration session data
- **Prediction**: Real-time cognitive load estimation (easy/medium/hard)

## Development Notes

- **CORS**: Configured for localhost development (ports 5173 ↔ 8000)
- **Database**: Persistent SQLite storage with automatic schema initialization
- **EEG Service**: Runs on separate port 8001 for OSC data reception
- **Model Versioning**: ML models saved with incremental version numbers
- **Real-time Updates**: Frontend polls backend for live EEG visualization
- **Error Handling**: Comprehensive error handling for EEG connection issues

## Dependencies

### Backend (Python)
- **FastAPI**: Web framework and API server
- **SQLAlchemy**: Database ORM and operations
- **scikit-learn**: Machine learning algorithms
- **NumPy/SciPy**: Numerical computing and signal processing
- **python-osc**: OSC protocol for EEG data reception

### Frontend (React)
- **React 19**: Modern React with hooks
- **Radix UI**: Accessible component library
- **Chart.js**: Real-time data visualization
- **Framer Motion**: Smooth animations and transitions
- **Vite**: Fast development build tool
