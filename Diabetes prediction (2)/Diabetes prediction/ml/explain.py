"""
Clinical Parameter Analysis and Explainability Engine for Diabetes Screening
Provides reference range checks, risk categorization, contributing factor ranking,
and tailored educational guidance.
"""

import json
import os
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'diabetes_model.joblib')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.joblib')
IMPUTER_PATH = os.path.join(MODELS_DIR, 'imputer.joblib')

FEATURE_ORDER = [
    'Pregnancies',
    'Glucose',
    'BloodPressure',
    'SkinThickness',
    'Insulin',
    'BMI',
    'DiabetesPedigreeFunction',
    'Age'
]

# Standard Clinical Reference Guidelines
CLINICAL_STANDARDS = {
    'Pregnancies': {
        'unit': 'count',
        'label': 'Pregnancies',
        'normal_min': 0,
        'normal_max': 3,
        'description': 'History of pregnancies is associated with gestational metabolic changes.'
    },
    'Glucose': {
        'unit': 'mg/dL',
        'label': 'Plasma Glucose Concentration',
        'normal_min': 70,
        'normal_max': 99,
        'prediabetes_max': 125,
        'description': 'Fasting plasma glucose. 70-99 mg/dL is normal; 100-125 mg/dL indicates prediabetes; ≥126 mg/dL warrants clinical diagnostic review.'
    },
    'BloodPressure': {
        'unit': 'mm Hg',
        'label': 'Diastolic Blood Pressure',
        'normal_min': 60,
        'normal_max': 80,
        'description': 'Diastolic arterial pressure. Under 80 mm Hg is optimal; 80-89 mm Hg is elevated; ≥90 mm Hg indicates hypertension.'
    },
    'SkinThickness': {
        'unit': 'mm',
        'label': 'Triceps Skinfold Thickness',
        'normal_min': 10,
        'normal_max': 25,
        'description': 'Surrogate measure of body fat distribution and subcutaneous adipose tissue.'
    },
    'Insulin': {
        'unit': 'μU/mL',
        'label': '2-Hour Serum Insulin',
        'normal_min': 16,
        'normal_max': 166,
        'description': 'Post-load circulating serum insulin. Elevated values (>166 μU/mL) frequently reflect systemic insulin resistance.'
    },
    'BMI': {
        'unit': 'kg/m²',
        'label': 'Body Mass Index (BMI)',
        'normal_min': 18.5,
        'normal_max': 24.9,
        'description': 'Weight-to-height ratio. 18.5-24.9 is normal; 25.0-29.9 is overweight; ≥30.0 indicates obesity (a leading diabetes risk factor).'
    },
    'DiabetesPedigreeFunction': {
        'unit': 'score',
        'label': 'Diabetes Pedigree Function',
        'normal_min': 0.08,
        'normal_max': 0.45,
        'description': 'Quantitative genetic score reflecting diabetes incidence in ancestral family medical history.'
    },
    'Age': {
        'unit': 'years',
        'label': 'Age',
        'normal_min': 18,
        'normal_max': 44,
        'description': 'Age in years. Type 2 diabetes risk significantly increases after 45 years due to accumulated metabolic factors.'
    }
}

_model = None
_scaler = None
_imputer = None

def get_ml_pipeline():
    global _model, _scaler, _imputer
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        _imputer = joblib.load(IMPUTER_PATH)
    return _model, _scaler, _imputer

def assess_bmi(bmi):
    """Categorize BMI according to WHO international classifications."""
    if bmi < 18.5:
        return {'category': 'Underweight', 'badge': 'warning', 'color': '#3b82f6', 'advice': 'Consult a nutritionist regarding balanced caloric and nutrient intake.'}
    elif 18.5 <= bmi <= 24.9:
        return {'category': 'Normal Weight', 'badge': 'safe', 'color': '#10b981', 'advice': 'Healthy weight range. Continue regular physical activity and balanced nutrition.'}
    elif 25.0 <= bmi <= 29.9:
        return {'category': 'Overweight', 'badge': 'caution', 'color': '#f59e0b', 'advice': 'Modest weight reduction (5-7%) can substantially reduce future diabetes risk.'}
    elif 30.0 <= bmi <= 34.9:
        return {'category': 'Obese (Class I)', 'badge': 'danger', 'color': '#ef4444', 'advice': 'Strong risk factor for metabolic syndrome. Prioritize medical and dietary consultation.'}
    else:
        return {'category': 'Severely Obese (Class II/III)', 'badge': 'danger', 'color': '#b91c1c', 'advice': 'Comprehensive clinical metabolic evaluation strongly recommended.'}

def analyze_parameters(user_inputs):
    """
    Compare input parameters to clinical standards, evaluating status and severity.
    """
    factors = []
    
    # 1. Glucose
    glucose = user_inputs.get('Glucose', 0)
    if glucose < 70 and glucose > 0:
        status, level = 'Low (Hypoglycemic tendency)', 'warning'
        comment = 'Glucose below typical fasting levels.'
    elif glucose <= 99:
        status, level = 'Normal Fasting Range', 'safe'
        comment = 'Optimal fasting blood sugar level (70-99 mg/dL).'
    elif glucose <= 125:
        status, level = 'Borderline / Prediabetes Alert', 'caution'
        comment = 'Fasting glucose between 100-125 mg/dL indicates impaired fasting glucose (Prediabetes).'
    else:
        status, level = 'Significantly Elevated', 'danger'
        comment = 'Glucose is ≥126 mg/dL. Primary clinical marker correlated with diabetes mellitus.'
    factors.append({
        'feature': 'Glucose',
        'label': 'Blood Glucose',
        'value': glucose,
        'unit': 'mg/dL',
        'status': status,
        'level': level,
        'normal_range': '70 – 99 mg/dL',
        'comment': comment
    })

    # 2. BMI
    bmi = user_inputs.get('BMI', 0)
    bmi_info = assess_bmi(bmi)
    level = 'safe' if bmi_info['badge'] == 'safe' else ('caution' if bmi_info['badge'] == 'caution' else 'danger')
    factors.append({
        'feature': 'BMI',
        'label': 'Body Mass Index',
        'value': round(bmi, 1),
        'unit': 'kg/m²',
        'status': bmi_info['category'],
        'level': level,
        'normal_range': '18.5 – 24.9 kg/m²',
        'comment': bmi_info['advice']
    })

    # 3. Blood Pressure
    bp = user_inputs.get('BloodPressure', 0)
    if bp == 0:
        status, level = 'Not recorded / Imputed', 'neutral'
        comment = 'Diastolic pressure missing; statistical median applied in model.'
    elif bp < 80:
        status, level = 'Optimal Diastolic', 'safe'
        comment = 'Diastolic blood pressure is within optimal cardiac limits (<80 mm Hg).'
    elif bp <= 89:
        status, level = 'Prehypertension (Elevated)', 'caution'
        comment = 'Diastolic blood pressure is borderline elevated (80-89 mm Hg).'
    else:
        status, level = 'Hypertension Alert', 'danger'
        comment = 'Diastolic BP is ≥90 mm Hg. Elevated blood pressure correlates with cardiovascular and metabolic strain.'
    factors.append({
        'feature': 'BloodPressure',
        'label': 'Diastolic Blood Pressure',
        'value': bp,
        'unit': 'mm Hg',
        'status': status,
        'level': level,
        'normal_range': '60 – 80 mm Hg',
        'comment': comment
    })

    # 4. Insulin
    ins = user_inputs.get('Insulin', 0)
    if ins == 0:
        status, level = 'Not recorded / Imputed', 'neutral'
        comment = '2-hour insulin not recorded; model applied population median.'
    elif ins < 166:
        status, level = 'Normal Range', 'safe'
        comment = 'Insulin levels within expected metabolic response parameters.'
    else:
        status, level = 'Elevated (Hyperinsulinemia)', 'caution'
        comment = 'Elevated serum insulin may reflect pancreatic compensatory response to cellular insulin resistance.'
    factors.append({
        'feature': 'Insulin',
        'label': 'Serum Insulin (2-Hour)',
        'value': ins,
        'unit': 'μU/mL',
        'status': status,
        'level': level,
        'normal_range': '16 – 166 μU/mL',
        'comment': comment
    })

    # 5. Diabetes Pedigree Function
    dpf = user_inputs.get('DiabetesPedigreeFunction', 0)
    if dpf < 0.35:
        status, level = 'Low Genetic Score', 'safe'
        comment = 'Lower estimated familial genetic predisposition.'
    elif dpf <= 0.65:
        status, level = 'Moderate Genetic Score', 'caution'
        comment = 'Moderate familial prevalence of diabetes reported.'
    else:
        status, level = 'High Family Predisposition', 'danger'
        comment = 'Higher genetic score indicates familial clusters of diabetes.'
    factors.append({
        'feature': 'DiabetesPedigreeFunction',
        'label': 'Diabetes Pedigree Function',
        'value': round(dpf, 3),
        'unit': 'score',
        'status': status,
        'level': level,
        'normal_range': '0.08 – 0.45',
        'comment': comment
    })

    # 6. Age
    age = user_inputs.get('Age', 0)
    if age < 35:
        status, level = 'Young Adult (Lower Age Risk)', 'safe'
        comment = 'Younger age group has lower baseline epidemiological incidence.'
    elif age <= 45:
        status, level = 'Middle Adult (Screening Advised)', 'caution'
        comment = 'General clinical guidelines advise baseline screening starting at age 35–45.'
    else:
        status, level = 'Mature Adult (Elevated Age Risk)', 'danger'
        comment = 'Metabolic risk factors and insulin resistance prevalence increase with age.'
    factors.append({
        'feature': 'Age',
        'label': 'Age',
        'value': int(age),
        'unit': 'years',
        'status': status,
        'level': level,
        'normal_range': '18 – 44 years',
        'comment': comment
    })

    # 7. Pregnancies
    preg = user_inputs.get('Pregnancies', 0)
    factors.append({
        'feature': 'Pregnancies',
        'label': 'Pregnancies',
        'value': int(preg),
        'unit': 'count',
        'status': 'Elevated Gestational History' if preg >= 4 else 'Low / Moderate',
        'level': 'caution' if preg >= 4 else 'safe',
        'normal_range': '0 – 3',
        'comment': 'Multiparity may influence gestational glucose tolerance history.'
    })

    # 8. Skin Thickness
    skin = user_inputs.get('SkinThickness', 0)
    factors.append({
        'feature': 'SkinThickness',
        'label': 'Triceps Skinfold',
        'value': skin,
        'unit': 'mm',
        'status': 'Elevated Adiposity' if skin > 30 else 'Typical',
        'level': 'caution' if skin > 30 else 'safe',
        'normal_range': '10 – 25 mm',
        'comment': 'Subcutaneous body fat marker.'
    })

    return factors

def generate_recommendations(risk_level, factors, user_inputs):
    """
    Produce structured, non-prescriptive lifestyle and clinical guidance.
    """
    recs = []
    
    # Always include clinical consultation reminder
    recs.append({
        'title': 'Consult a Licensed Healthcare Professional',
        'type': 'medical',
        'icon': 'stethoscope',
        'text': 'This screening tool is purely informational. Schedule a formal appointment with a physician to evaluate fasting blood glucose, HbA1c (glycated hemoglobin), and a comprehensive metabolic panel.'
    })

    glucose = user_inputs.get('Glucose', 0)
    if glucose >= 100:
        recs.append({
            'title': 'Glycemic Monitoring & Dietary Awareness',
            'type': 'nutrition',
            'icon': 'apple-whole',
            'text': 'Your entered glucose is elevated. Focus on low glycemic index (GI) whole foods, fiber-rich legumes, leafy vegetables, and minimize ultra-processed carbohydrates and sugary beverages.'
        })

    bmi = user_inputs.get('BMI', 0)
    if bmi >= 25:
        recs.append({
            'title': 'Targeted Weight & Physical Activity Strategy',
            'type': 'fitness',
            'icon': 'person-running',
            'text': 'Clinical studies (like the Diabetes Prevention Program) demonstrate that losing 5% to 7% of total body weight combined with 150 minutes per week of brisk walking reduces type 2 diabetes risk by up to 58%.'
        })
    else:
        recs.append({
            'title': 'Sustain Active Physical Conditioning',
            'type': 'fitness',
            'icon': 'heart-pulse',
            'text': 'Engage in at least 150 minutes of moderate-intensity aerobic exercise weekly (e.g., swimming, cycling, or jogging) alongside resistance training twice a week to promote insulin receptor sensitivity.'
        })

    bp = user_inputs.get('BloodPressure', 0)
    if bp >= 85:
        recs.append({
            'title': 'Cardiovascular & Blood Pressure Care',
            'type': 'health',
            'icon': 'shield-heart',
            'text': 'Maintain lower dietary sodium intake (<2,300 mg/day), manage daily mental stress through mindfulness or restorative sleep, and have your resting blood pressure rechecked.'
        })

    dpf = user_inputs.get('DiabetesPedigreeFunction', 0)
    if dpf > 0.5:
        recs.append({
            'title': 'Proactive Family History Surveillance',
            'type': 'prevention',
            'icon': 'dna',
            'text': 'With an elevated family history score, routine annual laboratory screenings (HbA1c tests) are strongly recommended even if you are currently asymptomatic.'
        })

    return recs

def generate_prevention_protocol(risk_level, factors, user_inputs):
    """
    Produce an evidence-based, actionable diabetes prevention plan
    tailored to clinical risk stratification (especially for High Risk).
    """
    glucose = float(user_inputs.get('Glucose', 0))
    bmi = float(user_inputs.get('BMI', 0))
    bp = float(user_inputs.get('BloodPressure', 0))
    dpf = float(user_inputs.get('DiabetesPedigreeFunction', 0))
    age = float(user_inputs.get('Age', 0))

    # Calculate 5-7% weight reduction targets if BMI is elevated
    weight_target_note = ""
    if bmi >= 25.0:
        weight_target_note = "Losing just 5% to 7% of current body weight has been proven to lower diabetes progression risk by 58%."

    if risk_level == 'High':
        alert_title = "High-Risk Diabetes Prevention Protocol & Action Plan"
        alert_subtitle = (
            "Your screening score is in the high/critical range. Don't panic — taking action right now "
            "with simple food changes, daily walking, and a doctor visit can strongly lower your blood sugar and protect your health."
        )
        urgency_level = "High Priority"

        simple_guide = {
            'condition_label': 'Critical / High Risk',
            'theme': 'danger',
            'simple_headline': 'Your diabetes risk is high — active blood sugar control is needed now.',
            'simple_explanation': (
                f'Your screening markers (such as blood sugar of {glucose:.0f} mg/dL and BMI of {bmi:.1f}) '
                'are noticeably above healthy limits. This is a screening warning — not a final diagnosis — '
                'so please visit a doctor soon for a lab test and start strict food and activity control today.'
            ),
            'foods_to_eat': [
                'Green leafy vegetables (spinach, methi, broccoli, cabbage, bitter gourd / karela) — fill half your plate',
                'Whole grains & millets in small portions (oats, ragi, barley, brown rice, broken wheat)',
                'Lean protein at every meal (moong dal, chickpeas, boiled eggs, grilled fish, chicken, tofu, paneer)',
                'Fiber-rich seeds & nuts (soaked almonds, walnuts, flaxseeds, chia seeds, fenugreek/methi water)',
                'Low-sugar whole fruits in small portions (guava, apple, papaya, berries — never juice)',
                'Plain water (8–10 glasses/day), buttermilk, or unsweetened green/herbal tea'
            ],
            'foods_to_avoid': [
                'All sugary drinks: soft drinks, packaged fruit juices, energy drinks, sweet tea/coffee',
                'Refined white carbs: large plates of white rice, white bread, maida, parotta, noodles',
                'Sweets & bakery foods: cakes, pastries, biscuits, chocolates, ice cream, jam',
                'Deep-fried & fast food: samosas, chips, fries, burgers, heavy oily curries',
                'Late-night heavy dinners and high-salt packaged snacks'
            ],
            'sample_meal_plan': [
                {'meal': 'Breakfast', 'menu': 'Vegetable oats / ragi dosa / 2 boiled eggs + green tea (no sugar)'},
                {'meal': 'Lunch', 'menu': 'Half plate green veggies + dal/fish/chicken + 1 small bowl brown rice or 2 multigrain rotis'},
                {'meal': 'Snack', 'menu': 'Handful of roasted chana / 5–6 almonds / cucumber or guava slices'},
                {'meal': 'Dinner', 'menu': 'Light & early (2 hrs before sleep): vegetable soup + grilled paneer/tofu or 2 phulkas + sabzi'}
            ],
            'control_title': 'How to Control Critical / High Risk — What to Do Right Now',
            'control_steps': [
                {
                    'title': '1. See a Doctor Within 1–2 Weeks',
                    'detail': 'Ask for an HbA1c test and Fasting Blood Sugar test to confirm your exact sugar level and check if medication is needed.'
                },
                {
                    'title': '2. Cut Out Sugar & Use the 50/25/25 Plate Rule',
                    'detail': 'Stop all sugary drinks immediately. Fill 50% of your plate with vegetables, 25% with protein, and 25% with whole grains.'
                },
                {
                    'title': '3. Walk 10–15 Minutes After Every Meal',
                    'detail': 'A gentle walk after breakfast, lunch, and dinner quickly clears excess sugar from your blood.'
                },
                {
                    'title': '4. Track Sugar, Blood Pressure & Weight Weekly',
                    'detail': 'Monitor your numbers regularly. Losing just 5–7% of body weight (if overweight) cuts diabetes risk by over half.'
                },
                {
                    'title': '5. Sleep 7–8 Hours & Stay Stress-Free',
                    'detail': 'Poor sleep and high stress make blood sugar spike even without eating sweets. Avoid smoking and alcohol.'
                }
            ],
            'warning_signs': [
                'Frequent urination (especially waking up at night)',
                'Extreme thirst or dry mouth all the time',
                'Sudden blurred vision or frequent headaches',
                'Unusual tiredness, dizziness, or tingling in hands/feet',
                'Cuts or wounds that heal very slowly'
            ]
        }

        pillars = [
            {
                'id': 'medical',
                'title': '1. Doctor Visit & Blood Tests',
                'icon': 'user-doctor',
                'badge': 'Urgent Priority',
                'badge_class': 'danger',
                'summary': 'Confirm your screening result with simple lab tests from a doctor.',
                'steps': [
                    'Book an appointment with a doctor within 1–2 weeks.',
                    'Ask for Fasting Blood Sugar (FPG) and HbA1c (3-month average sugar) lab tests.',
                    'Check your blood pressure, cholesterol, and kidney health as well.',
                    'Ask your doctor if you need a diet plan or preventive medicine.'
                ]
            },
            {
                'id': 'nutrition',
                'title': '2. Daily Food Control (What to Eat & Avoid)',
                'icon': 'utensils',
                'badge': 'High Impact',
                'badge_class': 'danger',
                'summary': 'Simple meal swaps keep your blood sugar steady all day.',
                'steps': [
                    'Use the simple 50/25/25 Plate Method: 50% green vegetables, 25% protein (dal, eggs, fish, chicken, tofu), 25% whole grains.',
                    'Stop all liquid sugar: avoid sodas, fruit juices, sweet tea, and sweet coffee. Drink plain water instead.',
                    'Swap white rice, white bread, and maida for oats, millets (ragi/jowar), brown rice, or lentils.',
                    'Eat more fiber every day: leafy greens, beans, chia/flax seeds, and whole low-sugar fruits.'
                ]
            },
            {
                'id': 'exercise',
                'title': '3. Daily Walking & Exercise Control',
                'icon': 'person-running',
                'badge': '58% Risk Drop',
                'badge_class': 'danger',
                'summary': 'Moving your muscles uses up extra blood sugar naturally.',
                'steps': [
                    'Walk briskly, cycle, or swim for 30 minutes at least 5 days a week.',
                    'Follow the 10–15 Minute Post-Meal Walk rule: take a light walk after lunch and dinner to stop sugar spikes.',
                    'Do light strength exercises (squats, push-ups, light weights) 2 times a week.',
                    'Avoid sitting continuously — stand and stretch for 2 minutes every 30 minutes.'
                ]
            },
            {
                'id': 'weight',
                'title': '4. Healthy Weight Control',
                'icon': 'weight-scale',
                'badge': '5%–7% Target',
                'badge_class': 'caution',
                'summary': 'Losing even a small amount of weight makes insulin work much better.',
                'steps': [
                    'Aim to lose 5% to 7% of your weight if overweight (for example, 4–5 kg if you weigh 80 kg).',
                    'Eat dinner at least 2 hours before sleeping and keep portions moderate.',
                    'Avoid crash diets — steady weekly loss of 0.5 kg is safest and lasts longest.'
                ]
            },
            {
                'id': 'lifestyle',
                'title': '5. Sleep, Stress & Regular Monitoring',
                'icon': 'bed-pulse',
                'badge': 'Daily Support',
                'badge_class': 'caution',
                'summary': 'Good sleep and calm habits keep blood sugar hormones balanced.',
                'steps': [
                    'Sleep 7–8 hours every night — sleeping under 6 hours raises morning blood sugar.',
                    'Spend 10 minutes daily on deep breathing, prayer, or calm relaxation to lower stress.',
                    'Keep a weekly log of your blood sugar (if advised by your doctor) and blood pressure.',
                    'Avoid smoking and limit or avoid alcohol completely.'
                ]
            }
        ]

        daily_checklist = [
            {'task': 'Avoid all sugary drinks; drink 8+ glasses of plain water today.', 'category': 'nutrition'},
            {'task': 'Take a 10–15 minute walk after lunch or dinner.', 'category': 'exercise'},
            {'task': 'Fill half your lunch and dinner plate with vegetables.', 'category': 'nutrition'},
            {'task': 'Complete at least 30 minutes of brisk walking or exercise.', 'category': 'exercise'},
            {'task': 'Choose whole grains/millets/dal instead of white rice or white bread.', 'category': 'nutrition'},
            {'task': 'Get 7–8 hours of good sleep tonight.', 'category': 'lifestyle'}
        ]

        questions_for_doctor = [
            "What is my current HbA1c percentage and fasting blood sugar level?",
            "Am I in the prediabetes or diabetes range based on lab tests?",
            "What daily food and exercise plan is safest for me?",
            "Do I need any medication or home blood sugar monitor right now?",
            "When should I come back for my next follow-up test?"
        ]

    elif risk_level == 'Medium':
        alert_title = "Moderate Risk Prevention & Early Intervention Strategy"
        alert_subtitle = (
            "Your numbers are in the borderline / warning zone. The good news is that simple food and walking "
            "habits right now can bring your blood sugar back to normal and prevent diabetes."
        )
        urgency_level = "Proactive Intervention"

        simple_guide = {
            'condition_label': 'Moderate / Borderline Risk',
            'theme': 'caution',
            'simple_headline': 'Early warning: Your risk is moderate, and you can still reverse it easily.',
            'simple_explanation': (
                f'Some of your health markers (such as glucose of {glucose:.0f} mg/dL or BMI of {bmi:.1f}) '
                'are slightly above the ideal range. Acting early with smarter meal choices and 30 minutes of daily walking '
                'can stop this from turning into high risk.'
            ),
            'foods_to_eat': [
                'Fresh green vegetables, salads, and high-fiber beans/lentils every day',
                'Whole grains: oats, ragi, brown rice, whole wheat roti, quinoa',
                'Healthy proteins: dal, chickpeas, eggs, fish, lean chicken, curd/yogurt',
                'Whole fruits in moderation (apple, guava, orange, berries)',
                'Healthy fats in small amounts: almonds, walnuts, flaxseeds, olive/mustard oil',
                'Plain water, lemon water, coconut water (occasionally), unsweetened tea'
            ],
            'foods_to_avoid': [
                'Sugary sodas, packaged juices, and sweetened milkshakes',
                'Excess white rice, white bread, maida snacks, and instant noodles',
                'Frequent sweets, chocolates, cakes, and bakery biscuits',
                'Fried street snacks, chips, and heavy late-night meals',
                'Skipping breakfast and overeating at dinner'
            ],
            'sample_meal_plan': [
                {'meal': 'Breakfast', 'menu': 'Oats / idli with sambar / whole-wheat toast + 1 boiled egg or sprouts'},
                {'meal': 'Lunch', 'menu': 'Salad + vegetable sabzi + dal/curd + 2 rotis or moderate brown/hand-pounded rice'},
                {'meal': 'Snack', 'menu': '1 whole fruit (apple/guava) + handful of roasted nuts or makhana'},
                {'meal': 'Dinner', 'menu': 'Light homemade meal: dal khichdi / 2 rotis + veggies + bowl of soup'}
            ],
            'control_title': 'How to Control Moderate Risk — Steps to Bring It Back to Normal',
            'control_steps': [
                {
                    'title': '1. Get a Routine Blood Test Soon',
                    'detail': 'Schedule a basic Fasting Blood Sugar and HbA1c test within the next 1–3 months to know your exact baseline.'
                },
                {
                    'title': '2. Cut Down Sugar & Refined Carbs',
                    'detail': 'Reduce sugar in tea/coffee, skip cold drinks, and replace half your white rice/bread with vegetables and dal.'
                },
                {
                    'title': '3. Walk 30 Minutes a Day (5 Days a Week)',
                    'detail': 'Daily brisk walking plus a 10-minute stroll after dinner keeps blood sugar steady.'
                },
                {
                    'title': '4. Watch Portion Sizes & Weight',
                    'detail': 'If overweight, losing just 3–5 kg gradually makes a huge difference in lowering diabetes risk.'
                },
                {
                    'title': '5. Keep Consistent Meal & Sleep Times',
                    'detail': 'Eat meals on time, avoid late-night snacking, and sleep 7–8 hours every night.'
                }
            ],
            'warning_signs': []
        }

        pillars = [
            {
                'id': 'medical',
                'title': '1. Routine Checkup & Blood Test',
                'icon': 'user-doctor',
                'badge': 'Screening Advised',
                'badge_class': 'caution',
                'summary': 'Check your exact blood sugar baseline with your doctor.',
                'steps': [
                    'Schedule a routine checkup within the next 1–3 months.',
                    'Ask for Fasting Blood Sugar and HbA1c lab tests.',
                    'Check your blood pressure and cholesterol at the same visit.'
                ]
            },
            {
                'id': 'nutrition',
                'title': '2. Smart Everyday Food Choices',
                'icon': 'utensils',
                'badge': 'Core Habit',
                'badge_class': 'caution',
                'summary': 'Eat more vegetables, dal, and whole grains; cut back on sugar.',
                'steps': [
                    'Choose low-sugar, high-fiber foods: dal, chickpeas, oats, millets, and green veggies.',
                    'Cut down on bakery snacks, sweets, chips, and sugary beverages.',
                    'Eat meals on time and avoid heavy late-night dinners.'
                ]
            },
            {
                'id': 'exercise',
                'title': '3. 30 Minutes Daily Walking',
                'icon': 'person-running',
                'badge': 'Active Lifestyle',
                'badge_class': 'caution',
                'summary': 'Daily movement keeps your body responsive to insulin.',
                'steps': [
                    'Walk briskly, cycle, or do yoga for 30 minutes at least 5 days a week.',
                    'Add simple strength exercises twice a week.',
                    'Take a 10-minute walk after your largest meal of the day.'
                ]
            },
            {
                'id': 'weight',
                'title': '4. Steady Healthy Weight',
                'icon': 'weight-scale',
                'badge': 'Preventative',
                'badge_class': 'safe',
                'summary': 'Prevent gradual weight gain around the waist.',
                'steps': [
                    'Aim to keep BMI between 18.5 and 24.9 kg/m².',
                    'If overweight, aim for a gentle 5% weight reduction over 3–6 months.'
                ]
            }
        ]

        daily_checklist = [
            {'task': 'Drink plain water instead of sugary drinks today.', 'category': 'nutrition'},
            {'task': 'Walk for at least 30 minutes or reach 8,000+ steps.', 'category': 'exercise'},
            {'task': 'Add vegetables or salad to both lunch and dinner.', 'category': 'nutrition'},
            {'task': 'Get 7–8 hours of restful sleep tonight.', 'category': 'lifestyle'}
        ]

        questions_for_doctor = [
            "What do my fasting blood sugar and HbA1c numbers look like?",
            "What food and exercise targets will bring my risk back to low?",
            "When should I schedule my next screening checkup?"
        ]

    else:
        alert_title = "Low Risk Maintenance & Long-Term Wellness Plan"
        alert_subtitle = (
            "Great job! Your entered health markers look healthy right now. "
            "Keep up balanced meals, regular movement, and yearly checkups to stay diabetes-free."
        )
        urgency_level = "Wellness Maintenance"

        simple_guide = {
            'condition_label': 'Normal / Low Risk',
            'theme': 'safe',
            'simple_headline': 'Good news! Your diabetes risk is currently low and healthy.',
            'simple_explanation': (
                f'Your health readings (including glucose of {glucose:.0f} mg/dL and BMI of {bmi:.1f}) '
                'are in a healthy range right now. Keep following good everyday food, exercise, and sleep habits '
                'so your risk stays low over the long term.'
            ),
            'foods_to_eat': [
                'Balanced home-cooked meals with colorful seasonal vegetables and greens',
                'Whole grains (oats, whole wheat, brown rice, millets) for steady energy',
                'Daily protein sources: dal, beans, eggs, fish, paneer, nuts, and plain curd',
                'Fresh whole fruits (1–2 servings per day)',
                'Plenty of clean drinking water (7–8 glasses daily)'
            ],
            'foods_to_avoid': [
                'Daily sugary sodas, energy drinks, and excess sugar in tea/coffee',
                'Frequent ultra-processed fast food, deep-fried snacks, and packaged sweets',
                'Regularly skipping meals or eating heavy junk food late at night'
            ],
            'sample_meal_plan': [
                {'meal': 'Breakfast', 'menu': 'Idli/dosa/poha/oats + fruit or boiled egg + milk/tea with minimal sugar'},
                {'meal': 'Lunch', 'menu': 'Balanced plate: rice or roti + dal + cooked vegetables + fresh salad/curd'},
                {'meal': 'Snack', 'menu': 'Seasonal fruit, roasted nuts, sprouts, or buttermilk'},
                {'meal': 'Dinner', 'menu': 'Light homemade meal with vegetables and protein at least 2 hours before bed'}
            ],
            'control_title': 'How to Stay Healthy — What to Keep Doing',
            'control_steps': [
                {
                    'title': '1. Keep Eating Balanced Homemade Meals',
                    'detail': 'Include vegetables, whole grains, and protein daily while keeping sweets and sodas occasional.'
                },
                {
                    'title': '2. Stay Physically Active',
                    'detail': 'Enjoy 30 minutes of walking, cycling, yoga, or sports most days of the week.'
                },
                {
                    'title': '3. Maintain Your Healthy Weight',
                    'detail': 'Check your weight monthly so small changes do not build up unnoticed.'
                },
                {
                    'title': '4. Get a Yearly Routine Checkup',
                    'detail': 'Do a simple annual blood sugar and blood pressure test (especially after age 35 or with family history).'
                },
                {
                    'title': '5. Prioritize Sleep & Hydration',
                    'detail': 'Sleep 7–8 hours per night, drink enough water, and manage daily stress.'
                }
            ],
            'warning_signs': []
        }

        pillars = [
            {
                'id': 'nutrition',
                'title': '1. Balanced Everyday Diet',
                'icon': 'apple-whole',
                'badge': 'Maintenance',
                'badge_class': 'safe',
                'summary': 'Keep eating fresh, natural, home-cooked foods.',
                'steps': [
                    'Include vegetables, whole grains, dal/lean proteins, and healthy fats every day.',
                    'Keep added sugars low and treat sodas or sweets as occasional only.'
                ]
            },
            {
                'id': 'exercise',
                'title': '2. Stay Active Weekly',
                'icon': 'heart-pulse',
                'badge': 'Maintenance',
                'badge_class': 'safe',
                'summary': 'Regular activity keeps your energy high and blood sugar healthy.',
                'steps': [
                    'Aim for 150 minutes of brisk walking, cycling, yoga, or sports each week.',
                    'Do light muscle-strengthening workouts twice a week.'
                ]
            },
            {
                'id': 'medical',
                'title': '3. Yearly Health Checkup',
                'icon': 'stethoscope',
                'badge': 'Annual',
                'badge_class': 'safe',
                'summary': 'Simple annual checks catch any changes early.',
                'steps': [
                    'Have a yearly checkup with basic blood sugar and blood pressure tests.',
                    'Re-screen sooner if your weight, diet, or family health history changes.'
                ]
            }
        ]

        daily_checklist = [
            {'task': 'Stay active with at least 30 minutes of movement today.', 'category': 'exercise'},
            {'task': 'Eat balanced meals with vegetables, fiber, and protein.', 'category': 'nutrition'},
            {'task': 'Drink plenty of water and get 7–8 hours of sleep.', 'category': 'lifestyle'}
        ]

        questions_for_doctor = [
            "Are there any risk factors I should watch based on my family history?",
            "How often should I do routine blood sugar checkups at my age?"
        ]

    # Specific personalized high-risk callouts
    personalized_alerts = []
    if glucose >= 126:
        personalized_alerts.append({
            'icon': 'droplet',
            'title': 'Critical Fasting Glucose Alert',
            'text': f'Your entered glucose level of {glucose} mg/dL is in the diagnostic range (≥126 mg/dL). Immediate medical confirmation via laboratory FPG or HbA1c is strongly advised.'
        })
    elif glucose >= 100:
        personalized_alerts.append({
            'icon': 'droplet',
            'title': 'Impaired Fasting Glucose (Prediabetes Range)',
            'text': f'Your entered glucose of {glucose} mg/dL is in the prediabetes window (100–125 mg/dL). Lifestyle modifications now can reverse this back to normal (<100 mg/dL).'
        })

    if bmi >= 30:
        personalized_alerts.append({
            'icon': 'weight-scale',
            'title': 'Adiposity & Insulin Resistance Factor',
            'text': f'A BMI of {bmi:.1f} kg/m² places high continuous demand on pancreatic beta cells. Losing 5–7% of your weight reduces insulin resistance significantly.'
        })

    if bp >= 90:
        personalized_alerts.append({
            'icon': 'heart-circle-exclamation',
            'title': 'Elevated Blood Pressure Co-Factor',
            'text': f'Diastolic pressure of {bp:.0f} mm Hg combined with elevated metabolic markers increases cardiovascular risk. Adhere to a low-sodium diet and seek medical evaluation.'
        })

    if dpf >= 0.5:
        personalized_alerts.append({
            'icon': 'dna',
            'title': 'Familial Genetic Predisposition',
            'text': f'Your family pedigree score of {dpf:.2f} indicates a familial tendency. While genetics cannot be changed, epigenetic lifestyle interventions remain exceptionally potent.'
        })

    return {
        'risk_level': risk_level,
        'urgency_level': urgency_level,
        'alert_title': alert_title,
        'alert_subtitle': alert_subtitle,
        'simple_guide': simple_guide,
        'pillars': pillars,
        'daily_checklist': daily_checklist,
        'questions_for_doctor': questions_for_doctor,
        'personalized_alerts': personalized_alerts,
        'weight_target_note': weight_target_note
    }


def predict_diabetes_risk(user_inputs):
    """
    Executes ML prediction, computes risk probability, assigns risk category,
    analyzes contributing factors, and returns structured result with prevention protocol.
    """
    model, scaler, imputer = get_ml_pipeline()

    # Build input array in correct feature sequence
    raw_vals = []
    for feat in FEATURE_ORDER:
        val = float(user_inputs.get(feat, 0.0))
        raw_vals.append(val)

    # Convert zeros to NaN for biological features
    impute_row = raw_vals.copy()
    for idx, feat in enumerate(FEATURE_ORDER):
        if feat in ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI'] and impute_row[idx] == 0:
            impute_row[idx] = np.nan

    # Impute and scale using DataFrame to preserve feature names
    df_impute = pd.DataFrame([impute_row], columns=FEATURE_ORDER)
    imputed = imputer.transform(df_impute)
    scaled = scaler.transform(imputed)

    # Logistic Regression Prediction
    raw_pred = int(model.predict(scaled)[0])
    raw_prob = float(model.predict_proba(scaled)[0][1])
    prob_pct = round(raw_prob * 100, 1)

    # Risk Category Assignment
    if prob_pct < 35.0:
        risk_level = 'Low'
        risk_class = 'safe'
        risk_desc = 'Your entered health parameters indicate a lower statistical probability of diabetes. Maintain proactive healthy habits.'
    elif prob_pct <= 65.0:
        risk_level = 'Medium'
        risk_class = 'caution'
        risk_desc = 'Borderline or elevated metabolic indicators detected. Focused lifestyle modifications and medical screening are advisable.'
    else:
        risk_level = 'High'
        risk_class = 'danger'
        risk_desc = 'Multiple clinical markers are significantly elevated. We strongly encourage scheduling a clinical assessment with a healthcare provider.'

    # Detailed parameter evaluation
    parameter_factors = analyze_parameters(user_inputs)
    bmi_assessment = assess_bmi(user_inputs.get('BMI', 0.0))
    recommendations = generate_recommendations(risk_level, parameter_factors, user_inputs)
    prevention_protocol = generate_prevention_protocol(risk_level, parameter_factors, user_inputs)
    risk_factor_map = generate_risk_profile_map(user_inputs, prob_pct)

    # Sort parameter factors by clinical concern (danger first, then caution, then safe)
    severity_order = {'danger': 0, 'caution': 1, 'warning': 2, 'safe': 3, 'neutral': 4}
    parameter_factors.sort(key=lambda x: severity_order.get(x['level'], 5))

    return {
        'prediction': raw_pred,
        'probability': prob_pct,
        'raw_probability': raw_prob,
        'risk_level': risk_level,
        'risk_class': risk_class,
        'risk_desc': risk_desc,
        'bmi_assessment': bmi_assessment,
        'parameter_factors': parameter_factors,
        'recommendations': recommendations,
        'prevention_protocol': prevention_protocol,
        'risk_factor_map': risk_factor_map
    }


def generate_risk_profile_map(user_inputs, prob_pct):
    """
    Computes visual breakdown for 'YOUR RISK PROFILE':
    Glucose          █████████░  High impact
    BMI              ███████░░░  Moderate
    Age              █████░░░░░  Moderate
    Blood Pressure   ███░░░░░░░  Lower impact
    Insulin          ██░░░░░░░░  Lower impact
    """
    factors = []

    # 1. Glucose
    glucose = float(user_inputs.get('Glucose', 0.0))
    if glucose >= 150:
        blocks = 9
        label = "High impact"
        cls = "danger"
    elif glucose >= 126:
        blocks = 8
        label = "High impact"
        cls = "danger"
    elif glucose >= 100:
        blocks = 6
        label = "Moderate"
        cls = "caution"
    elif glucose >= 70:
        blocks = 3
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"
    
    factors.append({
        'name': 'Glucose',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{glucose:.0f} mg/dL",
        'comment': "Primary clinical biomarker for glycemic regulation and cellular insulin sensitivity."
    })

    # 2. BMI
    bmi = float(user_inputs.get('BMI', 0.0))
    if bmi >= 35:
        blocks = 8
        label = "High impact"
        cls = "danger"
    elif bmi >= 30:
        blocks = 7
        label = "Moderate"
        cls = "caution"
    elif bmi >= 25:
        blocks = 5
        label = "Moderate"
        cls = "caution"
    elif bmi >= 18.5:
        blocks = 2
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"

    factors.append({
        'name': 'BMI',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{bmi:.1f} kg/m²",
        'comment': "Body mass index reflecting metabolic adiposity and peripheral insulin resistance."
    })

    # 3. Age
    age = float(user_inputs.get('Age', 0.0))
    if age >= 55:
        blocks = 6
        label = "Moderate"
        cls = "caution"
    elif age >= 40:
        blocks = 5
        label = "Moderate"
        cls = "caution"
    elif age >= 30:
        blocks = 3
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"

    factors.append({
        'name': 'Age',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{int(age)} yrs",
        'comment': "Epidemiological vulnerability co-factor associated with cumulative beta-cell strain."
    })

    # 4. Blood Pressure
    bp = float(user_inputs.get('BloodPressure', 0.0))
    if bp >= 95:
        blocks = 6
        label = "Moderate"
        cls = "caution"
    elif bp >= 85:
        blocks = 4
        label = "Moderate"
        cls = "caution"
    elif bp >= 70:
        blocks = 3
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"

    factors.append({
        'name': 'Blood Pressure',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{int(bp)} mm Hg",
        'comment': "Diastolic vascular indicator reflecting systemic arterial resistance."
    })

    # 5. Insulin
    ins = float(user_inputs.get('Insulin', 0.0))
    if ins >= 200:
        blocks = 6
        label = "Moderate"
        cls = "caution"
    elif ins >= 140:
        blocks = 4
        label = "Moderate"
        cls = "caution"
    elif ins >= 50:
        blocks = 2
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"

    factors.append({
        'name': 'Insulin',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{ins:.0f} μU/mL" if ins > 0 else "Baseline",
        'comment': "Circulating endocrine regulator of cellular glucose uptake and lipid metabolism."
    })

    # 6. Diabetes Pedigree Function (Genetics)
    dpf = float(user_inputs.get('DiabetesPedigreeFunction', 0.0))
    if dpf >= 0.7:
        blocks = 5
        label = "Moderate"
        cls = "caution"
    elif dpf >= 0.4:
        blocks = 3
        label = "Lower impact"
        cls = "safe"
    else:
        blocks = 2
        label = "Lower impact"
        cls = "safe"

    factors.append({
        'name': 'Genetic Pedigree (DPF)',
        'blocks': blocks,
        'bar_str': '█' * blocks + '░' * (10 - blocks),
        'pct': blocks * 10,
        'impact': label,
        'badge_class': cls,
        'value_str': f"{dpf:.2f}",
        'comment': "Hereditary coefficient evaluating familial diabetes clustering."
    })

    # Sort descending by blocks/impact
    factors.sort(key=lambda x: x['blocks'], reverse=True)
    return factors


