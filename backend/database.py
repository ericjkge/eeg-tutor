#!/usr/bin/env python3
"""
Database models and setup for Synapse
SQLite database for storing calibration and EEG data
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json

# Database setup
DATABASE_URL = "sqlite:///./synapse.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CalibrationSession(Base):
    """Stores calibration session metadata"""
    __tablename__ = "calibration_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user")  # For future multi-user support
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_questions = Column(Integer)
    correct_answers = Column(Integer, default=0)
    
    # Relationships
    responses = relationship("CalibrationResponse", back_populates="session")
    eeg_data = relationship("EEGData", back_populates="session")

class CalibrationResponse(Base):
    """Stores individual question responses during calibration"""
    __tablename__ = "calibration_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("calibration_sessions.id"))
    
    # Question data
    test_id = Column(String)  # e.g., "M3", "E2", "H1"
    question = Column(Text)
    difficulty = Column(String)  # easy, medium, hard
    
    # Response data
    selected_answer = Column(String)
    correct_answer = Column(String)
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)  # Time spent on question
    
    # Timestamps
    question_shown_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("CalibrationSession", back_populates="responses")

class EEGData(Base):
    """Stores EEG data collected during calibration"""
    __tablename__ = "eeg_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("calibration_sessions.id"))
    response_id = Column(Integer, ForeignKey("calibration_responses.id"), nullable=True)
    
    # EEG measurements
    timestamp = Column(DateTime, default=datetime.utcnow)
    tp9 = Column(Float)  # Left ear electrode
    af7 = Column(Float)  # Left forehead electrode  
    af8 = Column(Float)  # Right forehead electrode
    tp10 = Column(Float) # Right ear electrode
    
    # Additional sensor data (optional)
    accelerometer_x = Column(Float, nullable=True)
    accelerometer_y = Column(Float, nullable=True)
    accelerometer_z = Column(Float, nullable=True)
    
    # Data quality indicators
    sample_rate = Column(Float, nullable=True)
    connection_quality = Column(String, nullable=True)
    
    # Relationships
    session = relationship("CalibrationSession", back_populates="eeg_data")

class MLModel(Base):
    """Stores trained ML models and their metadata"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user")
    model_name = Column(String)  # e.g., "confusion_detector_v1"
    model_type = Column(String)  # e.g., "sklearn_random_forest"
    
    # Model performance metrics
    accuracy = Column(Float, nullable=True)
    training_samples = Column(Integer, nullable=True)
    
    # Model file path or serialized data
    model_path = Column(String, nullable=True)
    model_data = Column(Text, nullable=True)  # JSON serialized model
    
    # Timestamps
    trained_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

def create_database():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database with tables"""
    create_database()
    print("✅ Database initialized with tables:")
    print("   - calibration_sessions")
    print("   - calibration_responses") 
    print("   - eeg_data")
    print("   - ml_models")
    print(f"📁 Database file: {DATABASE_URL}")

if __name__ == "__main__":
    init_database()
