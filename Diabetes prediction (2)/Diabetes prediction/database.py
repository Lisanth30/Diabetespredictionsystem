"""
Database Configuration, Schema Models, and Queries for Diabetes Prediction System
Supports SQLite (default) and MySQL via SQLAlchemy.
"""

import json
import os
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, func, desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'diabetes.db')
DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')

engine = create_engine(
    DATABASE_URI,
    connect_args={'check_same_thread': False} if DATABASE_URI.startswith('sqlite') else {},
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user', nullable=False)  # 'user' or 'admin'
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    predictions = relationship('Prediction', back_populates='user', cascade='all, delete-orphan', order_by='desc(Prediction.created_at)')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'prediction_count': len(self.predictions)
        }


class Prediction(Base):
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Clinical input parameters
    pregnancies = Column(Integer, nullable=False)
    glucose = Column(Float, nullable=False)
    blood_pressure = Column(Float, nullable=False)
    skin_thickness = Column(Float, nullable=False)
    insulin = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)
    diabetes_pedigree_function = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    
    # Model evaluation output
    prediction_outcome = Column(Integer, nullable=False)  # 0 or 1
    probability = Column(Float, nullable=False)          # 0.0 to 100.0%
    risk_level = Column(String(20), nullable=False)      # 'Low', 'Medium', 'High'
    contributing_factors_json = Column(Text, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    user = relationship('User', back_populates='predictions')

    @property
    def contributing_factors(self):
        if not self.contributing_factors_json:
            return []
        try:
            return json.loads(self.contributing_factors_json)
        except Exception:
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'user_email': self.user.email if self.user else 'Unknown',
            'pregnancies': self.pregnancies,
            'glucose': self.glucose,
            'blood_pressure': self.blood_pressure,
            'skin_thickness': self.skin_thickness,
            'insulin': self.insulin,
            'bmi': round(self.bmi, 1),
            'diabetes_pedigree_function': round(self.diabetes_pedigree_function, 3),
            'age': self.age,
            'prediction_outcome': self.prediction_outcome,
            'probability': round(self.probability, 1),
            'risk_level': self.risk_level,
            'contributing_factors': self.contributing_factors,
            'notes': self.notes or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'formatted_date': self.created_at.strftime('%b %d, %Y - %I:%M %p')
        }


def init_db():
    """Initializes tables and seeds initial administrator & sample records if empty."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # Check if admin exists
        admin = session.query(User).filter_by(email='admin@healthguard.ai').first()
        if not admin:
            print("[*] Seeding default administrator account...")
            admin = User(
                name='HealthGuard Admin',
                email='admin@healthguard.ai',
                role='admin'
            )
            admin.set_password('Admin@12345')
            session.add(admin)
            session.commit()

        # Check if demo user exists
        demo_user = session.query(User).filter_by(email='john.doe@example.com').first()
        if not demo_user:
            print("[*] Seeding demo user account with clinical timeline...")
            demo_user = User(
                name='John Doe',
                email='john.doe@example.com',
                role='user'
            )
            demo_user.set_password('User@12345')
            session.add(demo_user)
            session.commit()

            # Seed 3 historical assessments showing a realistic health trajectory
            now = datetime.now()
            records = [
                {
                    'days_ago': 60,
                    'p': 2, 'glu': 148.0, 'bp': 86.0, 'skin': 32.0, 'ins': 140.0, 'bmi': 31.4, 'dpf': 0.58, 'age': 46,
                    'pred': 1, 'prob': 74.2, 'risk': 'High'
                },
                {
                    'days_ago': 30,
                    'p': 2, 'glu': 128.0, 'bp': 82.0, 'skin': 29.0, 'ins': 110.0, 'bmi': 29.8, 'dpf': 0.58, 'age': 46,
                    'pred': 0, 'prob': 48.6, 'risk': 'Medium'
                },
                {
                    'days_ago': 5,
                    'p': 2, 'glu': 112.0, 'bp': 78.0, 'skin': 26.0, 'ins': 85.0, 'bmi': 28.2, 'dpf': 0.58, 'age': 46,
                    'pred': 0, 'prob': 31.5, 'risk': 'Low'
                }
            ]
            for r in records:
                entry = Prediction(
                    user_id=demo_user.id,
                    pregnancies=r['p'],
                    glucose=r['glu'],
                    blood_pressure=r['bp'],
                    skin_thickness=r['skin'],
                    insulin=r['ins'],
                    bmi=r['bmi'],
                    diabetes_pedigree_function=r['dpf'],
                    age=r['age'],
                    prediction_outcome=r['pred'],
                    probability=r['prob'],
                    risk_level=r['risk'],
                    contributing_factors_json=json.dumps([
                        {'feature': 'Glucose', 'label': 'Blood Glucose', 'value': r['glu'], 'level': 'caution' if r['glu'] > 120 else 'safe'},
                        {'feature': 'BMI', 'label': 'Body Mass Index', 'value': r['bmi'], 'level': 'caution' if r['bmi'] > 29 else 'safe'}
                    ]),
                    notes='Quarterly health routine checkup',
                    created_at=now - timedelta(days=r['days_ago'])
                )
                session.add(entry)
            session.commit()
            print("[*] Database seeded successfully.")

    except Exception as e:
        session.rollback()
        print(f"[!] Error during database initialization: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    init_db()
