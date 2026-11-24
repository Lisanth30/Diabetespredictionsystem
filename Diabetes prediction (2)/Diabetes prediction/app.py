"""
Flask Application for HealthGuard Diabetes Prediction & Clinical Screening System
"""

import json
import os
import uuid
from functools import wraps
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify,
    send_file, abort, make_response
)
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc

from config import Config
from database import SessionLocal, User, Prediction, init_db
from ml.explain import predict_diabetes_risk, CLINICAL_STANDARDS, assess_bmi
from ml.train_model import train_and_evaluate
from utils.pdf_generator import generate_prediction_pdf

app = Flask(__name__)
app.config.from_object(Config)

# Ensure models and database exist
init_db()

def get_db():
    return SessionLocal()

@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()

# Authentication & Access Control Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access the administrator portal.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    """Inject user state and current year into all templates."""
    db = get_db()
    current_user = None
    if 'user_id' in session:
        current_user = db.query(User).filter_by(id=session['user_id']).first()
    return {
        'current_user': current_user,
        'now': datetime.now(),
        'year': datetime.now().year
    }

# ==============================================================================
# PUBLIC & EDUCATIONAL ROUTES
# ==============================================================================

@app.route('/')
def index():
    """Landing page introducing the screening platform."""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/education')
def education():
    """Interactive educational guide on diabetes types, prevention, and lifestyle."""
    return render_template('education.html')

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not name or len(name) < 2:
            flash('Please enter a valid full name (minimum 2 characters).', 'danger')
            return render_template('auth/register.html', name=name, email=email)

        if not email or '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match. Please verify.', 'danger')
            return render_template('auth/register.html', name=name, email=email)

        db = get_db()
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        new_user = User(
            name=name,
            email=email,
            role='user'
        )
        new_user.set_password(password)

        try:
            db.add(new_user)
            db.commit()
            flash('Registration successful! You may now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.rollback()
            flash('An unexpected error occurred while creating your account.', 'danger')
            return render_template('auth/register.html', name=name, email=email)

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        db = get_db()
        user = db.query(User).filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html', email=email)

            session.permanent = remember
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['role'] = user.role

            flash(f'Welcome back, {user.name}!', 'success')
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('auth/login.html', email=email)

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ==============================================================================
# USER DASHBOARD & SCREENING ROUTES
# ==============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """User home dashboard displaying health summary and recent predictions."""
    db = get_db()
    user_id = session['user_id']
    
    predictions = db.query(Prediction).filter_by(user_id=user_id).order_by(desc(Prediction.created_at)).all()
    total_count = len(predictions)
    latest = predictions[0] if total_count > 0 else None

    # Calculate average glucose and average BMI across user's history
    avg_glucose = db.query(func.avg(Prediction.glucose)).filter_by(user_id=user_id).scalar() or 0.0
    avg_bmi = db.query(func.avg(Prediction.bmi)).filter_by(user_id=user_id).scalar() or 0.0

    return render_template(
        'dashboard/index.html',
        predictions=predictions[:5],  # top 5 recent
        total_count=total_count,
        latest=latest,
        avg_glucose=round(avg_glucose, 1),
        avg_bmi=round(avg_bmi, 1)
    )

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    """Screening assessment input form and prediction handler."""
    if request.method == 'POST':
        try:
            # 1. Extract and sanitize inputs
            pregnancies = int(request.form.get('pregnancies') or 0)
            glucose = float(request.form.get('glucose') or 0.0)
            blood_pressure = float(request.form.get('blood_pressure') or 0.0)
            skin_thickness = float(request.form.get('skin_thickness') or 0.0)
            insulin = float(request.form.get('insulin') or 0.0)
            bmi = float(request.form.get('bmi') or 0.0)
            dpf = float(request.form.get('diabetes_pedigree_function') or 0.47)
            age = int(request.form.get('age') or 0)
            notes = request.form.get('notes', '').strip()

            # 2. Server-side clinical range validation
            errors = []
            if pregnancies < 0 or pregnancies > 25:
                errors.append('Pregnancies must be between 0 and 25.')
            if glucose < 40 or glucose > 300:
                errors.append('Glucose must be between 40 and 300 mg/dL.')
            if blood_pressure < 30 or blood_pressure > 200:
                errors.append('Diastolic Blood Pressure must be between 30 and 200 mm Hg.')
            if skin_thickness < 0 or skin_thickness > 100:
                errors.append('Skin Thickness must be between 0 and 100 mm.')
            if insulin < 0 or insulin > 900:
                errors.append('Insulin must be between 0 and 900 μU/mL.')
            if bmi < 10.0 or bmi > 75.0:
                errors.append('BMI must be between 10.0 and 75.0 kg/m².')
            if dpf < 0.05 or dpf > 3.0:
                errors.append('Diabetes Pedigree Function must be between 0.05 and 3.0.')
            if age < 15 or age > 120:
                errors.append('Age must be between 15 and 120 years.')

            if errors:
                for err in errors:
                    flash(err, 'danger')
                return render_template(
                    'dashboard/predict.html',
                    standards=CLINICAL_STANDARDS,
                    form_data=request.form
                )

            # 3. Model Inference via Explainability Engine
            input_dict = {
                'Pregnancies': pregnancies,
                'Glucose': glucose,
                'BloodPressure': blood_pressure,
                'SkinThickness': skin_thickness,
                'Insulin': insulin,
                'BMI': bmi,
                'DiabetesPedigreeFunction': dpf,
                'Age': age
            }
            result_data = predict_diabetes_risk(input_dict)

            # 4. Persist to Database
            db = get_db()
            new_pred = Prediction(
                user_id=session['user_id'],
                pregnancies=pregnancies,
                glucose=glucose,
                blood_pressure=blood_pressure,
                skin_thickness=skin_thickness,
                insulin=insulin,
                bmi=bmi,
                diabetes_pedigree_function=dpf,
                age=age,
                prediction_outcome=result_data['prediction'],
                probability=result_data['probability'],
                risk_level=result_data['risk_level'],
                contributing_factors_json=json.dumps(result_data['parameter_factors']),
                notes=notes
            )
            db.add(new_pred)
            db.commit()

            flash('Health assessment successfully analyzed and saved to your records!', 'success')
            return redirect(url_for('prediction_result', pred_id=new_pred.id))

        except ValueError as ve:
            flash('Invalid numeric format entered. Please verify all inputs.', 'danger')
            return render_template('dashboard/predict.html', standards=CLINICAL_STANDARDS, form_data=request.form)
        except Exception as e:
            flash(f'An error occurred during prediction analysis: {str(e)}', 'danger')
            return render_template('dashboard/predict.html', standards=CLINICAL_STANDARDS, form_data=request.form)

    return render_template('dashboard/predict.html', standards=CLINICAL_STANDARDS, form_data={})

@app.route('/result/<int:pred_id>')
@login_required
def prediction_result(pred_id):
    """Visual prediction result page with gauge, parameter breakdown, risk change alert, and advice."""
    db = get_db()
    pred = db.query(Prediction).filter_by(id=pred_id).first()

    if not pred:
        flash('Assessment record not found.', 'warning')
        return redirect(url_for('dashboard'))

    # Strict privacy: ensure users can only view their own predictions (unless admin)
    if pred.user_id != session['user_id'] and session.get('role') != 'admin':
        flash('Unauthorized access to this assessment record.', 'danger')
        return redirect(url_for('dashboard'))

    # Re-evaluate factors and recommendations for rich display
    input_dict = {
        'Pregnancies': pred.pregnancies,
        'Glucose': pred.glucose,
        'BloodPressure': pred.blood_pressure,
        'SkinThickness': pred.skin_thickness,
        'Insulin': pred.insulin,
        'BMI': pred.bmi,
        'DiabetesPedigreeFunction': pred.diabetes_pedigree_function,
        'Age': pred.age
    }
    analysis = predict_diabetes_risk(input_dict)

    # 4. Risk Change Alert: Compare with user's previous result
    previous_pred = db.query(Prediction).filter(
        Prediction.user_id == pred.user_id,
        Prediction.id < pred.id
    ).order_by(desc(Prediction.created_at), desc(Prediction.id)).first()

    risk_change = None
    if previous_pred:
        diff = round(pred.probability - previous_pred.probability, 1)
        risk_change = {
            'has_previous': True,
            'previous_id': previous_pred.id,
            'previous_date': previous_pred.created_at,
            'previous_prob': round(previous_pred.probability, 1),
            'current_prob': round(pred.probability, 1),
            'diff': diff,
            'diff_abs': abs(diff),
            'direction': 'increased' if diff > 0 else ('decreased' if diff < 0 else 'unchanged'),
            'previous_risk_level': previous_pred.risk_level,
            'current_risk_level': pred.risk_level
        }

    return render_template(
        'dashboard/result.html',
        prediction=pred,
        analysis=analysis,
        risk_change=risk_change,
        standards=CLINICAL_STANDARDS
    )

@app.route('/api/scan-report', methods=['POST'])
@login_required
def api_scan_report():
    """
    Accepts an uploaded lab report (PDF or Image), dataset file (CSV, Excel, TXT),
    or raw OCR text, and extracts clinical markers (Pregnancies, Glucose, BP,
    SkinThickness, Insulin, BMI, DPF, Age).
    """
    from ocr_service import (
        extract_text_from_pdf,
        extract_text_from_image,
        parse_clinical_values,
        parse_dataset_file
    )
    
    # 1. Pre-extracted text payload (e.g. client-side Tesseract.js)
    if request.is_json:
        data = request.get_json()
        raw_text = data.get('text', '')
        if raw_text:
            parsed = parse_clinical_values(raw_text)
            return jsonify({'success': True, 'data': parsed, 'source': 'client_ocr'})

    # 2. File upload processing
    if 'report_file' not in request.files:
        return jsonify({'success': False, 'error': 'No document file uploaded'}), 400

    file = request.files['report_file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'Empty file selected'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    temp_dir = os.path.join(app.root_path, 'scratch')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"scan_{uuid.uuid4().hex[:8]}_{filename}")
    file.save(temp_path)

    extracted_text = ""
    try:
        if ext in ['csv', 'xlsx', 'xls', 'txt']:
            parsed = parse_dataset_file(temp_path, ext)
            return jsonify({
                'success': True,
                'filename': filename,
                'text_length': parsed.get('raw_text_length', 0),
                'raw_preview': '',
                'data': parsed
            })
        elif ext == 'pdf':
            extracted_text = extract_text_from_pdf(temp_path)
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            extracted_text = extract_text_from_image(temp_path)
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported file format (.{ext}). Please upload CSV, Excel, TXT, PDF, or Image files.'
            }), 400
        
        parsed = parse_clinical_values(extracted_text)
        return jsonify({
            'success': True,
            'filename': filename,
            'text_length': len(extracted_text),
            'raw_preview': extracted_text[:400] if extracted_text else '',
            'data': parsed
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Scan processing error: {str(e)}'}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

@app.route('/history')
@login_required
def history():
    """User prediction history log with filtering and search."""
    db = get_db()
    user_id = session['user_id']
    risk_filter = request.args.get('risk', 'all')

    query = db.query(Prediction).filter_by(user_id=user_id)
    if risk_filter in ['Low', 'Medium', 'High']:
        query = query.filter_by(risk_level=risk_filter)

    records = query.order_by(desc(Prediction.created_at)).all()
    return render_template('dashboard/history.html', records=records, current_filter=risk_filter)

@app.route('/history/delete/<int:pred_id>', methods=['POST'])
@login_required
def delete_prediction(pred_id):
    """Allow user to remove an assessment record."""
    db = get_db()
    pred = db.query(Prediction).filter_by(id=pred_id).first()

    if not pred or (pred.user_id != session['user_id'] and session.get('role') != 'admin'):
        flash('Assessment record not found or permission denied.', 'danger')
        return redirect(url_for('history'))

    try:
        db.delete(pred)
        db.commit()
        flash('Assessment record deleted successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('Failed to delete assessment record.', 'danger')

    return redirect(url_for('history'))

@app.route('/trends')
@login_required
def trends():
    """Interactive risk and biomarker trend visualization dashboard."""
    return render_template('dashboard/trends.html')

@app.route('/prediction/<int:pred_id>/download-pdf')
@login_required
def download_pdf(pred_id):
    """Generate and return downloadable PDF assessment report."""
    db = get_db()
    pred = db.query(Prediction).filter_by(id=pred_id).first()

    if not pred or (pred.user_id != session['user_id'] and session.get('role') != 'admin'):
        abort(403)

    user = pred.user or db.query(User).filter_by(id=pred.user_id).first()
    user_name = user.name if user else 'Valued Patient'
    user_email = user.email if user else 'N/A'

    pdf_bytes = generate_prediction_pdf(pred.to_dict(), user_name, user_email)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=HealthGuard_Diabetes_Report_{pred.id}.pdf'
    return response

@app.route('/prediction/<int:pred_id>/print-report')
@login_required
def print_report(pred_id):
    """Printable clinical report view."""
    db = get_db()
    pred = db.query(Prediction).filter_by(id=pred_id).first()

    if not pred or (pred.user_id != session['user_id'] and session.get('role') != 'admin'):
        abort(403)

    input_dict = {
        'Pregnancies': pred.pregnancies,
        'Glucose': pred.glucose,
        'BloodPressure': pred.blood_pressure,
        'SkinThickness': pred.skin_thickness,
        'Insulin': pred.insulin,
        'BMI': pred.bmi,
        'DiabetesPedigreeFunction': pred.diabetes_pedigree_function,
        'Age': pred.age
    }
    analysis = predict_diabetes_risk(input_dict)

    return render_template(
        'report_template.html',
        prediction=pred,
        analysis=analysis,
        patient=pred.user
    )

# ==============================================================================
# REST API ENDPOINTS FOR INTERACTIVE CHARTS
# ==============================================================================

@app.route('/api/user/trends')
@login_required
def api_user_trends():
    """Returns chronological timeline data for Chart.js user trends."""
    db = get_db()
    user_id = session['user_id']
    preds = db.query(Prediction).filter_by(user_id=user_id).order_by(Prediction.created_at.asc()).all()

    labels = []
    probabilities = []
    glucoses = []
    bmis = []
    blood_pressures = []

    for p in preds:
        labels.append(p.created_at.strftime('%b %d, %Y'))
        probabilities.append(round(p.probability, 1))
        glucoses.append(round(p.glucose, 1))
        bmis.append(round(p.bmi, 1))
        blood_pressures.append(round(p.blood_pressure, 1))

    return jsonify({
        'labels': labels,
        'probabilities': probabilities,
        'glucoses': glucoses,
        'bmis': bmis,
        'blood_pressures': blood_pressures,
        'count': len(preds)
    })

# ==============================================================================
# ADMIN PORTAL ROUTES
# ==============================================================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin analytics overview: user counts, risk distribution, recent activity."""
    db = get_db()

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_predictions = db.query(func.count(Prediction.id)).scalar() or 0
    high_risk_count = db.query(func.count(Prediction.id)).filter_by(risk_level='High').scalar() or 0
    med_risk_count = db.query(func.count(Prediction.id)).filter_by(risk_level='Medium').scalar() or 0
    low_risk_count = db.query(func.count(Prediction.id)).filter_by(risk_level='Low').scalar() or 0

    recent_predictions = db.query(Prediction).order_by(desc(Prediction.created_at)).limit(8).all()
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()

    # Load cached ML metrics
    metrics = {}
    if os.path.exists(Config.METRICS_PATH):
        try:
            with open(Config.METRICS_PATH, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except Exception:
            metrics = {}

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_predictions=total_predictions,
        high_risk_count=high_risk_count,
        med_risk_count=med_risk_count,
        low_risk_count=low_risk_count,
        recent_predictions=recent_predictions,
        recent_users=recent_users,
        metrics=metrics
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    """User management view with role assignment and status control."""
    db = get_db()
    users = db.query(User).order_by(desc(User.created_at)).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def admin_toggle_user_role(user_id):
    """Toggle admin / user role."""
    if user_id == session['user_id']:
        flash('You cannot change your own administrative role.', 'warning')
        return redirect(url_for('admin_users'))

    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        user.role = 'user' if user.role == 'admin' else 'admin'
        db.commit()
        flash(f"Updated role for {user.name} to {user.role.upper()}.", 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Remove a user and cascade predictions."""
    if user_id == session['user_id']:
        flash('You cannot delete your own account while logged in.', 'danger')
        return redirect(url_for('admin_users'))

    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        db.delete(user)
        db.commit()
        flash(f'User {user.name} and associated records were deleted.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/predictions')
@admin_required
def admin_predictions():
    """System-wide prediction logs with search and risk filters."""
    db = get_db()
    risk_filter = request.args.get('risk', 'all')
    search_query = request.args.get('q', '').strip()

    query = db.query(Prediction).join(User)

    if risk_filter in ['Low', 'Medium', 'High']:
        query = query.filter(Prediction.risk_level == risk_filter)

    if search_query:
        query = query.filter(
            (User.name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        )

    predictions = query.order_by(desc(Prediction.created_at)).limit(100).all()
    return render_template(
        'admin/predictions.html',
        predictions=predictions,
        current_filter=risk_filter,
        search_query=search_query
    )

@app.route('/admin/model-performance')
@admin_required
def admin_model_performance():
    """ML Model Performance portal showing accuracy, ROC-AUC, confusion matrix, and coefficients."""
    metrics = {}
    if os.path.exists(Config.METRICS_PATH):
        try:
            with open(Config.METRICS_PATH, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except Exception:
            metrics = {}

    return render_template('admin/model_perf.html', metrics=metrics)

@app.route('/admin/retrain', methods=['POST'])
@admin_required
def admin_retrain_model():
    """Trigger training pipeline and refresh saved model, scaler, and metrics."""
    try:
        metrics = train_and_evaluate()
        flash('Logistic Regression model retrained and metrics updated successfully!', 'success')
    except Exception as e:
        flash(f'Error during model retraining: {str(e)}', 'danger')

    return redirect(url_for('admin_model_performance'))

@app.route('/api/admin/analytics')
@admin_required
def api_admin_analytics():
    """Returns aggregated data for Admin dashboard charts."""
    db = get_db()

    # Risk Distribution
    risk_counts = {
        'Low': db.query(func.count(Prediction.id)).filter_by(risk_level='Low').scalar() or 0,
        'Medium': db.query(func.count(Prediction.id)).filter_by(risk_level='Medium').scalar() or 0,
        'High': db.query(func.count(Prediction.id)).filter_by(risk_level='High').scalar() or 0
    }

    # Predictions over past 7 days
    now = datetime.now()
    dates = [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    daily_counts = []
    for d_str in dates:
        start_d = datetime.strptime(d_str, '%Y-%m-%d')
        end_d = start_d + timedelta(days=1)
        cnt = db.query(func.count(Prediction.id)).filter(
            Prediction.created_at >= start_d,
            Prediction.created_at < end_d
        ).scalar() or 0
        daily_counts.append(cnt)

    return jsonify({
        'risk_distribution': risk_counts,
        'dates': [datetime.strptime(d, '%Y-%m-%d').strftime('%b %d') for d in dates],
        'daily_counts': daily_counts
    })

# ==============================================================================
# ERROR HANDLERS
# ==============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_code=404, error_msg="The page you requested was not found."), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('base.html', error_code=403, error_msg="You do not have permission to view this resource."), 403

@app.errorhandler(500)
def internal_error(error):
    return render_template('base.html', error_code=500, error_msg="A system error occurred. Please try again later."), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    print(f"[*] Starting HealthGuard AI on http://127.0.0.1:{port}")
    app.run(host='127.0.0.1', port=port, debug=True)
