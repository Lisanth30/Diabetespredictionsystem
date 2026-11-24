"""
Application Configuration Settings for HealthGuard Diabetes Prediction System
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'healthguard_secret_key_super_secure_2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'diabetes.db')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # ML Model configuration
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    MODEL_PATH = os.path.join(MODELS_DIR, 'diabetes_model.joblib')
    SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.joblib')
    IMPUTER_PATH = os.path.join(MODELS_DIR, 'imputer.joblib')
    METRICS_PATH = os.path.join(MODELS_DIR, 'metrics.json')
