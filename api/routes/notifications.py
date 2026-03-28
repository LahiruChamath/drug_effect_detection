from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import Notification, db
from utils.notifications import create_in_app_notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get all notifications for current user"""
    try:
        user_id = int(get_jwt_identity())
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(50).all()
        
        unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'unread_count': unread_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/notifications/read', methods=['POST'])
@jwt_required()
def mark_read():
    """Mark notifications as read"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        
        query = Notification.query.filter_by(user_id=user_id, is_read=False)
        
        # If specific IDs are provided, only mark those
        if 'notification_ids' in data and data['notification_ids']:
            query = query.filter(Notification.id.in_(data['notification_ids']))
            
        notifications = query.all()
        for notif in notifications:
            notif.is_read = True
            
        db.session.commit()
        return jsonify({'message': f'Marked {len(notifications)} notifications as read'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/log_export', methods=['POST'])
@jwt_required()
def log_export():
    """Log when a user exports their data"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        export_type = data.get('export_type', 'data')
        
        create_in_app_notification(
            user_id=user_id,
            title="Data Exported",
            message=f"You successfully exported your scan history as {export_type.upper()}.",
            type="export"
        )
        return jsonify({'message': 'Export logged successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
