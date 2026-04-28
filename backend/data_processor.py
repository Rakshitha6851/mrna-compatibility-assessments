# filepath: backend/data_processor.py
"""
Data Processor for CSV Upload and Patient Data Processing
"""

import csv
import json
from io import StringIO
from datetime import datetime


class DataProcessor:
    """Process and validate patient data from CSV files"""
    
    # Required fields for patient data
    REQUIRED_FIELDS = [
        'patient_id', 'name', 'age', 'gender'
    ]
    
    # Optional fields
    OPTIONAL_FIELDS = [
        'blood_type', 'weight', 'height', 'bmi',
        'diabetes', 'hypertension', 'heart_disease', 'liver_disease',
        'kidney_disease', 'autoimmune', 'cancer_history',
        'drug_allergies', 'food_allergies', 'environmental_allergies',
        'medications', 'family_history', 'notes',
        'hepatitis', 'cirrhosis', 'immunodeficiency', 'anaphylaxis_history',
        'previous_vaccine_reaction'
    ]
    
    # Field mappings for CSV columns
    FIELD_MAPPINGS = {
        'patient_id': ['patient_id', 'patientid', 'id', 'patient_id'],
        'name': ['name', 'patient_name', 'full_name', 'patientname'],
        'age': ['age', 'patient_age'],
        'gender': ['gender', 'sex', 'patient_gender'],
        'blood_type': ['blood_type', 'bloodtype', 'blood_group'],
        'weight': ['weight', 'body_weight', 'weight_kg'],
        'height': ['height', 'body_height', 'height_cm'],
        'bmi': ['bmi', 'body_mass_index'],
        'diabetes': ['diabetes', 'diabetic', 'has_diabetes'],
        'hypertension': ['hypertension', 'high_bp', 'has_hypertension'],
        'heart_disease': ['heart_disease', 'cardiac', 'has_heart_disease'],
        'liver_disease': ['liver_disease', 'hepatic', 'has_liver_disease'],
        'kidney_disease': ['kidney_disease', 'renal', 'has_kidney_disease'],
        'autoimmune': ['autoimmune', 'autoimmune_disease'],
        'cancer_history': ['cancer_history', 'cancer', 'has_cancer'],
        'drug_allergies': ['drug_allergies', 'drug_allergy', 'allergy_drug'],
        'food_allergies': ['food_allergies', 'food_allergy', 'allergy_food'],
        'environmental_allergies': ['environmental_allergies', 'env_allergy', 'allergy_env'],
        'medications': ['medications', 'current_medications', 'meds'],
        'family_history': ['family_history', 'family_medical_history'],
        'notes': ['notes', 'remarks', 'comments']
    }
    
    @staticmethod
    def parse_csv(file_content):
        """Parse CSV file and return list of patient records"""
        
        patients = []
        errors = []
        
        try:
            # Try different encodings
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('latin-1')
            except:
                content = file_content.decode('cp1252')
        
        reader = csv.DictReader(StringIO(content))
        
        # Normalize column names
        normalized_fieldnames = []
        for field in reader.fieldnames:
            normalized_fieldnames.append(DataProcessor.normalize_field_name(field))
        
        reader = csv.DictReader(StringIO(content), fieldnames=normalized_fieldnames)
        next(reader)  # Skip header row
        
        row_num = 1
        for row in reader:
            row_num += 1
            
            # Skip empty rows
            if not row or not any(row.values()):
                continue
            
            # Validate required fields
            missing_fields = []
            for field in DataProcessor.REQUIRED_FIELDS:
                if not row.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                continue
            
            # Process and clean the data
            patient = DataProcessor.process_patient_data(row)
            
            if patient:
                patients.append(patient)
            else:
                errors.append(f"Row {row_num}: Invalid data format")
        
        return {
            'patients': patients,
            'errors': errors,
            'total': len(patients)
        }
    
    @staticmethod
    def normalize_field_name(field_name):
        """Normalize CSV column name to standard format"""
        
        field_name = field_name.strip().lower().replace(' ', '_').replace('-', '_')
        
        # Check against mappings
        for standard_name, variations in DataProcessor.FIELD_MAPPINGS.items():
            if field_name in variations:
                return standard_name
        
        return field_name
    
    @staticmethod
    def process_patient_data(row):
        """Process and clean patient data from a row"""
        
        patient = {}
        
        for field, value in row.items():
            if value is None or value == '':
                continue
            
            # Clean the value
            value = str(value).strip()
            
            # Convert boolean fields
            if field in ['diabetes', 'hypertension', 'heart_disease', 'liver_disease',
                        'kidney_disease', 'autoimmune', 'cancer_history', 'hepatitis',
                        'cirrhosis', 'immunodeficiency', 'anaphylaxis_history',
                        'previous_vaccine_reaction']:
                patient[field] = DataProcessor.parse_boolean(value)
                continue
            
            # Parse numeric fields
            if field in ['age', 'weight', 'height', 'bmi']:
                try:
                    patient[field] = float(value) if '.' in value else int(value)
                except ValueError:
                    patient[field] = None
                continue
            
            # Parse JSON fields
            if field in ['drug_allergies', 'food_allergies', 'environmental_allergies']:
                patient[field] = DataProcessor.parse_list_field(value)
                continue
            
            patient[field] = value
        
        return patient
    
    @staticmethod
    def parse_boolean(value):
        """Parse boolean values from various formats"""
        
        value = str(value).lower().strip()
        
        true_values = ['yes', 'y', 'true', '1', 't', 'positive', 'present', 'known']
        false_values = ['no', 'n', 'false', '0', 'f', 'negative', 'absent', 'none', 'unknown']
        
        if value in true_values:
            return True
        elif value in false_values:
            return False
        
        return None
    
    @staticmethod
    def parse_list_field(value):
        """Parse list fields (allergies, medications) from CSV"""
        
        # Try JSON first
        try:
            return json.loads(value)
        except:
            pass
        
        # Try pipe-separated
        if '|' in value:
            return [v.strip() for v in value.split('|') if v.strip()]
        
        # Try comma-separated
        if ',' in value:
            return [v.strip() for v in value.split(',') if v.strip()]
        
        # Return as single item
        return [value] if value else []
    
    @staticmethod
    def clean_data(patients):
        """Clean and normalize patient data"""
        
        cleaned = []
        
        for patient in patients:
            # Calculate BMI if not provided
            if 'weight' in patient and 'height' in patient:
                try:
                    weight = float(patient['weight'])
                    height = float(patient['height']) / 100  # Convert cm to m
                    patient['bmi'] = round(weight / (height * height), 2)
                except:
                    pass
            
            # Calculate age if not provided
            if 'age' not in patient or not patient['age']:
                patient['age'] = None
            
            # Normalize gender
            if 'gender' in patient:
                gender = str(patient['gender']).lower().strip()
                if gender in ['m', 'male', 'man', 'boy']:
                    patient['gender'] = 'Male'
                elif gender in ['f', 'female', 'woman', 'girl']:
                    patient['gender'] = 'Female'
                else:
                    patient['gender'] = 'Other'
            
            # Normalize blood type
            if 'blood_type' in patient:
                patient['blood_type'] = patient['blood_type'].upper().replace(' ', '')
            
            cleaned.append(patient)
        
        return cleaned
    
    @staticmethod
    def validate_data(patients):
        """Validate patient data and return validation results"""
        
        validation_results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }
        
        for i, patient in enumerate(patients):
            errors = []
            warnings = []
            
            # Check required fields
            for field in DataProcessor.REQUIRED_FIELDS:
                if not patient.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate age
            if patient.get('age'):
                if patient['age'] < 0 or patient['age'] > 120:
                    errors.append(f"Invalid age: {patient['age']}")
            
            # Validate weight
            if patient.get('weight'):
                if patient['weight'] < 0 or patient['weight'] > 500:
                    warnings.append(f"Unusual weight: {patient['weight']} kg")
            
            # Validate height
            if patient.get('height'):
                if patient['height'] < 20 or patient['height'] > 300:
                    warnings.append(f"Unusual height: {patient['height']} cm")
            
            # Validate BMI
            if patient.get('bmi'):
                if patient['bmi'] < 10 or patient['bmi'] > 60:
                    warnings.append(f"Unusual BMI: {patient['bmi']}")
            
            if errors:
                validation_results['invalid'].append({
                    'row': i + 1,
                    'patient_id': patient.get('patient_id'),
                    'errors': errors
                })
            else:
                patient['row'] = i + 1
                validation_results['valid'].append(patient)
            
            if warnings:
                validation_results['warnings'].append({
                    'row': i + 1,
                    'patient_id': patient.get('patient_id'),
                    'warnings': warnings
                })
        
        return validation_results
    
    @staticmethod
    def encode_medical_data(patient):
        """Encode medical data for ML model input"""
        
        encoded = {}
        
        # Numeric fields - normalize to 0-1 range
        numeric_fields = ['age', 'weight', 'height', 'bmi']
        for field in numeric_fields:
            if patient.get(field) is not None:
                encoded[field] = float(patient[field])
        
        # Boolean fields - convert to 0/1
        bool_fields = ['diabetes', 'hypertension', 'heart_disease', 'liver_disease',
                      'kidney_disease', 'autoimmune', 'cancer_history']
        for field in bool_fields:
            encoded[field] = 1 if patient.get(field) else 0
        
        # Gender encoding
        gender = patient.get('gender', '').lower()
        encoded['gender_male'] = 1 if gender == 'male' else 0
        encoded['gender_female'] = 1 if gender == 'female' else 0
        
        # Blood type encoding
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        for bt in blood_types:
            encoded[f'blood_type_{bt}'] = 1 if patient.get('blood_type') == bt else 0
        
        # Allergy count
        drug_allergies = patient.get('drug_allergies', [])
        food_allergies = patient.get('food_allergies', [])
        env_allergies = patient.get('environmental_allergies', [])
        
        encoded['drug_allergy_count'] = len(drug_allergies) if isinstance(drug_allergies, list) else 0
        encoded['food_allergy_count'] = len(food_allergies) if isinstance(food_allergies, list) else 0
        encoded['env_allergy_count'] = len(env_allergies) if isinstance(env_allergies, list) else 0
        
        return encoded
    
    @staticmethod
    def generate_summary(patients):
        """Generate summary statistics for patient dataset"""
        
        summary = {
            'total_patients': len(patients),
            'demographics': {},
            'conditions': {},
            'allergies': {}
        }
        
        # Demographics
        ages = [p.get('age') for p in patients if p.get('age')]
        if ages:
            summary['demographics']['average_age'] = round(sum(ages) / len(ages), 1)
            summary['demographics']['min_age'] = min(ages)
            summary['demographics']['max_age'] = max(ages)
        
        genders = {}
        for p in patients:
            g = p.get('gender', 'Unknown')
            genders[g] = genders.get(g, 0) + 1
        summary['demographics']['gender_distribution'] = genders
        
        # Conditions
        conditions = ['diabetes', 'hypertension', 'heart_disease', 'liver_disease',
                     'kidney_disease', 'autoimmune', 'cancer_history']
        for cond in conditions:
            count = sum(1 for p in patients if p.get(cond))
            summary['conditions'][cond] = count
        
        # Allergies
        drug_allergy_count = 0
        food_allergy_count = 0
        for p in patients:
            if isinstance(p.get('drug_allergies'), list):
                drug_allergy_count += len(p['drug_allergies'])
            if isinstance(p.get('food_allergies'), list):
                food_allergy_count += len(p['food_allergies'])
        
        summary['allergies']['total_drug_allergies'] = drug_allergy_count
        summary['allergies']['total_food_allergies'] = food_allergy_count
        summary['allergies']['patients_with_allergies'] = sum(
            1 for p in patients 
            if p.get('drug_allergies') or p.get('food_allergies') or p.get('environmental_allergies')
        )
        
        return summary