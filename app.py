from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import smtplib
import os
import json
from datetime import datetime

# Import backend modules
from backend.models import db, User, Patient, Vaccine, Prediction, PredictionHistory, init_database
from backend.data_processor import DataProcessor
from backend.prediction_engine import PredictionEngine

app = Flask(__name__)
app.secret_key = "digital_twin_secret_key_2024"  # Required for session management

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digital_twin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# In-memory storage (for backward compatibility)
users = {}
otp_storage = {}

EMAIL = "yourgmail@gmail.com"
APP_PASSWORD = "your_app_password"  # Gmail App Password

# ==================== INITIALIZATION ====================

def initialize_database():
    """Initialize database and add sample data"""
    with app.app_context():
        db.create_all()
        init_database(app)
        print("Database initialized with sample vaccines")

# Initialize on startup
initialize_database()

# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

# ---------- AUTH ----------
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data['email'].lower().strip()

    if email in users:
        return jsonify({"message": "User already exists"}), 400

    users[email] = {
        "name": data['name'],
        "password": data['password']
    }

    return jsonify({"message": "Account created"})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    print("LOGIN DATA RECEIVED:", data)
    if not data:
        return jsonify({"message": "No data provided"}), 400
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    print("Looking for user:", email)
    print("Available users:", list(users.keys()))

    user = users.get(email)

    if user and user['password'] == password:
        session['user_email'] = email
        session['user_name'] = user['name']
        print("Login successful for:", email)
        return jsonify({"message": "Login success", "name": user['name']})
    print("Login failed for:", email)
    return jsonify({"message": "Invalid credentials"}), 400


# ---------- OTP ----------
def send_email(to_email, otp):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL, APP_PASSWORD)

    message = f"Subject: OTP Verification\n\nYour OTP is {otp}"
    server.sendmail(EMAIL, to_email, message)
    server.quit()


@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json() or request.form
    print("DATA RECEIVED:", data)

    email = data.get('email')

    print("USERS:", users)   # <-- THIS LINE YOU KEEP SKIPPING

    if email not in users:
        return jsonify({"message": "Email not registered"}), 400

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    send_email(email, otp)
    return jsonify({"message": "OTP sent"})


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    email = data['email']
    otp = data['otp']

    if otp_storage.get(email) == otp:
        return jsonify({"message": "Verified"})
    return jsonify({"message": "Invalid OTP"}), 400


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data['email']
    password = data['password']

    if email in users:
        users[email]['password'] = password
        return jsonify({"message": "Password updated"})

    return jsonify({"message": "User not found"}), 400


# ==================== BACKEND PAGES ====================

@app.route('/patients')
def patients_page():
    """Patient management page"""
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', section='patients', name=session.get('user_name'))

@app.route('/vaccines')
def vaccines_page():
    """Vaccine information page"""
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', section='vaccines', name=session.get('user_name'))

@app.route('/predict')
def predict_page():
    """Prediction page"""
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', section='predict', name=session.get('user_name'))

@app.route('/history')
def history_page():
    """Prediction history page"""
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', section='history', name=session.get('user_name'))

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('home'))
    return render_template('dashboard.html', name=session.get('user_name'), email=session.get('user_email'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/check-session', methods=['GET'])
def check_session():
    if 'user_email' in session:
        return jsonify({"logged_in": True, "name": session.get('user_name'), "email": session.get('user_email')})
    return jsonify({"logged_in": False}), 401


# ==================== BACKEND API ROUTES ====================

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Upload and process CSV file with patient data"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        try:
            file_content = file.read()
            result = DataProcessor.parse_csv(file_content)
            
            if result['patients']:
                cleaned_patients = DataProcessor.clean_data(result['patients'])
                validation = DataProcessor.validate_data(cleaned_patients)
                summary = DataProcessor.generate_summary(validation['valid'])
                
                return jsonify({
                    'success': True,
                    'message': f'Processed {len(validation["valid"])} patients',
                    'patients': validation['valid'][:10],
                    'total_patients': len(validation['valid']),
                    'summary': summary,
                    'errors': result['errors'],
                    'warnings': validation['warnings']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No valid patient records found',
                    'parse_errors': result['errors']
                }), 400
                
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file'}), 400


@app.route('/api/save-patients', methods=['POST'])
def save_patients():
    """Save processed patient data to database"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    patients_data = data.get('patients', [])
    
    if not patients_data:
        return jsonify({'error': 'No patient data provided'}), 400
    
    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    saved_count = 0
    errors = []
    
    for patient_data in patients_data:
        try:
            existing = Patient.query.filter_by(
                user_id=user.id,
                patient_id=patient_data.get('patient_id')
            ).first()
            
            if existing:
                for key, value in patient_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                patient = Patient(
                    user_id=user.id,
                    patient_id=patient_data.get('patient_id'),
                    name=patient_data.get('name'),
                    age=patient_data.get('age'),
                    gender=patient_data.get('gender'),
                    blood_type=patient_data.get('blood_type'),
                    weight=patient_data.get('weight'),
                    height=patient_data.get('height'),
                    bmi=patient_data.get('bmi'),
                    diabetes=patient_data.get('diabetes'),
                    hypertension=patient_data.get('hypertension'),
                    heart_disease=patient_data.get('heart_disease'),
                    liver_disease=patient_data.get('liver_disease'),
                    kidney_disease=patient_data.get('kidney_disease'),
                    autoimmune=patient_data.get('autoimmune'),
                    cancer_history=patient_data.get('cancer_history'),
                    drug_allergies=json.dumps(patient_data.get('drug_allergies', [])),
                    food_allergies=json.dumps(patient_data.get('food_allergies', [])),
                    environmental_allergies=json.dumps(patient_data.get('environmental_allergies', [])),
                    medications=patient_data.get('medications'),
                    family_history=patient_data.get('family_history'),
                    notes=patient_data.get('notes')
                )
                db.session.add(patient)
            
            saved_count += 1
            
        except Exception as e:
            errors.append(f"Error saving patient {patient_data.get('patient_id')}: {str(e)}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'saved': saved_count,
        'errors': errors
    })


@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Get all patients for current user"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    patients = Patient.query.filter_by(user_id=user.id).all()
    
    return jsonify({
        'patients': [{
            'id': p.id,
            'patient_id': p.patient_id,
            'name': p.name,
            'age': p.age,
            'gender': p.gender,
            'blood_type': p.blood_type,
            'bmi': p.bmi
        } for p in patients]
    })


@app.route('/api/vaccines', methods=['GET'])
def get_vaccines():
    """Get all available vaccines"""
    
    vaccines = Vaccine.query.all()
    
    return jsonify({
        'vaccines': [{
            'id': v.id,
            'name': v.name,
            'manufacturer': v.manufacturer,
            'vaccine_type': v.vaccine_type,
            'age_min': v.age_min,
            'age_max': v.age_max,
            'dose_count': v.dose_count,
            'interval_days': v.interval_days
        } for v in vaccines]
    })


@app.route('/api/vaccines/<int:vaccine_id>', methods=['GET'])
def get_vaccine(vaccine_id):
    """Get specific vaccine details"""
    
    vaccine = Vaccine.query.get(vaccine_id)
    if not vaccine:
        return jsonify({'error': 'Vaccine not found'}), 404
    
    return jsonify({
        'vaccine': {
            'id': vaccine.id,
            'name': vaccine.name,
            'manufacturer': vaccine.manufacturer,
            'vaccine_type': vaccine.vaccine_type,
            'ingredients': json.loads(vaccine.ingredients) if vaccine.ingredients else [],
            'active_ingredients': json.loads(vaccine.active_ingredients) if vaccine.active_ingredients else [],
            'excipients': json.loads(vaccine.excipients) if vaccine.excipients else [],
            'contraindications': json.loads(vaccine.contraindications) if vaccine.contraindications else [],
            'common_side_effects': json.loads(vaccine.common_side_effects) if vaccine.common_side_effects else [],
            'rare_side_effects': json.loads(vaccine.rare_side_effects) if vaccine.rare_side_effects else [],
            'age_min': vaccine.age_min,
            'age_max': vaccine.age_max,
            'dose_count': vaccine.dose_count,
            'interval_days': vaccine.interval_days
        }
    })


@app.route('/api/predict', methods=['POST'])
def run_prediction():
    """Run prediction for patient-vaccine combination"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    patient_id = data.get('patient_id')
    vaccine_id = data.get('vaccine_id')
    
    if not patient_id or not vaccine_id:
        return jsonify({'error': 'Patient ID and Vaccine ID required'}), 400
    
    patient = Patient.query.get(patient_id)
    vaccine = Vaccine.query.get(vaccine_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    if not vaccine:
        return jsonify({'error': 'Vaccine not found'}), 404
    
    patient_data = {
        'patient_id': patient.patient_id,
        'name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'weight': patient.weight,
        'height': patient.height,
        'bmi': patient.bmi,
        'diabetes': patient.diabetes,
        'hypertension': patient.hypertension,
        'heart_disease': patient.heart_disease,
        'liver_disease': patient.liver_disease,
        'kidney_disease': patient.kidney_disease,
        'autoimmune': patient.autoimmune,
        'cancer_history': patient.cancer_history,
        'drug_allergies': json.loads(patient.drug_allergies) if patient.drug_allergies else [],
        'food_allergies': json.loads(patient.food_allergies) if patient.food_allergies else [],
        'environmental_allergies': json.loads(patient.environmental_allergies) if patient.environmental_allergies else [],
        'medications': patient.medications,
        'family_history': patient.family_history,
        'notes': patient.notes
    }
    
    vaccine_data = {
        'name': vaccine.name,
        'manufacturer': vaccine.manufacturer,
        'vaccine_type': vaccine.vaccine_type,
        'ingredients': vaccine.ingredients,
        'active_ingredients': vaccine.active_ingredients,
        'excipients': vaccine.excipients,
        'contraindications': vaccine.contraindications,
        'common_side_effects': vaccine.common_side_effects,
        'rare_side_effects': vaccine.rare_side_effects
    }
    
    result = PredictionEngine.predict(patient_data, vaccine_data)
    
    user = User.query.filter_by(email=session['user_email']).first()
    
    prediction = Prediction(
        user_id=user.id,
        patient_id=patient.id,
        vaccine_id=vaccine.id,
        allergy_risk=result['allergy_risk']['risk_level'],
        allergy_risk_score=result['allergy_risk']['risk_score'],
        side_effect_probability=result['side_effects']['probability'],
        side_effect_severity=result['side_effects']['severity'],
        metabolic_response=result['metabolic']['response'],
        genetic_compatibility=result['genetic']['compatibility'],
        compatibility_score=result['compatibility_score'],
        risk_classification=result['risk_classification'],
        recommendation=result['recommendation']['recommendation'],
        high_risk_factors=json.dumps(result['recommendation']['high_risk_factors']),
        risk_factors_data=json.dumps(result['chart_data']['radar']),
        ingredient_analysis=json.dumps(result['chart_data']['bar']),
        risk_breakdown=json.dumps(result['chart_data']['pie'])
    )
    db.session.add(prediction)
    
    history = PredictionHistory(
        user_id=user.id,
        patient_name=patient.name,
        vaccine_name=vaccine.name,
        risk_level=result['risk_classification'],
        compatibility=result['genetic']['compatibility']
    )
    db.session.add(history)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'prediction': {
            'id': prediction.id,
            'patient': patient.name,
            'vaccine': vaccine.name,
            'allergy_risk': result['allergy_risk'],
            'side_effects': result['side_effects'],
            'metabolic': result['metabolic'],
            'genetic': result['genetic'],
            'compatibility_score': result['compatibility_score'],
            'risk_classification': result['risk_classification'],
            'recommendation': result['recommendation'],
            'chart_data': result['chart_data']
        }
    })


@app.route('/api/history', methods=['GET'])
def get_prediction_history():
    """Get prediction history for current user"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.filter_by(email=session['user_email']).first()
    
    history = PredictionHistory.query.filter_by(user_id=user.id).order_by(
        PredictionHistory.created_at.desc()
    ).limit(50).all()
    
    return jsonify({
        'history': [{
            'id': h.id,
            'patient_name': h.patient_name,
            'vaccine_name': h.vaccine_name,
            'risk_level': h.risk_level,
            'compatibility': h.compatibility,
            'created_at': h.created_at.isoformat()
        } for h in history]
    })


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics for the user"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.filter_by(email=session['user_email']).first()
    
    total_patients = Patient.query.filter_by(user_id=user.id).count()
    total_predictions = Prediction.query.filter_by(user_id=user.id).count()
    
    risk_counts = db.session.query(
        Prediction.risk_classification,
        db.func.count(Prediction.id)
    ).filter_by(user_id=user.id).group_by(Prediction.risk_classification).all()
    
    risk_distribution = {r[0]: r[1] for r in risk_counts}
    
    recent_predictions = Prediction.query.filter_by(user_id=user.id).order_by(
        Prediction.created_at.desc()
    ).limit(5).all()
    
    recent_activity = []
    for p in recent_predictions:
        patient = Patient.query.get(p.patient_id)
        vaccine = Vaccine.query.get(p.vaccine_id)
        recent_activity.append({
            'patient': patient.name if patient else 'Unknown',
            'vaccine': vaccine.name if vaccine else 'Unknown',
            'risk': p.risk_classification,
            'date': p.created_at.isoformat()
        })
    
    return jsonify({
        'statistics': {
            'total_patients': total_patients,
            'total_predictions': total_predictions,
            'risk_distribution': risk_distribution,
            'recent_activity': recent_activity
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        'status': 'healthy',
        'service': 'Digital Twin Medical Platform API',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
