# filepath: backend/routes.py
"""
API Routes for Digital Twin Medical Platform Backend
"""

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import json
import os

from .models import db, User, Patient, Vaccine, Prediction, PredictionHistory
from .data_processor import DataProcessor
from .prediction_engine import PredictionEngine

# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# ==================== FILE UPLOAD ROUTES ====================

@api.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Upload and process CSV file with patient data"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        try:
            # Read file content
            file_content = file.read()
            
            # Parse CSV
            result = DataProcessor.parse_csv(file_content)
            
            if result['patients']:
                # Clean data
                cleaned_patients = DataProcessor.clean_data(result['patients'])
                
                # Validate data
                validation = DataProcessor.validate_data(cleaned_patients)
                
                # Generate summary
                summary = DataProcessor.generate_summary(validation['valid'])
                
                return jsonify({
                    'success': True,
                    'message': f'Processed {len(validation["valid"])} patients',
                    'patients': validation['valid'][:10],  # Return first 10 for preview
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


@api.route('/save-patients', methods=['POST'])
def save_patients():
    """Save processed patient data to database"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    patients_data = data.get('patients', [])
    
    if not patients_data:
        return jsonify({'error': 'No patient data provided'}), 400
    
    # Get user
    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    saved_count = 0
    errors = []
    
    for patient_data in patients_data:
        try:
            # Check if patient already exists
            existing = Patient.query.filter_by(
                user_id=user.id,
                patient_id=patient_data.get('patient_id')
            ).first()
            
            if existing:
                # Update existing patient
                for key, value in patient_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Create new patient
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


# ==================== PATIENT MANAGEMENT ROUTES ====================

@api.route('/patients', methods=['GET'])
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


@api.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get specific patient details"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    return jsonify({
        'patient': {
            'id': patient.id,
            'patient_id': patient.patient_id,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'blood_type': patient.blood_type,
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
    })


@api.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """Delete a patient"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    db.session.delete(patient)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Patient deleted'})


# ==================== VACCINE ROUTES ====================

@api.route('/vaccines', methods=['GET'])
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


@api.route('/vaccines/<int:vaccine_id>', methods=['GET'])
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


# ==================== PREDICTION ROUTES ====================

@api.route('/predict', methods=['POST'])
def run_prediction():
    """Run prediction for patient-vaccine combination"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    patient_id = data.get('patient_id')
    vaccine_id = data.get('vaccine_id')
    
    if not patient_id or not vaccine_id:
        return jsonify({'error': 'Patient ID and Vaccine ID required'}), 400
    
    # Get patient and vaccine
    patient = Patient.query.get(patient_id)
    vaccine = Vaccine.query.get(vaccine_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    if not vaccine:
        return jsonify({'error': 'Vaccine not found'}), 404
    
    # Prepare patient data
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
    
    # Prepare vaccine data
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
    
    # Run prediction
    result = PredictionEngine.predict(patient_data, vaccine_data)
    
    # Get user
    user = User.query.filter_by(email=session['user_email']).first()
    
    # Save prediction to database
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
    
    # Add to history
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


@api.route('/predict/batch', methods=['POST'])
def run_batch_prediction():
    """Run prediction for multiple patients with a vaccine"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    patient_ids = data.get('patient_ids', [])
    vaccine_id = data.get('vaccine_id')
    
    if not patient_ids or not vaccine_id:
        return jsonify({'error': 'Patient IDs and Vaccine ID required'}), 400
    
    vaccine = Vaccine.query.get(vaccine_id)
    if not vaccine:
        return jsonify({'error': 'Vaccine not found'}), 404
    
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
    
    results = []
    for patient_id in patient_ids:
        patient = Patient.query.get(patient_id)
        if not patient:
            continue
        
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
            'medications': patient.medications
        }
        
        result = PredictionEngine.predict(patient_data, vaccine_data)
        
        results.append({
            'patient_id': patient.id,
            'patient_name': patient.name,
            'vaccine': vaccine.name,
            'allergy_risk': result['allergy_risk']['risk_level'],
            'compatibility_score': result['compatibility_score'],
            'risk_classification': result['risk_classification']
        })
    
    return jsonify({
        'success': True,
        'results': results,
        'total': len(results)
    })


# ==================== HISTORY ROUTES ====================

@api.route('/history', methods=['GET'])
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


@api.route('/predictions/<int:prediction_id>', methods=['GET'])
def get_prediction_detail(prediction_id):
    """Get detailed prediction result"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    prediction = Prediction.query.get(prediction_id)
    if not prediction:
        return jsonify({'error': 'Prediction not found'}), 404
    
    patient = Patient.query.get(prediction.patient_id)
    vaccine = Vaccine.query.get(prediction.vaccine_id)
    
    return jsonify({
        'prediction': {
            'id': prediction.id,
            'patient': patient.name if patient else 'Unknown',
            'vaccine': vaccine.name if vaccine else 'Unknown',
            'allergy_risk': prediction.allergy_risk,
            'allergy_risk_score': prediction.allergy_risk_score,
            'side_effect_probability': prediction.side_effect_probability,
            'side_effect_severity': prediction.side_effect_severity,
            'metabolic_response': prediction.metabolic_response,
            'genetic_compatibility': prediction.genetic_compatibility,
            'compatibility_score': prediction.compatibility_score,
            'risk_classification': prediction.risk_classification,
            'recommendation': prediction.recommendation,
            'high_risk_factors': json.loads(prediction.high_risk_factors) if prediction.high_risk_factors else [],
            'chart_data': {
                'radar': json.loads(prediction.risk_factors_data) if prediction.risk_factors_data else {},
                'bar': json.loads(prediction.ingredient_analysis) if prediction.ingredient_analysis else {},
                'pie': json.loads(prediction.risk_breakdown) if prediction.risk_breakdown else {}
            },
            'created_at': prediction.created_at.isoformat()
        }
    })


# ==================== STATISTICS ROUTES ====================

@api.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics for the user"""
    
    if 'user_email' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.filter_by(email=session['user_email']).first()
    
    # Patient statistics
    total_patients = Patient.query.filter_by(user_id=user.id).count()
    
    # Prediction statistics
    total_predictions = Prediction.query.filter_by(user_id=user.id).count()
    
    # Risk distribution
    risk_counts = db.session.query(
        Prediction.risk_classification,
        db.func.count(Prediction.id)
    ).filter_by(user_id=user.id).group_by(Prediction.risk_classification).all()
    
    risk_distribution = {r[0]: r[1] for r in risk_counts}
    
    # Recent activity
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


# ==================== HEALTH CHECK ====================

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    
    return jsonify({
        'status': 'healthy',
        'service': 'Digital Twin Medical Platform API',
        'version': '1.0.0'
    })