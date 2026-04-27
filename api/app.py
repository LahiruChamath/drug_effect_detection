import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from routes.auth import auth_bp
from routes.predict import predict_bp
from routes.history import history_bp
from routes.notifications import notifications_bp

from flask_mail import Mail
import firebase_admin
from firebase_admin import credentials

mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS - simplified version
    CORS(app, supports_credentials=True)
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    mail.init_app(app)
    
    # Initialize Firebase Admin
    try:
        cred_path = app.config['FIREBASE_SERVICE_ACCOUNT_PATH']
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Admin initialized!")
        else:
            print(f"⚠️ Warning: Firebase service account not found at {cred_path}. Push notifications will be disabled.")
    except Exception as e:
        print(f"❌ Error initializing Firebase: {e}")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(predict_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api')
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'healthy',
            'model': 'XGBoost',
            'accuracy': '85%'
        })
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("✅ Database tables created!")
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "=" * 50)
    print("  SafePose API Server")
    print("=" * 50)
    print("  Endpoints:")
    print("    POST /api/auth/register")
    print("    POST /api/auth/login")
    print("    GET  /api/auth/me")
    print("    POST /api/predict")
    print("    GET  /api/scans")
    print("    GET  /api/stats")
    print("=" * 50 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
