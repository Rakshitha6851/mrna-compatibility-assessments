# filepath: backend/models.py
"""
Database models for Digital Twin Medical Platform
"""

from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ==================== MODELS ====================

class User(db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = db.relationship('Patient', backref='user', lazy=True, cascade='all, delete-orphan')
    predictions = db.relationship('Prediction', backref='user', lazy=True, cascade='all, delete-orphan')


class Patient(db.Model):
    """Patient data model"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.String(50), nullable=False)  # External patient ID
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    blood_type = db.Column(db.String(10))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    bmi = db.Column(db.Float)
    
    # Medical conditions
    diabetes = db.Column(db.Boolean, default=False)
    hypertension = db.Column(db.Boolean, default=False)
    heart_disease = db.Column(db.Boolean, default=False)
    liver_disease = db.Column(db.Boolean, default=False)
    kidney_disease = db.Column(db.Boolean, default=False)
    autoimmune = db.Column(db.Boolean, default=False)
    cancer_history = db.Column(db.Boolean, default=False)
    
    # Allergies
    drug_allergies = db.Column(db.Text)  # JSON string of drug allergies
    food_allergies = db.Column(db.Text)  # JSON string of food allergies
    environmental_allergies = db.Column(db.Text)  # JSON string of environmental allergies
    
    # Lab values
    liver_score = db.Column(db.Float)  # Calculated liver function score
    immune_score = db.Column(db.Float)  # Calculated immune function score
    allergy_index = db.Column(db.Float)  # Calculated allergy index
    
    # Additional data
    medications = db.Column(db.Text)  # Current medications
    family_history = db.Column(db.Text)  # Family medical history
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predictions = db.relationship('Prediction', backref='patient', lazy=True, cascade='all, delete-orphan')


class Vaccine(db.Model):
    """Vaccine information model"""
    __tablename__ = 'vaccines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100))
    vaccine_type = db.Column(db.String(50))  # mRNA, Vector, Inactivated, etc.
    
    # Ingredients stored as JSON
    ingredients = db.Column(db.Text)  # JSON string of ingredients
    active_ingredients = db.Column(db.Text)  # JSON string of active ingredients
    excipients = db.Column(db.Text)  # JSON string of excipients
    
    # Safety information
    contraindications = db.Column(db.Text)
    common_side_effects = db.Column(db.Text)
    rare_side_effects = db.Column(db.Text)
    
    # Usage
    age_min = db.Column(db.Integer)  # Minimum age
    age_max = db.Column(db.Integer)  # Maximum age
    dose_count = db.Column(db.Integer)  # Number of doses
    interval_days = db.Column(db.Integer)  # Days between doses
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prediction(db.Model):
    """Prediction results model"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    vaccine_id = db.Column(db.Integer, db.ForeignKey('vaccines.id'), nullable=False)
    
    # Prediction results
    allergy_risk = db.Column(db.String(20))  # Low, Medium, High, Critical
    allergy_risk_score = db.Column(db.Float)  # 0-100 score
    
    side_effect_probability = db.Column(db.Float)  # 0-100 percentage
    side_effect_severity = db.Column(db.String(20))  # Mild, Moderate, Severe
    
    metabolic_response = db.Column(db.String(50))  # Normal, Slow, Fast, Abnormal
    genetic_compatibility = db.Column(db.String(20))  # Compatible, Partial, Incompatible
    
    # Compatibility
    compatibility_score = db.Column(db.Float)  # 0-100 weighted score
    risk_classification = db.Column(db.String(20))  # Safe, Monitor, Reformulate
    
    # AI Decision
    recommendation = db.Column(db.Text)  # Final recommendation message
    high_risk_factors = db.Column(db.Text)  # JSON string of high-risk factors
    
    # Data for charts
    risk_factors_data = db.Column(db.Text)  # JSON for radar chart
    ingredient_analysis = db.Column(db.Text)  # JSON for bar chart
    risk_breakdown = db.Column(db.Text)  # JSON for pie chart
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PredictionHistory(db.Model):
    """History of all predictions for quick access"""
    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_name = db.Column(db.String(100))
    vaccine_name = db.Column(db.String(100))
    risk_level = db.Column(db.String(20))
    compatibility = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ==================== DATABASE INIT ====================

def init_database(app):
    """Initialize database with sample vaccines"""
    with app.app_context():
        db.create_all()
        
        # Add sample vaccines if none exist
        if Vaccine.query.count() == 0:
            vaccines = [
                {
                    "name": "Pfizer-BioNTech COVID-19",
                    "manufacturer": "Pfizer/BioNTech",
                    "vaccine_type": "mRNA",
                    "ingredients": '["mRNA", "Lipids", "Potassium chloride", "Monobasic potassium phosphate", "Sodium chloride", "Dibasic sodium phosphate dihydrate", "Sucrose"]',
                    "active_ingredients": '["mRNA (BNT162b2)"]',
                    "excipients": '["ALC-0315", "ALC-0159", "DSPC", "Cholesterol", "Tromethamine", "Tromethamine hydrochloride"]',
                    "contraindications": '["Severe allergic reaction to any component of the vaccine", "Known allergy to polyethylene glycol (PEG)"]',
                    "common_side_effects": '["Pain at injection site", "Fatigue", "Headache", "Muscle pain", "Chills", "Joint pain", "Fever"]',
                    "rare_side_effects": '["Anaphylaxis", "Myocarditis", "Pericarditis"]',
                    "age_min": 12,
                    "age_max": 999,
                    "dose_count": 2,
                    "interval_days": 21
                },
                {
                    "name": "Moderna COVID-19",
                    "manufacturer": "ModernaTX, Inc.",
                    "vaccine_type": "mRNA",
                    "ingredients": '["mRNA-1273", "Lipids", "Tromethamine", "Tromethamine hydrochloride", "Acetic acid", "Sodium acetate trihydrate", "Sucrose"]',
                    "active_ingredients": '["mRNA-1273"]',
                    "excipients": '["SM-102", "PEG2000-DMG", "DSPC", "Cholesterol", "1,2-distearoyl-sn-glycero-3-phosphocholine"]',
                    "contraindications": '["Severe allergic reaction to any component of the vaccine"]',
                    "common_side_effects": '["Pain at injection site", "Fatigue", "Headache", "Nausea", "Chills", "Fever"]',
                    "rare_side_effects": '["Anaphylaxis", "Myocarditis", "Facial swelling"]',
                    "age_min": 18,
                    "age_max": 999,
                    "dose_count": 2,
                    "interval_days": 28
                },
                {
                    "name": "Oxford-AstraZeneca COVID-19",
                    "manufacturer": "AstraZeneca",
                    "vaccine_type": "Viral Vector",
                    "ingredients": '["ChAdOx1-S", "L-Histidine", "L-Histidine hydrochloride", "Magnesium chloride hexahydrate", "Ethanol", "Sucrose", "Sodium chloride", "EDTA"]',
                    "active_ingredients": '["ChAdOx1-S recombinant"]',
                    "excipients": '["L-Histidine", "Magnesium chloride", "EDTA", "Sucrose", "Polysorbate 80"]',
                    "contraindications": '["Severe allergic reaction to any component", "History of capillary leak syndrome", "Thrombosis with thrombocytopenia syndrome"]',
                    "common_side_effects": '["Pain at injection site", "Headache", "Nausea", "Fatigue", "Muscle pain"]',
                    "rare_side_effects": '["Anaphylaxis", "Thrombosis", "Thrombocytopenia"]',
                    "age_min": 18,
                    "age_max": 999,
                    "dose_count": 2,
                    "interval_days": 28
                },
                {
                    "name": "Johnson & Johnson COVID-19",
                    "manufacturer": "Janssen (Johnson & Johnson)",
                    "vaccine_type": "Viral Vector",
                    "ingredients": '["Ad26.COV2.S", "Citric acid monohydrate", "Trisodium citrate dihydrate", "Ethanol", "2-Hydroxypropyl-β-cyclodextrin", "Polysorbate-80", "Sodium chloride"]',
                    "active_ingredients": '["Ad26.COV2.S recombinant"]',
                    "excipients": '["Citric acid", "Trisodium citrate", "2-Hydroxypropyl-β-cyclodextrin", "Polysorbate 80"]',
                    "contraindications": '["Severe allergic reaction to any component", "History of Guillain-Barré syndrome", "Thrombosis with thrombocytopenia"]',
                    "common_side_effects": '["Pain at injection site", "Headache", "Fatigue", "Muscle pain", "Nausea"]',
                    "rare_side_effects": '["Anaphylaxis", "Thrombosis", "Guillain-Barré syndrome"]',
                    "age_min": 18,
                    "age_max": 999,
                    "dose_count": 1,
                    "interval_days": 0
                },
                {
                    "name": "Influenza (Flu) Vaccine",
                    "manufacturer": "Various",
                    "vaccine_type": "Inactivated",
                    "ingredients": '["Inactivated influenza virus", "Egg protein", "Gelatin", "Sodium chloride", "Potassium chloride"]',
                    "active_ingredients": '["Inactivated influenza virus strains"]',
                    "excipients": '["Egg albumin", "Gelatin", "Sodium chloride", "Potassium chloride"]',
                    "contraindications": '["Severe allergic reaction to egg proteins", "History of Guillain-Barré syndrome within 6 weeks of flu vaccine"]',
                    "common_side_effects": '["Soreness at injection site", "Low-grade fever", "Fatigue", "Headache"]',
                    "rare_side_effects": '["Anaphylaxis", "Guillain-Barré syndrome"]',
                    "age_min": 6,
                    "age_max": 999,
                    "dose_count": 1,
                    "interval_days": 0
                },
                {
                    "name": "Hepatitis B Vaccine",
                    "manufacturer": "Merck/GSK",
                    "vaccine_type": "Recombinant",
                    "ingredients": '["HBsAg", "Aluminum hydroxide", "Yeast protein", "Sodium chloride"]',
                    "active_ingredients": '["Recombinant hepatitis B surface antigen"]',
                    "excipients": '["Aluminum phosphate", "Yeast extract", "Sodium chloride"]',
                    "contraindications": '["Severe allergic reaction to any component", "Yeast allergy"]',
                    "common_side_effects": '["Pain at injection site", "Low-grade fever", "Fatigue"]',
                    "rare_side_effects": '["Anaphylaxis", "Autoimmune disorders"]',
                    "age_min": 0,
                    "age_max": 999,
                    "dose_count": 3,
                    "interval_days": 30
                }
            ]
            
            for v in vaccines:
                vaccine = Vaccine(**v)
                db.session.add(vaccine)
            
            db.session.commit()
            print("Sample vaccines added to database")