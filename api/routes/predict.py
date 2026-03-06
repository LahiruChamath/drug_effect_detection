from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import Scan, db
from services.ml_service import ml_service

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """Predict drug effect from pose frames"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        if 'frames' not in data:
            return jsonify({'error': 'Missing frames data'}), 400
        
        frames = data['frames']
        
        if len(frames) < 30:
            return jsonify({'error': 'Need at least 30 frames'}), 400
        
        # Get prediction
        result = ml_service.predict(frames)
        
        # Save to database
        scan = Scan(
            user_id=user_id,
            prediction=result['prediction'],
            confidence=result['confidence'],
            probabilities=result['probabilities'],
            frames_analyzed=len(frames),
            duration_seconds=len(frames) / 30.0  # Assuming 30 FPS
        )
        
        db.session.add(scan)
        db.session.commit()
        
        return jsonify({
            'scan_id': scan.id,
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'frames_analyzed': len(frames)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500