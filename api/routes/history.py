from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import Scan, db
from utils.notifications import create_in_app_notification

history_bp = Blueprint('history', __name__)


@history_bp.route('/scans', methods=['GET'])
@jwt_required()
def get_scans():
    """Get all scans for current user"""
    try:
        user_id = int(get_jwt_identity())
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query scans
        scans_query = Scan.query.filter_by(user_id=user_id)\
            .order_by(Scan.created_at.desc())
        
        # Get total count
        total = scans_query.count()
        
        # Paginate
        scans = scans_query.limit(per_page).offset((page - 1) * per_page).all()
        
        return jsonify({
            'scans': [scan.to_dict() for scan in scans],
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page if total > 0 else 0
        }), 200
        
    except Exception as e:
        print(f"Error in get_scans: {e}")
        return jsonify({'error': str(e)}), 500


@history_bp.route('/scans/<int:scan_id>', methods=['GET'])
@jwt_required()
def get_scan(scan_id):
    """Get single scan details"""
    try:
        user_id = int(get_jwt_identity())
        
        scan = Scan.query.filter_by(id=scan_id, user_id=user_id).first()
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        return jsonify({'scan': scan.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@history_bp.route('/scans/all', methods=['DELETE'])
@jwt_required()
def delete_all_scans():
    """Delete all scans for current user"""
    try:
        user_id = int(get_jwt_identity())
        
        # Delete all
        Scan.query.filter_by(user_id=user_id).delete()
        
        create_in_app_notification(
            user_id=user_id,
            title="History Cleared",
            message="You have permanently deleted all your previously saved scan results.",
            type="system"
        )
        
        db.session.commit()
        
        return jsonify({'message': 'All history cleared'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@history_bp.route('/scans/<int:scan_id>', methods=['DELETE'])
@jwt_required()
def delete_scan(scan_id):
    """Delete a scan"""
    try:
        user_id = int(get_jwt_identity())
        
        scan = Scan.query.filter_by(id=scan_id, user_id=user_id).first()
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        db.session.delete(scan)
        
        create_in_app_notification(
            user_id=user_id,
            title="Scan Deleted",
            message=f"You deleted a scan result from {scan.created_at.strftime('%B %d, %Y')}.",
            type="system"
        )
        
        db.session.commit()
        
        return jsonify({'message': 'Scan deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@history_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get user statistics"""
    try:
        user_id = int(get_jwt_identity())
        
        total_scans = Scan.query.filter_by(user_id=user_id).count()
        
        # Count by prediction
        from sqlalchemy import func
        prediction_counts = db.session.query(
            Scan.prediction,
            func.count(Scan.id)
        ).filter_by(user_id=user_id).group_by(Scan.prediction).all()
        
        by_prediction = {pred: count for pred, count in prediction_counts}
        
        stats = {
            'total_scans': total_scans,
            'by_prediction': by_prediction
        }
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        print(f"Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500
