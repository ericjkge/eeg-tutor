#!/usr/bin/env python3
"""
ML Service for Synapse EEG-Cognitive Load Prediction
Implements linear regression model to predict cognitive load from EEG data
"""

import numpy as np
import sqlite3
import pickle
import os
import time
from typing import Dict, List, Tuple, Optional, Any
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from database import get_db_connection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CognitiveLoadPredictor:
    """ML model for predicting cognitive load from EEG data"""
    
    def __init__(self, model_version: int = None):
        self.models_dir = "models"
        self.model_version = model_version or self._get_latest_version()
        self.model_path = os.path.join(self.models_dir, f"ml_model_{self.model_version}.pkl")
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['tp9', 'af7', 'af8', 'tp10', 'avg_all', 'tp9_af7_ratio', 'af8_tp10_ratio']
        self.difficulty_mapping = {'easy': 1, 'medium': 2, 'hard': 3}
        self.reverse_difficulty_mapping = {1: 'easy', 2: 'medium', 3: 'hard'}
        
        # Model performance metrics
        self.last_training_metrics = {}
        self.training_history = []
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
    
    def _get_latest_version(self) -> int:
        """Get the latest model version number"""
        if not os.path.exists("models"):
            return 1
        
        model_files = [f for f in os.listdir("models") if f.startswith("ml_model_") and f.endswith(".pkl")]
        if not model_files:
            return 1
        
        versions = []
        for filename in model_files:
            try:
                # Extract version number from ml_model_X.pkl
                version_str = filename.replace("ml_model_", "").replace(".pkl", "")
                versions.append(int(version_str))
            except ValueError:
                continue
        
        return max(versions) if versions else 1
    
    def _get_next_version(self) -> int:
        """Get the next model version number for saving"""
        return self._get_latest_version() + 1
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available model versions with metadata"""
        if not os.path.exists(self.models_dir):
            return []
        
        models = []
        model_files = [f for f in os.listdir(self.models_dir) if f.startswith("ml_model_") and f.endswith(".pkl")]
        
        for filename in model_files:
            try:
                version_str = filename.replace("ml_model_", "").replace(".pkl", "")
                version = int(version_str)
                filepath = os.path.join(self.models_dir, filename)
                
                # Get file metadata
                stat = os.stat(filepath)
                models.append({
                    'version': version,
                    'filename': filename,
                    'filepath': filepath,
                    'size_bytes': stat.st_size,
                    'created_at': stat.st_ctime,
                    'modified_at': stat.st_mtime,
                    'is_current': version == self.model_version
                })
            except (ValueError, OSError):
                continue
        
        # Sort by version number
        models.sort(key=lambda x: x['version'], reverse=True)
        return models
        
    def _extract_features(self, eeg_data: List[Dict[str, float]]) -> np.ndarray:
        """
        Extract features from EEG data
        
        Args:
            eeg_data: List of EEG samples with tp9, af7, af8, tp10 values
            
        Returns:
            Feature matrix (n_samples, n_features)
        """
        if not eeg_data:
            return np.array([]).reshape(0, len(self.feature_names))
        
        features = []
        for sample in eeg_data:
            tp9 = sample.get('tp9', 0.0)
            af7 = sample.get('af7', 0.0)
            af8 = sample.get('af8', 0.0)
            tp10 = sample.get('tp10', 0.0)
            
            # Basic features: raw channel values
            raw_features = [tp9, af7, af8, tp10]
            
            # Derived features
            avg_all = np.mean(raw_features)
            tp9_af7_ratio = tp9 / (af7 + 1e-8)  # Avoid division by zero
            af8_tp10_ratio = af8 / (tp10 + 1e-8)
            
            feature_vector = raw_features + [avg_all, tp9_af7_ratio, af8_tp10_ratio]
            features.append(feature_vector)
        
        return np.array(features)
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Prepare training data by joining EEG samples with calibration responses
        
        Returns:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,) - difficulty levels as integers
            metadata: List of dictionaries with additional info about each sample
        """
        logger.info("🔍 Preparing training data from database...")
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Join EEG samples with calibration responses on session_id and test_id
            query = """
            SELECT 
                e.session_id,
                e.question_id,
                e.tp9,
                e.af7,
                e.af8,
                e.tp10,
                e.timestamp,
                e.samples_averaged,
                r.difficulty,
                r.is_correct,
                r.response_time_ms,
                r.question,
                r.test_id
            FROM eeg_samples e
            INNER JOIN calibration_responses r 
                ON e.session_id = r.session_id AND e.question_id = r.test_id
            ORDER BY e.session_id, e.question_id
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
        if not rows:
            logger.warning("⚠️ No training data found in database")
            return np.array([]).reshape(0, len(self.feature_names)), np.array([]), []
        
        logger.info(f"📊 Found {len(rows)} EEG-response pairs for training")
        
        # Convert rows to feature matrix and target vector
        eeg_samples = []
        targets = []
        metadata = []
        
        for row in rows:
            # Extract EEG data
            eeg_sample = {
                'tp9': float(row['tp9']) if row['tp9'] is not None else 0.0,
                'af7': float(row['af7']) if row['af7'] is not None else 0.0,
                'af8': float(row['af8']) if row['af8'] is not None else 0.0,
                'tp10': float(row['tp10']) if row['tp10'] is not None else 0.0,
            }
            eeg_samples.append(eeg_sample)
            
            # Convert difficulty to numeric target
            difficulty = str(row['difficulty']).lower()
            target = self.difficulty_mapping.get(difficulty, 2)  # Default to medium if unknown
            targets.append(target)
            
            # Store metadata
            metadata.append({
                'session_id': row['session_id'],
                'question_id': row['question_id'],
                'difficulty_label': difficulty,
                'is_correct': bool(row['is_correct']),
                'response_time_ms': row['response_time_ms'],
                'question': row['question'],
                'timestamp': row['timestamp'],
                'samples_averaged': row['samples_averaged']
            })
        
        # Extract features
        X = self._extract_features(eeg_samples)
        y = np.array(targets)
        
        logger.info(f"✅ Prepared {X.shape[0]} samples with {X.shape[1]} features")
        logger.info(f"📈 Target distribution: {np.bincount(y, minlength=4)[1:4]}")  # Count for levels 1,2,3
        
        return X, y, metadata
    
    def train_model(self, validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the cognitive load prediction model
        
        Args:
            validation_split: Fraction of data to use for validation
            
        Returns:
            Dictionary with training metrics and results
        """
        logger.info("🧠 Starting model training...")
        
        # Prepare data
        X, y, metadata = self._prepare_training_data()
        
        if len(X) == 0:
            logger.error("❌ No training data available")
            return {
                'success': False,
                'error': 'No training data available',
                'n_samples': 0
            }
        
        if len(X) < 5:
            logger.warning(f"⚠️ Very few samples ({len(X)}) for training. Results may be unreliable.")
        
        # Split data
        if len(X) >= 10:
            # Use stratified split for larger datasets
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=validation_split, random_state=42, stratify=y
                )
            except ValueError:
                # Fallback to simple split if stratification fails
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=validation_split, random_state=42
                )
        elif len(X) >= 5:
            # Use simple split for medium datasets
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=validation_split, random_state=42
            )
        else:
            # Use all data for training if we have very few samples
            X_train, X_test, y_train, y_test = X, X, y, y
        
        # Scale features
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        start_time = time.time()
        self.model.fit(X_train_scaled, y_train)
        training_time = time.time() - start_time
        
        # Make predictions
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        metrics = {
            'success': True,
            'n_samples': len(X),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'training_time_seconds': training_time,
            'train_r2': r2_score(y_train, y_train_pred),
            'test_r2': r2_score(y_test, y_test_pred),
            'train_mse': mean_squared_error(y_train, y_train_pred),
            'test_mse': mean_squared_error(y_test, y_test_pred),
            'train_mae': mean_absolute_error(y_train, y_train_pred),
            'test_mae': mean_absolute_error(y_test, y_test_pred),
            'feature_names': self.feature_names,
            'feature_coefficients': self.model.coef_.tolist(),
            'intercept': float(self.model.intercept_),
            'difficulty_distribution': {
                'easy': int(np.sum(y == 1)),
                'medium': int(np.sum(y == 2)),
                'hard': int(np.sum(y == 3))
            }
        }
        
        # Cross-validation if we have enough samples
        if len(X) >= 5:
            try:
                cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=min(5, len(X_train)), scoring='r2')
                metrics['cv_r2_mean'] = float(np.mean(cv_scores))
                metrics['cv_r2_std'] = float(np.std(cv_scores))
            except Exception as e:
                logger.warning(f"⚠️ Cross-validation failed: {e}")
                metrics['cv_r2_mean'] = None
                metrics['cv_r2_std'] = None
        
        # Store results
        self.is_trained = True
        self.last_training_metrics = metrics
        self.training_history.append({
            'timestamp': time.time(),
            'metrics': metrics.copy()
        })
        
        logger.info(f"✅ Model training completed!")
        logger.info(f"📊 Test R² Score: {metrics['test_r2']:.3f}")
        logger.info(f"📊 Test MAE: {metrics['test_mae']:.3f}")
        
        return metrics
    
    def predict(self, eeg_data: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Predict cognitive load from EEG data
        
        Args:
            eeg_data: List of EEG samples with tp9, af7, af8, tp10 values
            
        Returns:
            Dictionary with predictions and confidence scores
        """
        if not self.is_trained:
            return {
                'success': False,
                'error': 'Model not trained yet'
            }
        
        if not eeg_data:
            return {
                'success': False,
                'error': 'No EEG data provided'
            }
        
        # Extract features
        X = self._extract_features(eeg_data)
        if len(X) == 0:
            return {
                'success': False,
                'error': 'Could not extract features from EEG data'
            }
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        
        # Convert predictions to difficulty labels and confidence
        results = []
        for i, pred in enumerate(predictions):
            # Clamp prediction to valid range
            pred_clamped = np.clip(pred, 1, 3)
            
            # Convert to discrete difficulty level (round to nearest integer)
            difficulty_level = int(np.round(pred_clamped))
            difficulty_label = self.reverse_difficulty_mapping.get(difficulty_level, 'medium')
            
            # Calculate confidence as inverse of distance from nearest integer
            confidence = 1.0 - abs(pred_clamped - difficulty_level)
            
            results.append({
                'sample_index': i,
                'raw_prediction': float(pred),
                'clamped_prediction': float(pred_clamped),
                'difficulty_level': difficulty_level,
                'difficulty_label': difficulty_label,
                'confidence': float(confidence),
                'eeg_features': X[i].tolist()
            })
        
        # Overall prediction (average of all samples)
        avg_prediction = np.mean(predictions)
        avg_difficulty_level = int(np.round(np.clip(avg_prediction, 1, 3)))
        avg_difficulty_label = self.reverse_difficulty_mapping.get(avg_difficulty_level, 'medium')
        
        return {
            'success': True,
            'n_samples': len(eeg_data),
            'individual_predictions': results,
            'overall_prediction': {
                'raw_prediction': float(avg_prediction),
                'difficulty_level': avg_difficulty_level,
                'difficulty_label': avg_difficulty_label,
                'confidence': float(np.mean([r['confidence'] for r in results]))
            }
        }
    
    def predict_single(self, tp9: float, af7: float, af8: float, tp10: float) -> Dict[str, Any]:
        """
        Predict cognitive load from single EEG sample
        
        Args:
            tp9, af7, af8, tp10: EEG channel values
            
        Returns:
            Dictionary with prediction and confidence
        """
        eeg_sample = [{'tp9': tp9, 'af7': af7, 'af8': af8, 'tp10': tp10}]
        result = self.predict(eeg_sample)
        
        if result['success']:
            return result['overall_prediction']
        else:
            return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'is_trained': self.is_trained,
            'model_version': self.model_version,
            'feature_names': self.feature_names,
            'last_training_metrics': self.last_training_metrics,
            'training_history_count': len(self.training_history),
            'model_type': 'LinearRegression',
            'model_path': self.model_path,
            'models_dir': self.models_dir,
            'available_models': self.list_available_models()
        }
    
    def save_model(self, save_as_new_version: bool = True) -> bool:
        """Save the trained model to disk"""
        if not self.is_trained:
            logger.error("❌ Cannot save untrained model")
            return False
        
        try:
            # Determine version and path for saving
            if save_as_new_version:
                save_version = self._get_next_version()
                save_path = os.path.join(self.models_dir, f"ml_model_{save_version}.pkl")
            else:
                save_version = self.model_version
                save_path = self.model_path
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'difficulty_mapping': self.difficulty_mapping,
                'reverse_difficulty_mapping': self.reverse_difficulty_mapping,
                'last_training_metrics': self.last_training_metrics,
                'training_history': self.training_history,
                'is_trained': self.is_trained,
                'model_version': save_version,
                'saved_at': time.time()
            }
            
            with open(save_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            # Update current instance to point to the new version
            if save_as_new_version:
                self.model_version = save_version
                self.model_path = save_path
            
            logger.info(f"✅ Model v{save_version} saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")
            return False
    
    def load_model(self, version: int = None) -> bool:
        """Load a trained model from disk"""
        # If specific version requested, update the path
        if version is not None:
            self.model_version = version
            self.model_path = os.path.join(self.models_dir, f"ml_model_{version}.pkl")
        
        if not os.path.exists(self.model_path):
            logger.info(f"ℹ️ No saved model found at {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.difficulty_mapping = model_data['difficulty_mapping']
            self.reverse_difficulty_mapping = model_data['reverse_difficulty_mapping']
            self.last_training_metrics = model_data['last_training_metrics']
            self.training_history = model_data['training_history']
            self.is_trained = model_data['is_trained']
            
            # Load version info if available (backwards compatibility)
            if 'model_version' in model_data:
                self.model_version = model_data['model_version']
            
            logger.info(f"✅ Model v{self.model_version} loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

# Global model instance
cognitive_load_predictor = CognitiveLoadPredictor()

# Auto-load model on import
cognitive_load_predictor.load_model()
