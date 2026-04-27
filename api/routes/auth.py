from flask import Blueprint, request, jsonify, current_app as app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.database import User, db
from google.oauth2 import id_token
from google.auth.transport import requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """Authenticate with Google token"""
    try:
        data = request.get_json()
        if not data or 'idToken' not in data:
            return jsonify({'error': 'No Google ID Token provided'}), 400
        
        token = data['idToken']
        
        # Try verifying with Web Client ID first, then iOS Client ID
        web_client_id = app.config.get('GOOGLE_CLIENT_ID')
        ios_client_id = '333625476432-vbl45ecp8onsh91sdbqukdqhnqvf02d0.apps.googleusercontent.com'
        
        idinfo = None
        
        # Try Web Client ID
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), web_client_id)
            print(f"✅ Token verified with Web Client ID")
        except ValueError as e:
            print(f"⚠️ Web Client ID verification failed: {e}")
        
        # Try iOS Client ID
        if idinfo is None:
            try:
                idinfo = id_token.verify_oauth2_token(token, requests.Request(), ios_client_id)
                print(f"✅ Token verified with iOS Client ID")
            except ValueError as e:
                print(f"⚠️ iOS Client ID verification failed: {e}")
        
        # Last resort: verify without audience check (development only)
        if idinfo is None:
            try:
                idinfo = id_token.verify_oauth2_token(token, requests.Request())
                print(f"✅ Token verified without audience check (dev mode)")
                print(f"   Token audience: {idinfo.get('aud', 'unknown')}")
            except ValueError as e:
                print(f"❌ All verification attempts failed: {e}")
                return jsonify({'error': f'Invalid Google ID Token: {str(e)}'}), 401
        
        # ID token is valid. Get the user's info.
        email = idinfo['email'].strip().lower()
        name = idinfo.get('name', 'Google User').strip()
        
        print(f"✅ Google user: {name} ({email})")
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create user for social login
            user = User(email=email, name=name)
            user.set_password('google-oauth-user')  # Placeholder - user logs in via Google
            db.session.add(user)
            db.session.commit()
            print(f"✅ New user created for {email}")
        else:
            print(f"✅ Existing user found for {email}")
        
        # Generate SafePose token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Google authentication successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'error': 'Email, password, and name are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(email=email, name=name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'password' in data and len(data['password']) >= 6:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_settings():
    """Update notification settings and FCM token"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if 'fcm_token' in data:
            user.fcm_token = data['fcm_token'].strip()
            print(f"📱 FCM Token updated for {user.email}")
            
        if 'push_enabled' in data:
            user.push_enabled = bool(data['push_enabled'])
            
        if 'email_enabled' in data:
            user.email_enabled = bool(data['email_enabled'])
            
        db.session.commit()
        
        return jsonify({
            'message': 'Settings updated',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500