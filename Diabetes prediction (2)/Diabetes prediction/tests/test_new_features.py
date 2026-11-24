"""
Tests for New Features:
1. 🌐 Tamil + English Health Assistant
2. 📸 Health Report Scanner (OCR)
3. 🚦 Risk Change Alert
4. 🧩 Diabetes Risk Factor Map (YOUR RISK PROFILE)
"""

import unittest
import json
from app import app, get_db
from database import User, Prediction
from ocr_service import parse_clinical_values
from ml.explain import generate_risk_profile_map, predict_diabetes_risk

class NewFeaturesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_ocr_service_parsing(self):
        """Test parsing clinical report texts for glucose, blood pressure, BMI, age."""
        sample_report = """
        METABOLIC PROFILE & LAB ASSESSMENT
        Patient Name: Jane Doe    Age: 48 Yrs
        Fasting Blood Sugar (FBS): 142.5 mg/dL
        Blood Pressure (BP): 135/86 mmHg
        BMI: 29.4 kg/m2
        Serum Insulin: 110 uU/mL
        Triceps Skinfold: 28 mm
        Pregnancies: 3
        Diabetes Pedigree Function: 0.55
        """
        parsed = parse_clinical_values(sample_report)
        extracted = parsed['extracted']
        self.assertIn('glucose', extracted)
        self.assertEqual(extracted['glucose']['value'], 142.5)
        self.assertIn('blood_pressure', extracted)
        self.assertEqual(extracted['blood_pressure']['value'], 86.0)
        self.assertIn('bmi', extracted)
        self.assertEqual(extracted['bmi']['value'], 29.4)
        self.assertIn('age', extracted)
        self.assertEqual(extracted['age']['value'], 48)
        self.assertIn('insulin', extracted)
        self.assertEqual(extracted['insulin']['value'], 110.0)

    def test_risk_profile_map_generation(self):
        """Test YOUR RISK PROFILE ASCII bar and impact calculation."""
        inputs = {
            'Glucose': 165.0,
            'BMI': 33.8,
            'Age': 52,
            'BloodPressure': 88,
            'Insulin': 140,
            'DiabetesPedigreeFunction': 0.62
        }
        factor_map = generate_risk_profile_map(inputs, 78.5)
        self.assertTrue(len(factor_map) >= 5)
        
        # Verify Glucose is top impact factor
        glucose_item = next(f for f in factor_map if f['name'] == 'Glucose')
        self.assertIn('High impact', glucose_item['impact'])
        self.assertIn('█', glucose_item['bar_str'])
        self.assertEqual(len(glucose_item['bar_str']), 10)

        # Verify BMI is high/moderate
        bmi_item = next(f for f in factor_map if f['name'] == 'BMI')
        self.assertTrue(bmi_item['blocks'] >= 7)

    def test_risk_change_alert_flow(self):
        """Test that submitting sequential predictions computes the probability comparison."""
        # 1. Log in
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        })

        # 2. First screening (e.g. moderate risk)
        res1 = self.client.post('/predict', data={
            'pregnancies': 1,
            'glucose': 110,
            'blood_pressure': 76,
            'skin_thickness': 22,
            'insulin': 80,
            'bmi': 25.5,
            'diabetes_pedigree_function': 0.35,
            'age': 38,
            'notes': 'Initial baseline screening'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)

        # 3. Second screening (elevated risk)
        res2 = self.client.post('/predict', data={
            'pregnancies': 1,
            'glucose': 175,
            'blood_pressure': 92,
            'skin_thickness': 32,
            'insulin': 160,
            'bmi': 34.2,
            'diabetes_pedigree_function': 0.75,
            'age': 40,
            'notes': 'Followup changed screening'
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)

        # Assert Risk Change Alert rendered
        self.assertIn(b'Biometric Trajectory Comparison', res2.data)
        self.assertIn(b'Previous prediction:', res2.data)
        self.assertIn(b'Current prediction:', res2.data)
        self.assertIn(b'Prediction probability changed', res2.data)
        self.assertIn(b'Clinical Guidance:', res2.data)

        # Assert YOUR RISK PROFILE rendered
        self.assertIn(b'YOUR RISK PROFILE', res2.data)
        self.assertIn(b'High impact', res2.data)

    def test_api_scan_report_endpoint(self):
        """Test the /api/scan-report endpoint with JSON raw text."""
        self.client.post('/login', data={
            'email': 'john.doe@example.com',
            'password': 'User@12345'
        })

        payload = {
            'text': 'CLINICAL LAB REPORT\nFasting Glucose: 138 mg/dL\nBP: 120/82\nBMI: 28.5'
        }
        res = self.client.post('/api/scan-report', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        extracted = data['data']['extracted']
        self.assertIn('glucose', extracted)
        self.assertEqual(extracted['glucose']['value'], 138.0)
        self.assertEqual(extracted['blood_pressure']['value'], 82.0)

    def test_bilingual_assistant_presence_in_base(self):
        """Verify that the Tamil + English Health Assistant elements exist in rendered pages."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Health Assistant', res.data)
        self.assertIn('நல உதவியாளர்'.encode('utf-8'), res.data)
        self.assertIn(b'What is BMI?', res.data)
        self.assertIn(b'What does glucose mean?', res.data)
        self.assertIn(b'What does my prediction result mean?', res.data)

if __name__ == '__main__':
    unittest.main()
