#!/usr/bin/env python3
"""
Adaptive Learning Web App
Three-stage EEG-based learning system: Calibration, Learning, Results
"""

from flask import Flask, render_template, jsonify, request
import json
import numpy as np
from adaptive_learning_backend import learning_system

app = Flask(__name__)

@app.route('/')
def index():
    """Main application interface"""
    return render_template('adaptive_learning.html')

# STAGE 1: CALIBRATION ENDPOINTS
@app.route('/api/calibration/start', methods=['POST'])
def start_calibration():
    """Start calibration stage"""
    session = learning_system.start_calibration()
    return jsonify({
        'session_id': session['session_id'],
        'total_prompts': len(learning_system.calibration_prompts),
        'status': 'calibration_started'
    })

@app.route('/api/calibration/prompt/<int:prompt_index>')
def get_calibration_prompt(prompt_index):
    """Get calibration prompt"""
    trial = learning_system.get_calibration_prompt(prompt_index)
    if trial:
        return jsonify({
            'trial_id': trial['trial_id'],
            'prompt': trial['prompt'],
            'prompt_number': prompt_index + 1,
            'total_prompts': len(learning_system.calibration_prompts),
            'status': 'prompt_ready'
        })
    return jsonify({'error': 'Invalid prompt index'}), 400

@app.route('/api/calibration/submit', methods=['POST'])
def submit_calibration_score():
    """Submit calibration confusion score"""
    data = request.json
    confusion_score = data.get('score')
    
    if learning_system.submit_calibration_score(confusion_score):
        return jsonify({'status': 'score_recorded'})
    return jsonify({'error': 'Failed to record score'}), 400

@app.route('/api/calibration/finish', methods=['POST'])
def finish_calibration():
    """Complete calibration and train model"""
    success = learning_system.finish_calibration()
    if success:
        return jsonify({
            'status': 'calibration_complete',
            'model_score': learning_system.confusion_model.training_score,
            'ready_for_learning': True
        })
    return jsonify({'error': 'Calibration failed'}), 400

# STAGE 2: LEARNING ENDPOINTS
@app.route('/api/flashcards/add', methods=['POST'])
def add_flashcard():
    """Add a new flashcard"""
    data = request.json
    front = data.get('front')
    back = data.get('back')
    
    if not front or not back:
        return jsonify({'error': 'Front and back are required'}), 400
    
    card_id = learning_system.add_flashcard(front, back)
    return jsonify({'card_id': card_id, 'status': 'card_added'})

@app.route('/api/flashcards/bulk_add', methods=['POST'])
def bulk_add_flashcards():
    """Add multiple flashcards at once"""
    data = request.json
    cards = data.get('cards', [])
    
    added_cards = []
    for card_data in cards:
        if 'front' in card_data and 'back' in card_data:
            card_id = learning_system.add_flashcard(card_data['front'], card_data['back'])
            added_cards.append(card_id)
    
    return jsonify({
        'cards_added': len(added_cards),
        'card_ids': added_cards,
        'status': 'bulk_add_complete'
    })

@app.route('/api/flashcards/list')
def list_flashcards():
    """Get all flashcards"""
    cards = []
    for card_id, card in learning_system.flashcards.items():
        cards.append({
            'id': card_id,
            'front': card.front,
            'back': card.back,
            'avg_confusion': card.avg_confusion,
            'repetitions': card.repetitions,
            'next_review': card.next_review.isoformat(),
            'interval': card.interval
        })
    
    return jsonify({'cards': cards, 'total': len(cards)})

@app.route('/api/learning/start', methods=['POST'])
def start_learning():
    """Start learning session"""
    session = learning_system.start_learning_session()
    if session:
        return jsonify({
            'session_id': session['session_id'],
            'total_cards': len(learning_system.flashcards),
            'status': 'learning_started'
        })
    return jsonify({'error': 'Model not calibrated'}), 400

@app.route('/api/learning/next_card')
def get_next_card():
    """Get next flashcard for review"""
    card_data = learning_system.get_next_flashcard()
    if card_data:
        return jsonify(card_data)
    return jsonify({'error': 'No cards available'}), 400

@app.route('/api/learning/review', methods=['POST'])
def review_flashcard():
    """Process flashcard review"""
    data = request.json
    card_id = data.get('card_id')
    user_rating = data.get('user_rating')  # Optional manual rating
    
    review_data = learning_system.process_flashcard_review(card_id, user_rating)
    if review_data:
        return jsonify({
            'predicted_confusion': review_data['predicted_confusion'],
            'final_confusion': review_data['final_confusion'],
            'next_review': review_data['next_review'].isoformat(),
            'interval_days': review_data['interval'],
            'status': 'review_processed'
        })
    return jsonify({'error': 'Failed to process review'}), 400

# STAGE 3: RESULTS ENDPOINTS
@app.route('/api/results/generate', methods=['POST'])
def generate_results():
    """Generate comprehensive results"""
    results = learning_system.generate_results()
    if results:
        return jsonify(results)
    return jsonify({'error': 'No session data available'}), 400

@app.route('/api/results/flashcard_stats')
def get_flashcard_stats():
    """Get flashcard statistics"""
    stats = learning_system.get_flashcard_stats()
    return jsonify(stats)

@app.route('/api/results/confusion_analysis')
def get_confusion_analysis():
    """Get confusion pattern analysis"""
    analysis = learning_system.analyze_confusion_patterns()
    return jsonify(analysis)

@app.route('/api/results/learning_efficiency')
def get_learning_efficiency():
    """Get learning efficiency metrics"""
    efficiency = learning_system.calculate_learning_efficiency()
    return jsonify(efficiency)

# GENERAL ENDPOINTS
@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify(learning_system.get_status())

@app.route('/api/eeg/live')
def get_live_eeg():
    """Get live EEG data for visualization"""
    # Get recent EEG samples (last 100 samples for smooth visualization)
    recent_samples = list(learning_system.eeg_buffer)[-100:] if learning_system.eeg_buffer else []
    
    # Format for frontend visualization
    eeg_data = {
        'timestamps': [sample['timestamp'] for sample in recent_samples],
        'tp9': [sample['tp9'] for sample in recent_samples],
        'af7': [sample['af7'] for sample in recent_samples], 
        'af8': [sample['af8'] for sample in recent_samples],
        'tp10': [sample['tp10'] for sample in recent_samples],
        'sample_count': len(recent_samples),
        'is_collecting': learning_system.is_collecting
    }
    
    return jsonify(eeg_data)

@app.route('/api/reset', methods=['POST'])
def reset_system():
    """Reset the entire system"""
    learning_system.current_stage = 'ready'
    learning_system.is_collecting = False
    learning_system.calibration_data = []
    learning_system.current_session = None
    learning_system.confusion_model = learning_system.confusion_model.__class__()
    
    return jsonify({'status': 'system_reset'})

if __name__ == '__main__':
    print("🧠 Adaptive Learning System Starting...")
    print(f"📡 OSC server listening on port {learning_system.osc_port}")
    print("🌐 Web app available at: http://localhost:5002")
    print("🎯 Three-stage system: Calibration → Learning → Results")
    print(f"⚠️  Update your Muse app to send OSC data to port {learning_system.osc_port}")
    print("-" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5002)