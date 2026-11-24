"""
Automated Test Suite for Diabetes Prediction System
"""

import os
import unittest
import json
from app import app, get_db
from database import User, Prediction

class DiabetesAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_model_files_exist(self):
        """Verify that ML model artifacts and metrics are properly saved."""
        self.assertTrue(os.path.exists('models/diabetes_model.joblib'), "Model file missing")
        self.assertTrue(os.path.exists('models/scaler.joblib'), "Scaler file missing")
        self.assertTrue(os.path.exists('models/imputer.joblib'), "Imputer file missing")
        self.assertTrue(os.path.exists('models/metrics.json'), "Metrics file missing")

    def test_public_routes(self):
        """Verify public landing page and health education routes return 200."""
        res_home = self.client.get('/')
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b'HealthGuard AI', res_home.data)

        res_edu = self.client.get('/education')
        self.assertEqual(res_edu.status_code, 200)
        self.assertIn(b'Understanding Diabetes Classifications', res_edu.data)

    def test_auth_login_demo_user(self):
        """Test logging in as demo user."""
        res = self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back, John Doe', res.data)

    def test_admin_access_control(self):
        """Test that regular user cannot access admin routes."""
        # Log in as normal user
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        }, follow_redirects=True)

        res_admin = self.client.get('/admin', follow_redirects=True)
        # Should be redirected away with access denied
        self.assertIn(b'Access denied', res_admin.data)

    def test_admin_login_and_dashboard(self):
        """Test logging in as administrator."""
        res = self.client.post('/login', data={
            'email': 'admin@healthguard.ai',
            'password': 'Admin@12345'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Clinical System Administration & Analytics', res.data)

    def test_prediction_submission_and_pdf(self):
        """Test submitting health parameters, verifying result page and PDF download with prevention protocol."""
        # Log in as demo user
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        })

        sample_data = {
            'pregnancies': 2,
            'glucose': 165,
            'blood_pressure': 88,
            'skin_thickness': 33,
            'insulin': 140,
            'bmi': 33.8,
            'diabetes_pedigree_function': 0.62,
            'age': 52,
            'notes': 'Test automated high-risk screening'
        }
        res = self.client.post('/predict', data=sample_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Clinical Screening Assessment Summary', res.data)
        self.assertIn(b'Likelihood', res.data)
        self.assertIn(b'High-Risk Diabetes Prevention Protocol', res.data)
        self.assertIn(b'Daily Prevention Habit Tracker', res.data)
        self.assertIn(b'Key Questions to Bring to Your Physician Appointment', res.data)

        # Verify record in DB
        db = get_db()
        latest_pred = db.query(Prediction).filter_by(notes='Test automated high-risk screening').order_by(Prediction.id.desc()).first()
        self.assertIsNotNone(latest_pred)
        self.assertEqual(latest_pred.glucose, 165)

        # Test PDF download
        pdf_res = self.client.get(f'/prediction/{latest_pred.id}/download-pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.content_type, 'application/pdf')
        self.assertGreater(len(pdf_res.data), 1000)

        # Test printable report
        report_res = self.client.get(f'/prediction/{latest_pred.id}/print-report')
        self.assertEqual(report_res.status_code, 200)
        self.assertIn(b'High-Risk Diabetes Prevention Protocol', report_res.data)

    def test_api_endpoints(self):
        """Test JSON REST endpoints for charts."""
        # User trends
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        })
        res_trends = self.client.get('/api/user/trends')
        self.assertEqual(res_trends.status_code, 200)
        data = json.loads(res_trends.data)
        self.assertIn('probabilities', data)
        self.assertIn('glucoses', data)

        # Logout first
        self.client.get('/logout')

        # Admin analytics
        self.client.post('/login', data={
            'email': 'admin@healthguard.ai',
            'password': 'Admin@12345'
        })
        res_admin = self.client.get('/api/admin/analytics')
        self.assertEqual(res_admin.status_code, 200)
        admin_data = json.loads(res_admin.data)
        self.assertIn('risk_distribution', admin_data)

    def test_prevention_protocol_risk_levels(self):
        """Test that predict_diabetes_risk produces appropriate prevention protocol for High, Medium, and Low risk."""
        from ml.explain import predict_diabetes_risk

        # High risk input
        high_input = {
            'Pregnancies': 4,
            'Glucose': 175,
            'BloodPressure': 92,
            'SkinThickness': 35,
            'Insulin': 210,
            'BMI': 36.2,
            'DiabetesPedigreeFunction': 0.85,
            'Age': 55
        }
        res_high = predict_diabetes_risk(high_input)
        self.assertEqual(res_high['risk_level'], 'High')
        self.assertIn('prevention_protocol', res_high)
        proto_high = res_high['prevention_protocol']
        self.assertEqual(proto_high['urgency_level'], 'High Priority')
        self.assertGreaterEqual(len(proto_high['pillars']), 5)
        self.assertGreaterEqual(len(proto_high['daily_checklist']), 5)
        self.assertGreaterEqual(len(proto_high['questions_for_doctor']), 3)
        self.assertTrue(any('Plate Method' in s for p in proto_high['pillars'] for s in p['steps']))
        self.assertTrue(any('Post-Meal Walk' in s for p in proto_high['pillars'] for s in p['steps']))

        # Low risk input
        low_input = {
            'Pregnancies': 0,
            'Glucose': 82,
            'BloodPressure': 70,
            'SkinThickness': 18,
            'Insulin': 60,
            'BMI': 21.5,
            'DiabetesPedigreeFunction': 0.15,
            'Age': 24
        }
        res_low = predict_diabetes_risk(low_input)
        self.assertEqual(res_low['risk_level'], 'Low')
        self.assertIn('prevention_protocol', res_low)
        proto_low = res_low['prevention_protocol']
        self.assertEqual(proto_low['urgency_level'], 'Wellness Maintenance')

if __name__ == '__main__':
    unittest.main()

