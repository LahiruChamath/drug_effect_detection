import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import traceback
from services.ml_service import ml_service
from services.pose_extractor import PoseExtractor
from utils.notifications import send_push_notification, send_scan_result_email
from models.database import User, Scan, db

predict_bp = Blueprint('predict', __name__)

# Initialize pose extractor globally
try:
    pose_extractor = PoseExtractor(max_duration=10.0)
except Exception as e:
    print(f"Warning: Could not initialize PoseExtractor. {e}")
    pose_extractor = None

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
        
        # Send notifications
        user = User.query.get(user_id)
        if user:
            # Push
            send_push_notification(
                user, 
                "Scan Completed", 
                f"Result: {scan.prediction.capitalize()} ({int(scan.confidence * 100)}% Confidence)",
                data={"scan_id": str(scan.id)}
            )
            # Email
            send_scan_result_email(user, scan)
        
        return jsonify({
            'scan_id': scan.id,
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'frames_analyzed': len(frames)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@predict_bp.route('/analyze_video', methods=['POST'])
@jwt_required()
def analyze_video():
    """Predict drug effect from uploaded video file natively via server ML"""
    filepath = None
    try:
        user_id = int(get_jwt_identity())
        
        if pose_extractor is None:
            return jsonify({'error': 'Server missing Mediapipe/OpenCV dependencies'}), 500
            
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
            
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': 'No video file selected'}), 400
            
        # Save temp video
        temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp_videos')
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(temp_dir, unique_filename)
        
        file.save(filepath)
        
        # Extract poses
        sequence = pose_extractor.extract_from_video(filepath, label='none', show_progress=False)
        
        # Convert to list for ml_service
        frames = sequence.to_numpy().tolist()
        
        if len(frames) < 30:
            return jsonify({'error': 'Need at least 30 frames with detectable poses'}), 400
            
        # Get prediction
        result = ml_service.predict(frames)
        
        # Save to database
        scan = Scan(
            user_id=user_id,
            prediction=result['prediction'],
            confidence=result['confidence'],
            probabilities=result['probabilities'],
            frames_analyzed=len(frames),
            duration_seconds=sequence.duration
        )
        
        db.session.add(scan)
        db.session.commit()
        
        # Send notifications
        user = User.query.get(user_id)
        if user:
            # Push
            send_push_notification(
                user, 
                "Video Analysis Completed", 
                f"Result: {scan.prediction.capitalize()} ({int(scan.confidence * 100)}% Confidence)",
                data={"scan_id": str(scan.id)}
            )
            # Email
            send_scan_result_email(user, scan)
        
        return jsonify({
            'scan_id': scan.id,
            'prediction': result['prediction'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'frames_analyzed': len(frames)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass