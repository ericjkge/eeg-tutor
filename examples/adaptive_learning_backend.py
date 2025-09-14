#!/usr/bin/env python3
"""
Adaptive Learning Backend with EEG-Based Confusion Detection
Three-stage system: Calibration, Learning, Results
"""

import numpy as np
import json
import time
from datetime import datetime, timedelta
from collections import deque, defaultdict
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from scipy import signal
from pythonosc import dispatcher, osc_server
import threading
import os
import pickle
import math

class EEGProcessor:
    """Processes EEG data and extracts frequency features"""
    
    def __init__(self, sample_rate=256):
        self.sample_rate = sample_rate
        self.freq_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 50)
        }
    
    def extract_features(self, eeg_data):
        """Extract frequency domain features from EEG data"""
        if len(eeg_data) < 256:  # Need minimum samples
            return None
        
        features = {}
        
        # Convert to numpy array and get each channel
        channels = ['tp9', 'af7', 'af8', 'tp10']
        
        for i, channel in enumerate(channels):
            channel_data = [sample[channel] for sample in eeg_data if channel in sample]
            
            if len(channel_data) < 256:
                continue
                
            # Apply window and compute PSD
            windowed = np.array(channel_data) * signal.windows.hann(len(channel_data))
            freqs, psd = signal.welch(windowed, self.sample_rate, nperseg=min(256, len(channel_data)))
            
            # Extract power in each frequency band
            for band_name, (low, high) in self.freq_bands.items():
                band_mask = (freqs >= low) & (freqs <= high)
                band_power = np.mean(psd[band_mask])
                features[f'{channel}_{band_name}'] = band_power
            
            # Additional features
            features[f'{channel}_total_power'] = np.mean(psd)
            features[f'{channel}_peak_freq'] = freqs[np.argmax(psd)]
            
        return features

class ConfusionModel:
    """Linear regression model to predict confusion from EEG features"""
    
    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = None
        self.training_score = None
    
    def train(self, features_list, confusion_scores):
        """Train the confusion prediction model"""
        if len(features_list) < 5:  # Need minimum samples
            return False
        
        # Convert features to matrix
        feature_matrix = []
        self.feature_names = list(features_list[0].keys())
        
        for features in features_list:
            feature_vector = [features.get(name, 0) for name in self.feature_names]
            feature_matrix.append(feature_vector)
        
        X = np.array(feature_matrix)
        y = np.array(confusion_scores)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate training performance
        y_pred = self.model.predict(X_scaled)
        self.training_score = {
            'r2': r2_score(y, y_pred),
            'mse': mean_squared_error(y, y_pred),
            'samples': len(y)
        }
        
        self.is_trained = True
        return True
    
    def predict(self, features):
        """Predict confusion score from EEG features"""
        if not self.is_trained or not features:
            return None
        
        feature_vector = [features.get(name, 0) for name in self.feature_names]
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        return max(1, min(10, prediction))  # Clamp to 1-10 range

class Flashcard:
    """Individual flashcard with spaced repetition scheduling"""
    
    def __init__(self, front, back, card_id=None):
        self.id = card_id or str(int(time.time() * 1000))
        self.front = front
        self.back = back
        self.created_at = datetime.now()
        
        # Spaced repetition parameters
        self.ease_factor = 2.5
        self.interval = 1  # days
        self.repetitions = 0
        self.next_review = datetime.now()
        
        # EEG-based confusion tracking
        self.confusion_history = []
        self.avg_confusion = 5.0
        self.last_confusion = None
    
    def update_from_confusion(self, confusion_score):
        """Update spaced repetition schedule based on EEG confusion score"""
        self.last_confusion = confusion_score
        self.confusion_history.append({
            'score': confusion_score,
            'timestamp': datetime.now()
        })
        
        # Calculate average confusion (weighted toward recent)
        if len(self.confusion_history) > 10:
            recent_scores = [h['score'] for h in self.confusion_history[-10:]]
        else:
            recent_scores = [h['score'] for h in self.confusion_history]
        
        self.avg_confusion = np.mean(recent_scores)
        
        # Adjust scheduling based on confusion
        if confusion_score >= 7:  # High confusion
            # Review sooner and more frequently
            self.interval = max(0.1, self.interval * 0.5)
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        elif confusion_score >= 4:  # Medium confusion
            # Standard spaced repetition
            self.interval = self.interval * 1.0
        else:  # Low confusion (well understood)
            # Review less frequently
            self.interval = min(30, self.interval * 1.5)
            self.ease_factor = min(3.0, self.ease_factor + 0.1)
        
        # Set next review time
        self.next_review = datetime.now() + timedelta(days=self.interval)
        self.repetitions += 1

class AdaptiveLearningSystem:
    """Main system coordinating all three stages"""
    
    def __init__(self, osc_port=8000):
        self.osc_port = osc_port
        self.eeg_processor = EEGProcessor()
        self.confusion_model = ConfusionModel()
        
        # Data storage
        self.eeg_buffer = deque(maxlen=2560)  # 10 seconds at 256Hz
        self.calibration_data = []
        self.flashcards = {}
        self.learning_sessions = []
        
        # Current state
        self.current_stage = 'ready'  # ready, calibration, learning, results
        self.current_session = None
        self.is_collecting = False
        
        # Calibration prompts (20 varied difficulty levels)
        self.calibration_prompts = [
            # Easy (should score 1-3)
            "What is 2 + 2?",
            "What color is the sky?",
            "How many days are in a week?",
            
            # Medium-Easy (should score 3-5)
            "If you have 12 apples and eat 3, how many are left?",
            "What comes after Thursday?",
            "How many minutes are in an hour?",
            
            # Medium (should score 4-6)
            "If a train travels 60 mph for 2 hours, how far does it go?",
            "What is 15% of 200?",
            "If it's 3:45 PM, what time will it be in 2 hours and 30 minutes?",
            
            # Medium-Hard (should score 6-8)
            "A bat and ball cost $1.10 total. The bat costs $1 more than the ball. How much does the ball cost?",
            "If you're running a race and pass the person in 2nd place, what place are you in?",
            "Mary's father has 5 daughters: Nana, Nene, Nini, Nono. What's the 5th daughter's name?",
            
            # Hard (should score 7-9)
            "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
            "A man lives on the 20th floor. Every morning he takes the elevator down. When he comes home, he takes the elevator to the 10th floor and walks the rest... except on rainy days. Why?",
            "What comes next: O, T, T, F, F, S, S, E, ?",
            
            # Very Hard (should score 8-10)
            "You have 30 cows and 28 chickens. How many didn't?",
            "A rooster laid an egg on top of a barn roof. Which way did it roll?",
            "How much dirt is in a hole that measures 2 feet by 3 feet by 4 feet?",
            "If a plane crashes on the border of the US and Canada, where do they bury the survivors?",
            "Before Mount Everest was discovered, what was the tallest mountain in the world?"
        ]
        
        # Setup OSC server
        self.setup_osc_server()
    
    def setup_osc_server(self):
        """Setup OSC server to receive EEG data"""
        self.dispatcher = dispatcher.Dispatcher()
        self.dispatcher.map("/muse/eeg", self.eeg_handler)
        self.dispatcher.map("/eeg", self.eeg_handler)
        
        # Try multiple ports if 8000 is busy
        ports_to_try = [self.osc_port, 8001, 8002, 7000, 9000]
        
        for port in ports_to_try:
            try:
                self.server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), self.dispatcher)
                self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.server_thread.start()
                self.osc_port = port  # Update to actual port used
                print(f"✅ OSC server started on port {port}")
                return
            except Exception as e:
                if port == ports_to_try[-1]:  # Last port failed
                    print(f"❌ Failed to start OSC server on all ports: {e}")
                continue
    
    def eeg_handler(self, address, *args):
        """Handle incoming EEG data"""
        if len(args) >= 4 and self.is_collecting:
            timestamp = time.time()
            eeg_sample = {
                'timestamp': timestamp,
                'tp9': float(args[0]),
                'af7': float(args[1]),
                'af8': float(args[2]),
                'tp10': float(args[3])
            }
            self.eeg_buffer.append(eeg_sample)
    
    # STAGE 1: CALIBRATION
    def start_calibration(self):
        """Start the calibration stage"""
        self.current_stage = 'calibration'
        self.calibration_data = []
        self.is_collecting = True
        
        session = {
            'session_id': f"calibration_{int(time.time())}",
            'start_time': datetime.now(),
            'trials': [],
            'stage': 'calibration'
        }
        self.current_session = session
        return session
    
    def get_calibration_prompt(self, prompt_index):
        """Get a calibration prompt and start EEG collection"""
        if not self.current_session or prompt_index >= len(self.calibration_prompts):
            return None
        
        # Clear EEG buffer for new trial
        self.eeg_buffer.clear()
        
        trial = {
            'trial_id': prompt_index,
            'prompt': self.calibration_prompts[prompt_index],
            'start_time': time.time(),
            'eeg_data': [],
            'confusion_score': None
        }
        
        self.current_session['trials'].append(trial)
        return trial
    
    def submit_calibration_score(self, confusion_score):
        """Submit confusion score and process EEG data"""
        if not self.current_session or not self.current_session['trials']:
            return False
        
        current_trial = self.current_session['trials'][-1]
        current_trial['confusion_score'] = confusion_score
        current_trial['end_time'] = time.time()
        current_trial['eeg_data'] = list(self.eeg_buffer)
        
        # Extract features from EEG data
        features = self.eeg_processor.extract_features(current_trial['eeg_data'])
        if features:
            current_trial['eeg_features'] = features
            self.calibration_data.append({
                'features': features,
                'confusion_score': confusion_score
            })
        
        return True
    
    def finish_calibration(self):
        """Complete calibration and train the confusion model"""
        if not self.calibration_data:
            return False
        
        # Train the confusion prediction model
        features_list = [data['features'] for data in self.calibration_data]
        confusion_scores = [data['confusion_score'] for data in self.calibration_data]
        
        success = self.confusion_model.train(features_list, confusion_scores)
        
        if success:
            self.current_stage = 'ready_for_learning'
            self.is_collecting = False
            
            # Save calibration results
            self.save_calibration_data()
            
        return success
    
    def save_calibration_data(self):
        """Save calibration data and model"""
        timestamp = int(time.time())
        
        # Save session data
        filename = f"calibration_session_{timestamp}.json"
        with open(filename, 'w') as f:
            # Convert datetime objects to strings for JSON serialization
            session_copy = self.current_session.copy()
            session_copy['start_time'] = session_copy['start_time'].isoformat()
            json.dump(session_copy, f, indent=2)
        
        # Save trained model
        model_filename = f"confusion_model_{timestamp}.pkl"
        with open(model_filename, 'wb') as f:
            pickle.dump({
                'model': self.confusion_model,
                'training_score': self.confusion_model.training_score,
                'calibration_data': self.calibration_data
            }, f)
        
        print(f"📊 Calibration completed! Model R² score: {self.confusion_model.training_score['r2']:.3f}")
        return filename, model_filename
    
    # STAGE 2: LEARNING
    def add_flashcard(self, front, back):
        """Add a new flashcard to the system"""
        card = Flashcard(front, back)
        self.flashcards[card.id] = card
        return card.id
    
    def start_learning_session(self):
        """Start a learning session with spaced repetition"""
        if not self.confusion_model.is_trained:
            return None
        
        self.current_stage = 'learning'
        self.is_collecting = True
        
        session = {
            'session_id': f"learning_{int(time.time())}",
            'start_time': datetime.now(),
            'cards_reviewed': [],
            'stage': 'learning'
        }
        self.current_session = session
        self.learning_sessions.append(session)
        return session
    
    def get_next_flashcard(self):
        """Get the next flashcard based on spaced repetition and confusion"""
        if not self.flashcards:
            return None
        
        # Get cards that are due for review
        now = datetime.now()
        due_cards = [card for card in self.flashcards.values() if card.next_review <= now]
        
        if not due_cards:
            # If no cards are due, get the most confused ones
            due_cards = sorted(self.flashcards.values(), key=lambda x: x.avg_confusion, reverse=True)[:5]
        
        # Prioritize by confusion level and due date
        def priority_score(card):
            time_overdue = max(0, (now - card.next_review).total_seconds() / 3600)  # hours overdue
            return card.avg_confusion * 2 + time_overdue
        
        next_card = max(due_cards, key=priority_score)
        
        # Clear EEG buffer for new card
        self.eeg_buffer.clear()
        
        return {
            'card_id': next_card.id,
            'front': next_card.front,
            'back': next_card.back,
            'avg_confusion': next_card.avg_confusion,
            'repetitions': next_card.repetitions
        }
    
    def process_flashcard_review(self, card_id, user_rating=None):
        """Process flashcard review using EEG-based confusion detection"""
        if card_id not in self.flashcards:
            return None
        
        card = self.flashcards[card_id]
        
        # Extract EEG features and predict confusion
        eeg_features = self.eeg_processor.extract_features(list(self.eeg_buffer))
        predicted_confusion = None
        
        if eeg_features and self.confusion_model.is_trained:
            predicted_confusion = self.confusion_model.predict(eeg_features)
        
        # Use EEG prediction or fall back to user rating
        confusion_score = predicted_confusion if predicted_confusion else (user_rating or 5)
        
        # Update card's spaced repetition schedule
        card.update_from_confusion(confusion_score)
        
        # Record the review
        review_data = {
            'card_id': card_id,
            'timestamp': datetime.now(),
            'predicted_confusion': predicted_confusion,
            'user_rating': user_rating,
            'final_confusion': confusion_score,
            'eeg_features': eeg_features,
            'next_review': card.next_review,
            'interval': card.interval
        }
        
        if self.current_session:
            self.current_session['cards_reviewed'].append(review_data)
        
        return review_data
    
    # STAGE 3: RESULTS
    def generate_results(self):
        """Generate comprehensive results and statistics"""
        if not self.current_session:
            return None
        
        results = {
            'session_summary': {
                'session_id': self.current_session['session_id'],
                'start_time': self.current_session['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_cards_reviewed': len(self.current_session.get('cards_reviewed', [])),
                'stage': self.current_session['stage']
            },
            'model_performance': self.confusion_model.training_score if self.confusion_model.is_trained else None,
            'flashcard_statistics': self.get_flashcard_stats(),
            'confusion_analysis': self.analyze_confusion_patterns(),
            'learning_efficiency': self.calculate_learning_efficiency()
        }
        
        # Save results
        filename = f"results_{self.current_session['session_id']}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return results
    
    def get_flashcard_stats(self):
        """Get statistics about flashcard performance"""
        if not self.flashcards:
            return {}
        
        cards = list(self.flashcards.values())
        
        return {
            'total_cards': len(cards),
            'avg_confusion': np.mean([card.avg_confusion for card in cards]),
            'avg_repetitions': np.mean([card.repetitions for card in cards]),
            'cards_by_difficulty': {
                'easy': len([c for c in cards if c.avg_confusion < 3]),
                'medium': len([c for c in cards if 3 <= c.avg_confusion < 7]),
                'hard': len([c for c in cards if c.avg_confusion >= 7])
            },
            'most_confused_cards': [
                {'front': card.front, 'confusion': card.avg_confusion}
                for card in sorted(cards, key=lambda x: x.avg_confusion, reverse=True)[:5]
            ]
        }
    
    def analyze_confusion_patterns(self):
        """Analyze patterns in confusion over time"""
        if not self.current_session or 'cards_reviewed' not in self.current_session:
            return {}
        
        reviews = self.current_session['cards_reviewed']
        if not reviews:
            return {}
        
        confusion_scores = [r['final_confusion'] for r in reviews]
        timestamps = [r['timestamp'] for r in reviews]
        
        return {
            'avg_confusion': np.mean(confusion_scores),
            'confusion_trend': self.calculate_trend(confusion_scores),
            'total_reviews': len(reviews),
            'eeg_predictions_used': len([r for r in reviews if r['predicted_confusion'] is not None]),
            'confusion_distribution': {
                'low': len([s for s in confusion_scores if s < 4]),
                'medium': len([s for s in confusion_scores if 4 <= s < 7]),
                'high': len([s for s in confusion_scores if s >= 7])
            }
        }
    
    def calculate_learning_efficiency(self):
        """Calculate learning efficiency metrics"""
        if not self.flashcards:
            return {}
        
        cards = list(self.flashcards.values())
        
        # Cards that improved (confusion decreased over time)
        improved_cards = []
        for card in cards:
            if len(card.confusion_history) >= 2:
                first_confusion = card.confusion_history[0]['score']
                recent_confusion = np.mean([h['score'] for h in card.confusion_history[-3:]])
                if recent_confusion < first_confusion:
                    improved_cards.append(card)
        
        return {
            'total_cards_studied': len([c for c in cards if c.repetitions > 0]),
            'cards_improved': len(improved_cards),
            'improvement_rate': len(improved_cards) / max(1, len([c for c in cards if len(c.confusion_history) >= 2])),
            'avg_sessions_to_improve': np.mean([c.repetitions for c in improved_cards]) if improved_cards else 0
        }
    
    def calculate_trend(self, values):
        """Calculate trend direction of a series of values"""
        if len(values) < 2:
            return 0
        
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope
    
    def get_status(self):
        """Get current system status"""
        return {
            'stage': self.current_stage,
            'eeg_samples': len(self.eeg_buffer),
            'is_collecting': self.is_collecting,
            'model_trained': self.confusion_model.is_trained,
            'model_score': self.confusion_model.training_score['r2'] if self.confusion_model.is_trained else None,
            'total_flashcards': len(self.flashcards),
            'calibration_trials': len(self.calibration_data)
        }

# Global system instance
learning_system = AdaptiveLearningSystem()