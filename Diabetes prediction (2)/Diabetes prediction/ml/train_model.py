"""
Machine Learning Training Pipeline for Diabetes Prediction System
Algorithm: Logistic Regression
Dataset: Pima Indians Diabetes Dataset
Features: Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age
"""

import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# Define file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'ml', 'dataset.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'diabetes_model.joblib')
SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.joblib')
IMPUTER_PATH = os.path.join(MODELS_DIR, 'imputer.joblib')
METRICS_PATH = os.path.join(MODELS_DIR, 'metrics.json')

FEATURE_NAMES = [
    'Pregnancies',
    'Glucose',
    'BloodPressure',
    'SkinThickness',
    'Insulin',
    'BMI',
    'DiabetesPedigreeFunction',
    'Age'
]

# Columns where zero indicates a missing/unrecorded biological measurement
ZERO_AS_MISSING_COLS = ['Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI']

def train_and_evaluate():
    os.makedirs(MODELS_DIR, exist_ok=True)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    print(f"[*] Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)

    X = df[FEATURE_NAMES].copy()
    y = df['Outcome'].copy()

    # Preprocessing: Replace zeros with NaN for biological markers that cannot physiologically be zero
    X_impute_input = X.copy()
    for col in ZERO_AS_MISSING_COLS:
        X_impute_input[col] = X_impute_input[col].replace(0, np.nan)

    # Train-test split (Stratified 80/20 to preserve diabetes class ratio)
    X_train, X_test, y_train, y_test = train_test_split(
        X_impute_input, y, test_size=0.20, random_state=42, stratify=y
    )

    # Fit median imputer on training set only to prevent data leakage
    imputer = SimpleImputer(strategy='median')
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    # Feature Scaling with StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_imputed)
    X_test_scaled = scaler.transform(X_test_imputed)

    # Train Logistic Regression Model
    print("[*] Training Logistic Regression model...")
    model = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=42,
        solver='lbfgs',
        class_weight='balanced'
    )
    model.fit(X_train_scaled, y_train)

    # Predictions & Evaluation on Test Set
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred))
    recall = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    # Compute ROC curve points for dashboard visualization
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    # Downsample points for neat JSON transmission
    step = max(1, len(fpr) // 20)
    roc_points = [
        {"fpr": round(float(f), 4), "tpr": round(float(t), 4)}
        for f, t in zip(fpr[::step], tpr[::step])
    ]
    if roc_points[-1]["fpr"] != 1.0 or roc_points[-1]["tpr"] != 1.0:
        roc_points.append({"fpr": 1.0, "tpr": 1.0})

    # Feature Importance (Coefficients & Odds Ratios)
    coefficients = model.coef_[0].tolist()
    odds_ratios = np.exp(model.coef_[0]).tolist()
    feature_importance = []
    for name, coef, odds in zip(FEATURE_NAMES, coefficients, odds_ratios):
        feature_importance.append({
            "feature": name,
            "coefficient": round(float(coef), 4),
            "odds_ratio": round(float(odds), 4),
            "abs_impact": round(float(abs(coef)), 4)
        })
    feature_importance.sort(key=lambda x: x["abs_impact"], reverse=True)

    # Imputer statistics (for reference & client-side guidance)
    feature_medians = {
        name: round(float(med), 2)
        for name, med in zip(FEATURE_NAMES, imputer.statistics_)
    }

    metrics = {
        "model_name": "Logistic Regression",
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_records": int(len(df)),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
            "matrix": [[tn, fp], [fn, tp]]
        },
        "feature_importance": feature_importance,
        "feature_medians": feature_medians,
        "roc_curve": roc_points,
        "intercept": round(float(model.intercept_[0]), 4)
    }

    # Save artifacts
    print(f"[*] Saving model to {MODEL_PATH}...")
    joblib.dump(model, MODEL_PATH)

    print(f"[*] Saving scaler to {SCALER_PATH}...")
    joblib.dump(scaler, SCALER_PATH)

    print(f"[*] Saving imputer to {IMPUTER_PATH}...")
    joblib.dump(imputer, IMPUTER_PATH)

    print(f"[*] Saving metrics to {METRICS_PATH}...")
    with open(METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print("\n==========================================")
    print(" MODEL TRAINING & EVALUATION COMPLETED")
    print("==========================================")
    print(f" Accuracy : {accuracy * 100:.2f}%")
    print(f" Precision: {precision * 100:.2f}%")
    print(f" Recall   : {recall * 100:.2f}%")
    print(f" F1-Score : {f1 * 100:.2f}%")
    print(f" ROC-AUC  : {roc_auc:.4f}")
    print(f" Confusion Matrix:\n   TN={tn}  FP={fp}\n   FN={fn}  TP={tp}")
    print("==========================================\n")
    return metrics

if __name__ == '__main__':
    train_and_evaluate()
