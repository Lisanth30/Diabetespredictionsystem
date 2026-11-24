"""
HealthGuard AI - Lab Report OCR & Biomarker Extraction Service
Extracts clinical parameters (Glucose, Blood Pressure, BMI, Insulin, Age, etc.)
from laboratory reports (PDF and Images) with confidence scoring.
"""

import re
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Biomarker Regex Patterns
PATTERNS = {
    'glucose': [
        r'(?:fasting\s*(?:blood\s*sugar|plasma\s*glucose|blood\s*glucose|glucose)|fbs|fpg|serum\s*glucose|glucose\s*\(?fasting\)?|glucose)\s*[:=\-]?\s*(\d{2,3}(?:\.\d+)?)',
        r'(\d{2,3}(?:\.\d+)?)\s*(?:mg\s*\/\s*d[lL]|mmol\s*\/\s*[lL])\s*(?:fasting|fbs|fpg|glucose)?',
        r'blood\s*sugar\s*[:=\-]?\s*(\d{2,3}(?:\.\d+)?)',
    ],
    'blood_pressure': [
        # Match systolic/diastolic e.g. 120/80 mmHg -> capture diastolic as second group
        r'(?:blood\s*pressure|b\.?p\.?)\s*[:=\-]?\s*(\d{2,3})\s*[\/\-]\s*(\d{2,3})',
        r'(?:diastolic\s*(?:pressure|blood\s*pressure)?|dbp)\s*[:=\-]?\s*(\d{2,3})',
        r'(\d{2,3})\s*[\/\-]\s*(\d{2,3})\s*mm\s*hg',
    ],
    'bmi': [
        r'(?:body\s*mass\s*index|bmi)\s*[:=\-]?\s*(\d{1,2}(?:\.\d+)?)',
        r'(\d{1,2}(?:\.\d+)?)\s*kg\s*\/\s*m(?:2|\^2|\u00b2)',
    ],
    'insulin': [
        r'(?:fasting\s*insulin|serum\s*insulin|insulin\s*\(?fasting\)?|insulin)\s*[:=\-]?\s*(\d{1,3}(?:\.\d+)?)',
        r'(\d{1,3}(?:\.\d+)?)\s*(?:\u03bc[uU]\s*\/\s*m[lL]|u[iI][uU]\s*\/\s*m[lL]|m[uU]\s*\/\s*[lL])',
    ],
    'age': [
        r'(?:age|patient\s*age|age\s*[\/\\]\s*sex|age\s*[\/\\]\s*gender)\s*[:=\-]?\s*(\d{1,3})\s*(?:y(?:ears?|rs?)?)?',
        r'(\d{1,3})\s*(?:y(?:ears?|rs?))\s*(?:old)?',
    ],
    'skin_thickness': [
        r'(?:skin\s*thickness|triceps\s*skinfold|skinfold|tsf)\s*[:=\-]?\s*(\d{1,2}(?:\.\d+)?)',
    ],
    'pregnancies': [
        r'(?:pregnancies|gravida|para|number\s*of\s*pregnancies)\s*[:=\-]?\s*(\d{1,2})',
    ],
    'dpf': [
        r'(?:diabetes\s*pedigree\s*function|pedigree\s*function|dpf)\s*[:=\-]?\s*(0\.\d+)',
    ]
}

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text content from a PDF document using pdfplumber."""
    extracted_text = []
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text.append(page_text)
                # Also check tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        clean_row = [str(cell) for cell in row if cell]
                        if clean_row:
                            extracted_text.append(" | ".join(clean_row))
    except Exception as e:
        logger.error(f"Error reading PDF with pdfplumber: {e}")
    return "\n".join(extracted_text)

def extract_text_from_image(file_path: str) -> str:
    """Attempts OCR extraction on an image using pytesseract if available."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        logger.warning(f"Server-side pytesseract not available or failed: {e}")
        return ""

def parse_clinical_values(text: str) -> Dict[str, Any]:
    """
    Parses unstructured clinical report text to detect and extract parameters:
    Glucose, Blood Pressure, BMI, Insulin, Age, Skin Thickness, Pregnancies, DPF.
    """
    results: Dict[str, Any] = {
        'raw_text_length': len(text),
        'extracted': {},
        'detected_count': 0
    }

    if not text:
        return results

    text_lower = text.lower()

    # 1. Glucose
    for pattern in PATTERNS['glucose']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            # Validate sensible clinical range for fasting glucose
            if 40 <= val <= 400:
                results['extracted']['glucose'] = {
                    'value': round(val, 1),
                    'unit': 'mg/dL',
                    'field': 'glucose',
                    'label': 'Fasting Glucose',
                    'snippet': m.group(0),
                    'confidence': 95 if 'fast' in m.group(0) or 'glucose' in m.group(0) else 80
                }
                break

    # 2. Blood Pressure
    for pattern in PATTERNS['blood_pressure']:
        m = re.search(pattern, text_lower)
        if m:
            if len(m.groups()) == 2 and m.group(2):
                systolic = float(m.group(1))
                diastolic = float(m.group(2))
                # Diastolic is used by the Pima model
                if 40 <= diastolic <= 140:
                    results['extracted']['blood_pressure'] = {
                        'value': round(diastolic, 0),
                        'systolic': round(systolic, 0),
                        'unit': 'mm Hg',
                        'field': 'blood_pressure',
                        'label': 'Diastolic Blood Pressure',
                        'snippet': f"{systolic:.0f}/{diastolic:.0f} mm Hg",
                        'confidence': 95
                    }
                    break
            elif m.group(1):
                dia = float(m.group(1))
                if 40 <= dia <= 140:
                    results['extracted']['blood_pressure'] = {
                        'value': round(dia, 0),
                        'unit': 'mm Hg',
                        'field': 'blood_pressure',
                        'label': 'Diastolic Blood Pressure',
                        'snippet': m.group(0),
                        'confidence': 85
                    }
                    break

    # 3. BMI
    for pattern in PATTERNS['bmi']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            if 12 <= val <= 65:
                results['extracted']['bmi'] = {
                    'value': round(val, 1),
                    'unit': 'kg/m²',
                    'field': 'bmi',
                    'label': 'Body Mass Index',
                    'snippet': m.group(0),
                    'confidence': 95
                }
                break

    # Check if height & weight exist to compute BMI if BMI wasn't directly found
    if 'bmi' not in results['extracted']:
        m_ht = re.search(r'(?:height|ht)\s*[:=\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:cm|cms)?', text_lower)
        m_wt = re.search(r'(?:weight|wt)\s*[:=\-]?\s*(\d{2,3}(?:\.\d+)?)\s*(?:kg|kgs)?', text_lower)
        if m_ht and m_wt:
            ht_val = float(m_ht.group(1))
            wt_val = float(m_wt.group(1))
            if ht_val > 100 and wt_val > 30:
                calc_bmi = round(wt_val / ((ht_val / 100) ** 2), 1)
                if 12 <= calc_bmi <= 65:
                    results['extracted']['bmi'] = {
                        'value': calc_bmi,
                        'unit': 'kg/m²',
                        'field': 'bmi',
                        'label': 'Body Mass Index (Computed from Ht/Wt)',
                        'snippet': f"Ht: {ht_val}cm, Wt: {wt_val}kg",
                        'confidence': 90
                    }

    # 4. Insulin
    for pattern in PATTERNS['insulin']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            if 0 <= val <= 850:
                results['extracted']['insulin'] = {
                    'value': round(val, 1),
                    'unit': 'μU/mL',
                    'field': 'insulin',
                    'label': 'Serum Insulin',
                    'snippet': m.group(0),
                    'confidence': 90
                }
                break

    # 5. Age
    for pattern in PATTERNS['age']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            if 10 <= val <= 110:
                results['extracted']['age'] = {
                    'value': int(val),
                    'unit': 'years',
                    'field': 'age',
                    'label': 'Patient Age',
                    'snippet': m.group(0),
                    'confidence': 88
                }
                break

    # 6. Skin Thickness
    for pattern in PATTERNS['skin_thickness']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            if 5 <= val <= 99:
                results['extracted']['skin_thickness'] = {
                    'value': round(val, 1),
                    'unit': 'mm',
                    'field': 'skin_thickness',
                    'label': 'Triceps Skinfold',
                    'snippet': m.group(0),
                    'confidence': 85
                }
                break

    # 7. Pregnancies
    for pattern in PATTERNS['pregnancies']:
        m = re.search(pattern, text_lower)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 20:
                results['extracted']['pregnancies'] = {
                    'value': val,
                    'unit': 'count',
                    'field': 'pregnancies',
                    'label': 'Pregnancies',
                    'snippet': m.group(0),
                    'confidence': 85
                }
                break

    # 8. Diabetes Pedigree Function
    for pattern in PATTERNS['dpf']:
        m = re.search(pattern, text_lower)
        if m:
            val = float(m.group(1))
            if 0.05 <= val <= 2.5:
                results['extracted']['diabetes_pedigree_function'] = {
                    'value': round(val, 3),
                    'unit': 'score',
                    'field': 'diabetes_pedigree_function',
                    'label': 'Pedigree Function (DPF)',
                    'snippet': m.group(0),
                    'confidence': 80
                }
                break

    results['detected_count'] = len(results['extracted'])
    return results


DATASET_COLUMN_MAP = {
    'pregnancies': ('pregnancies', 'Pregnancies', 'count', 'int'),
    'pregnant': ('pregnancies', 'Pregnancies', 'count', 'int'),
    'glucose': ('glucose', 'Fasting Glucose', 'mg/dL', 'float1'),
    'fastingglucose': ('glucose', 'Fasting Glucose', 'mg/dL', 'float1'),
    'bloodpressure': ('blood_pressure', 'Diastolic Blood Pressure', 'mm Hg', 'float1'),
    'bp': ('blood_pressure', 'Diastolic Blood Pressure', 'mm Hg', 'float1'),
    'skinthickness': ('skin_thickness', 'Triceps Skinfold', 'mm', 'float1'),
    'skinfold': ('skin_thickness', 'Triceps Skinfold', 'mm', 'float1'),
    'insulin': ('insulin', 'Serum Insulin', 'μU/mL', 'float1'),
    'bmi': ('bmi', 'Body Mass Index', 'kg/m²', 'float1'),
    'bodymassindex': ('bmi', 'Body Mass Index', 'kg/m²', 'float1'),
    'diabetespedigreefunction': ('diabetes_pedigree_function', 'Pedigree Function (DPF)', 'score', 'float3'),
    'dpf': ('diabetes_pedigree_function', 'Pedigree Function (DPF)', 'score', 'float3'),
    'age': ('age', 'Patient Age', 'years', 'int'),
}


def _normalize_col_name(col: str) -> str:
    return re.sub(r'[^a-z0-9]', '', str(col).strip().lower())


def _format_dataset_value(raw_val: Any, fmt: str):
    if raw_val is None:
        return None
    s = str(raw_val).strip()
    if s == '' or s.lower() in ('nan', 'none', 'null'):
        return None
    val = float(s)
    if fmt == 'int':
        return int(round(val))
    if fmt == 'float3':
        return round(val, 3)
    return round(val, 1)


def _row_to_extracted(row: Dict[str, Any]) -> Dict[str, Any]:
    extracted: Dict[str, Any] = {}
    meta = {
        'pregnancies': ('Pregnancies', 'count'),
        'glucose': ('Fasting Glucose', 'mg/dL'),
        'blood_pressure': ('Diastolic Blood Pressure', 'mm Hg'),
        'skin_thickness': ('Triceps Skinfold', 'mm'),
        'insulin': ('Serum Insulin', 'μU/mL'),
        'bmi': ('Body Mass Index', 'kg/m²'),
        'diabetes_pedigree_function': ('Pedigree Function (DPF)', 'score'),
        'age': ('Patient Age', 'years'),
    }
    for field, (label, unit) in meta.items():
        if field in row and row[field] is not None:
            extracted[field] = {
                'value': row[field],
                'unit': unit,
                'field': field,
                'label': label,
                'snippet': f"{label}: {row[field]}",
                'confidence': 100
            }
    return extracted


def parse_dataset_file(file_path: str, ext: str) -> Dict[str, Any]:
    """
    Parses an uploaded CSV, Excel (.xlsx/.xls), or delimited TXT dataset file
    containing diabetes screening columns (Pregnancies, Glucose, BloodPressure,
    SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age).
    """
    import csv
    import pandas as pd

    df = None
    if ext == 'csv':
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    elif ext in ('xlsx', 'xls'):
        df = pd.read_excel(file_path)
    elif ext == 'txt':
        with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
            raw_text = f.read()
        # Check if TXT contains comma-separated dataset header
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else ''
        if ',' in first_line and any(
            _normalize_col_name(col) in DATASET_COLUMN_MAP for col in first_line.split(',')
        ):
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        else:
            return parse_clinical_values(raw_text)

    if df is None or df.empty:
        return {'raw_text_length': 0, 'extracted': {}, 'detected_count': 0, 'dataset_rows': []}

    # Map matching columns
    col_mapping = {}
    outcome_col = None
    for orig_col in df.columns:
        norm = _normalize_col_name(orig_col)
        if norm in DATASET_COLUMN_MAP:
            col_mapping[orig_col] = DATASET_COLUMN_MAP[norm]
        elif norm in ('outcome', 'diabetes', 'target', 'class', 'label'):
            outcome_col = orig_col

    if not col_mapping:
        # Fallback: parse file text via clinical regexes
        try:
            with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                return parse_clinical_values(f.read())
        except Exception:
            return {'raw_text_length': 0, 'extracted': {}, 'detected_count': 0, 'dataset_rows': []}

    dataset_rows = []
    for idx, record in df.iterrows():
        row_data: Dict[str, Any] = {'_row_num': int(idx) + 1}
        has_any = False
        for orig_col, (field, _label, _unit, fmt) in col_mapping.items():
            try:
                val = _format_dataset_value(record[orig_col], fmt)
            except (ValueError, TypeError):
                val = None
            if val is not None:
                row_data[field] = val
                has_any = True
        if outcome_col is not None:
            try:
                out_val = _format_dataset_value(record[outcome_col], 'int')
                if out_val is not None:
                    row_data['_outcome'] = out_val
            except (ValueError, TypeError):
                pass
        if has_any:
            dataset_rows.append(row_data)

    if not dataset_rows:
        return {'raw_text_length': 0, 'extracted': {}, 'detected_count': 0, 'dataset_rows': []}

    first_extracted = _row_to_extracted(dataset_rows[0])
    return {
        'raw_text_length': len(dataset_rows),
        'extracted': first_extracted,
        'detected_count': len(first_extracted),
        'is_dataset': True,
        'total_rows': len(dataset_rows),
        'dataset_rows': dataset_rows
    }
