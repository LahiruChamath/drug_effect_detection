import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///safepose.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Model paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'drug_classifier_xgboost.pkl')
    SVM_PATH = os.path.join(BASE_DIR, 'models', 'drug_classifier_svm.pkl')
    LSTM_PATH = os.path.join(BASE_DIR, 'models', 'best_lstm_model.h5')
    SCALER_PATH = os.path.join(BASE_DIR, 'models', 'scaler.pkl')
    ENCODER_PATH = os.path.join(BASE_DIR, 'models', 'label_encoder.pkl')
    
    # Google Auth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or '333625476432-na4lks9opog2ss8a1kseh7vk9hb6293d.apps.googleusercontent.com'