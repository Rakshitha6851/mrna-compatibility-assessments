# filepath: backend/prediction_engine.py
"""
Prediction Engine for Allergy Risk and Vaccine Safety Analysis
"""

import json
import random
from datetime import datetime


class PredictionEngine:
    """Core prediction engine for vaccine safety analysis"""
    
    # Risk factor weights for different medical conditions
    CONDITION_WEIGHTS = {
        'diabetes': 15,
        'hypertension': 12,
        'heart_disease': 20,
        'liver_disease': 25,
        'kidney_disease': 20,
        'autoimmune': 25,
        'cancer_history': 18
    }
    
    # Allergy severity multipliers
    ALLERGY_SEVERITY = {
        'severe': 2.0,
        'moderate': 1.5,
        'mild': 1.0
    }
    
    # Vaccine ingredient risk categories
    INGREDIENT_RISK = {
        'mRNA': {'risk': 0.1, 'description': 'Genetic material - generally safe'},
        'Lipids': {'risk': 0.15, 'description': 'Fat molecules for delivery - rare allergic reactions'},
        'PEG': {'risk': 0.3, 'description': 'Polyethylene glycol - known allergen for some'},
        'Polysorbate 80': {'risk': 0.25, 'description': 'Emulsifier - can cause allergic reactions'},
        'Egg protein': {'risk': 0.4, 'description': 'Egg allergen - contraindicated for egg allergy'},
        'Yeast': {'risk': 0.35, 'description': 'Yeast allergen - contraindicated for yeast allergy'},
        'Gelatin': {'risk': 0.2, 'description': 'Gelatin - rare allergic reactions'},
        'Aluminum': {'risk': 0.1, 'description': 'Adjuvant - generally safe'},
        'Sodium chloride': {'risk': 0.05, 'description': 'Salt - very low risk'},
        'Sucrose': {'risk': 0.05, 'description': 'Sugar - very low risk'},
        'Tromethamine': {'risk': 0.1, 'description': 'Buffer - generally safe'},
        'Acetic acid': {'risk': 0.1, 'description': 'Acid - generally safe'},
        'Cholesterol': {'risk': 0.05, 'description': 'Fat - very low risk'},
        'Ethanol': {'risk': 0.15, 'description': 'Alcohol - rare reactions'},
        'Citric acid': {'risk': 0.1, 'description': 'Citrus acid - generally safe'}
    }
    
    @staticmethod
    def calculate_liver_score(patient_data):
        """Calculate liver function score (0-100)"""
        score = 75  # Base score
        
        # Adjust for liver disease
        if patient_data.get('liver_disease'):
            score -= 40
        if patient_data.get('hepatitis'):
            score -= 25
        if patient_data.get('cirrhosis'):
            score -= 35
        
        # Adjust for medications that affect liver
        medications = patient_data.get('medications', '').lower()
        hepatotoxic_meds = ['acetaminophen', 'statins', 'anticonvulsants', 'antibiotics']
        for med in hepatotoxic_meds:
            if med in medications:
                score -= 10
        
        # Age factor
        age = patient_data.get('age', 40)
        if age > 60:
            score -= 10
        elif age > 50:
            score -= 5
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_immune_score(patient_data):
        """Calculate immune function score (0-100)"""
        score = 80  # Base score
        
        # Adjust for conditions
        if patient_data.get('autoimmune'):
            score -= 30
        if patient_data.get('immunodeficiency'):
            score -= 35
        if patient_data.get('cancer_history'):
            score -= 20
        
        # Adjust for medications
        medications = patient_data.get('medications', '').lower()
        immunosuppressants = ['corticosteroids', 'prednisone', 'cyclosporine', 'methotrexate']
        for med in immunosuppressants:
            if med in medications:
                score -= 15
        
        # Age factor
        age = patient_data.get('age', 40)
        if age > 70:
            score -= 15
        elif age > 60:
            score -= 10
        
        # BMI factor
        bmi = patient_data.get('bmi', 25)
        if bmi > 35 or bmi < 18:
            score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_allergy_index(patient_data):
        """Calculate allergy index (0-100)"""
        score = 20  # Base score
        
        # Drug allergies
        drug_allergies = patient_data.get('drug_allergies', [])
        if isinstance(drug_allergies, str):
            try:
                drug_allergies = json.loads(drug_allergies)
            except:
                drug_allergies = [drug_allergies] if drug_allergies else []
        
        for allergy in drug_allergies:
            if allergy:
                score += 15
        
        # Food allergies
        food_allergies = patient_data.get('food_allergies', [])
        if isinstance(food_allergies, str):
            try:
                food_allergies = json.loads(food_allergies)
            except:
                food_allergies = [food_allergies] if food_allergies else []
        
        for allergy in food_allergies:
            if allergy:
                score += 12
        
        # Environmental allergies
        env_allergies = patient_data.get('environmental_allergies', [])
        if isinstance(env_allergies, str):
            try:
                env_allergies = json.loads(env_allergies)
            except:
                env_allergies = [env_allergies] if env_allergies else []
        
        for allergy in env_allergies:
            if allergy:
                score += 8
        
        # History of anaphylaxis
        if patient_data.get('anaphylaxis_history'):
            score += 25
        
        # Previous vaccine reactions
        if patient_data.get('previous_vaccine_reaction'):
            score += 20
        
        return min(100, score)
    
    @staticmethod
    def predict_allergy_risk(patient_data, vaccine_data):
        """Predict allergy risk for a patient-vaccine combination"""
        
        # Calculate base scores
        liver_score = PredictionEngine.calculate_liver_score(patient_data)
        immune_score = PredictionEngine.calculate_immune_score(patient_data)
        allergy_index = PredictionEngine.calculate_allergy_index(patient_data)
        
        # Get vaccine ingredients
        ingredients = []
        try:
            ingredients = json.loads(vaccine_data.get('ingredients', '[]'))
        except:
            ingredients = []
        
        # Calculate ingredient risk
        ingredient_risk_score = 0
        problematic_ingredients = []
        
        for ingredient in ingredients:
            ingredient_upper = ingredient.upper()
            
            # Check against known allergies
            patient_allergies = []
            drug_allergies = patient_data.get('drug_allergies', [])
            if isinstance(drug_allergies, str):
                try:
                    patient_allergies = json.loads(drug_allergies)
                except:
                    patient_allergies = []
            
            # Check for specific ingredient concerns
            for risk_ingredient, risk_data in PredictionEngine.INGREDIENT_RISK.items():
                if risk_ingredient.upper() in ingredient_upper:
                    ingredient_risk_score += risk_data['risk'] * 100
                    
                    # Check if patient has related allergy
                    for patient_allergy in patient_allergies:
                        if risk_ingredient.lower() in str(patient_allergy).lower():
                            ingredient_risk_score += 30
                            problematic_ingredients.append({
                                'ingredient': risk_ingredient,
                                'reason': f'Patient has allergy to {risk_ingredient.lower()}'
                            })
        
        # Calculate final allergy risk score
        risk_score = (
            allergy_index * 0.4 +
            ingredient_risk_score * 0.3 +
            (100 - liver_score) * 0.15 +
            (100 - immune_score) * 0.15
        )
        
        # Determine risk level
        if risk_score < 20:
            risk_level = 'Low'
        elif risk_score < 40:
            risk_level = 'Medium'
        elif risk_score < 60:
            risk_level = 'High'
        else:
            risk_level = 'Critical'
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'liver_score': round(liver_score, 2),
            'immune_score': round(immune_score, 2),
            'allergy_index': round(allergy_index, 2),
            'problematic_ingredients': problematic_ingredients
        }
    
    @staticmethod
    def predict_side_effects(patient_data, vaccine_data):
        """Predict probability and severity of side effects"""
        
        base_probability = 25  # Base 25%
        
        # Adjust for patient conditions
        for condition, weight in PredictionEngine.CONDITION_WEIGHTS.items():
            if patient_data.get(condition):
                base_probability += weight * 0.3
        
        # Age adjustments
        age = patient_data.get('age', 40)
        if age < 18:
            base_probability += 5
        elif age > 65:
            base_probability += 10
        
        # Vaccine type adjustments
        vaccine_type = vaccine_data.get('vaccine_type', '').lower()
        if 'mrna' in vaccine_type:
            base_probability += 5  # Higher reactogenicity
        elif 'vector' in vaccine_type:
            base_probability += 3
        
        # Determine severity
        if base_probability < 30:
            severity = 'Mild'
        elif base_probability < 50:
            severity = 'Moderate'
        else:
            severity = 'Severe'
        
        return {
            'probability': round(min(95, base_probability), 2),
            'severity': severity
        }
    
    @staticmethod
    def analyze_metabolic_response(patient_data, vaccine_data):
        """Analyze metabolic response to vaccine"""
        
        # Calculate metabolic score
        metabolic_score = 70
        
        # Liver function impact
        liver_score = PredictionEngine.calculate_liver_score(patient_data)
        if liver_score < 50:
            metabolic_score -= 20
            response_type = 'Slow - Impaired liver function may delay vaccine metabolism'
        elif liver_score < 70:
            metabolic_score -= 10
            response_type = 'Normal with monitoring'
        else:
            response_type = 'Normal'
        
        # Kidney function impact
        if patient_data.get('kidney_disease'):
            metabolic_score -= 15
            response_type = 'Abnormal - Kidney function may affect vaccine clearance'
        
        # BMI impact
        bmi = patient_data.get('bmi', 25)
        if bmi > 30:
            metabolic_score -= 5
        elif bmi < 18:
            metabolic_score -= 5
        
        # Diabetes impact
        if patient_data.get('diabetes'):
            metabolic_score -= 10
        
        if metabolic_score >= 60:
            final_response = 'Normal'
        elif metabolic_score >= 40:
            final_response = 'Slow'
        else:
            final_response = 'Abnormal'
        
        return {
            'response': final_response,
            'details': response_type,
            'metabolic_score': round(metabolic_score, 2)
        }
    
    @staticmethod
    def analyze_genetic_compatibility(patient_data, vaccine_data):
        """Analyze genetic compatibility (simplified)"""
        
        compatibility_score = 85
        
        # HLA factors (simplified - in real scenario would use genetic data)
        # Check for known genetic risk factors
        
        # Age-related genetic factors
        age = patient_data.get('age', 40)
        if age > 70:
            compatibility_score -= 10
        elif age > 60:
            compatibility_score -= 5
        
        # Autoimmune conditions
        if patient_data.get('autoimmune'):
            compatibility_score -= 20
        
        # Previous adverse reactions
        if patient_data.get('previous_vaccine_reaction'):
            compatibility_score -= 25
        
        # Determine compatibility level
        if compatibility_score >= 70:
            compatibility = 'Compatible'
        elif compatibility_score >= 50:
            compatibility = 'Partial'
        else:
            compatibility = 'Incompatible'
        
        return {
            'compatibility': compatibility,
            'score': round(compatibility_score, 2)
        }
    
    @staticmethod
    def calculate_compatibility_score(allergy_risk, side_effects, metabolic, genetic):
        """Calculate weighted compatibility score"""
        
        # Weights for different factors
        weights = {
            'allergy': 0.35,
            'side_effects': 0.25,
            'metabolic': 0.20,
            'genetic': 0.20
        }
        
        # Convert risk levels to scores
        risk_scores = {
            'Low': 100,
            'Medium': 70,
            'High': 40,
            'Critical': 10
        }
        
        allergy_score = risk_scores.get(allergy_risk['risk_level'], 50)
        side_effect_score = 100 - side_effects['probability']
        
        metabolic_scores = {'Normal': 100, 'Slow': 70, 'Abnormal': 40}
        metabolic_score = metabolic_scores.get(metabolic['response'], 50)
        
        genetic_score = genetic['score']
        
        # Calculate weighted score
        weighted_score = (
            allergy_score * weights['allergy'] +
            side_effect_score * weights['side_effects'] +
            metabolic_score * weights['metabolic'] +
            genetic_score * weights['genetic']
        )
        
        return round(weighted_score, 2)
    
    @staticmethod
    def determine_risk_classification(compatibility_score):
        """Determine risk classification"""
        
        if compatibility_score >= 70:
            return 'Safe'
        elif compatibility_score >= 50:
            return 'Monitor'
        else:
            return 'Reformulate'
    
    @staticmethod
    def generate_recommendation(allergy_risk, side_effects, metabolic, genetic, compatibility_score, risk_classification):
        """Generate AI decision and recommendation message"""
        
        messages = []
        high_risk_factors = []
        
        # Allergy risk factors
        if allergy_risk['risk_level'] in ['High', 'Critical']:
            messages.append(f"⚠️ HIGH ALLERGY RISK: Score {allergy_risk['risk_score']}%")
            high_risk_factors.append({
                'factor': 'Allergy Risk',
                'severity': allergy_risk['risk_level'],
                'value': allergy_risk['risk_score']
            })
            
            if allergy_risk.get('problematic_ingredients'):
                for pi in allergy_risk['problematic_ingredients']:
                    messages.append(f"  • {pi['ingredient']}: {pi['reason']}")
        
        # Side effects
        if side_effects['probability'] > 40:
            messages.append(f"⚠️ ELEVATED SIDE EFFECT RISK: {side_effects['probability']}% probability ({side_effects['severity']})")
            high_risk_factors.append({
                'factor': 'Side Effects',
                'severity': side_effects['severity'],
                'value': side_effects['probability']
            })
        
        # Metabolic response
        if metabolic['response'] != 'Normal':
            messages.append(f"⚠️ METABOLIC CONCERN: {metabolic['details']}")
            high_risk_factors.append({
                'factor': 'Metabolic Response',
                'severity': metabolic['response'],
                'value': metabolic['metabolic_score']
            })
        
        # Genetic compatibility
        if genetic['compatibility'] != 'Compatible':
            messages.append(f"⚠️ GENETIC COMPATIBILITY: {genetic['compatibility']} (Score: {genetic['score']})")
            high_risk_factors.append({
                'factor': 'Genetic Compatibility',
                'severity': genetic['compatibility'],
                'value': genetic['score']
            })
        
        # Final recommendation
        if risk_classification == 'Safe':
            recommendation = "✅ VACCINE RECOMMENDED\n\nThe patient shows good compatibility with this vaccine. Standard post-vaccination monitoring is advised."
        elif risk_classification == 'Monitor':
            recommendation = "⚠️ VACCINE WITH MONITORING\n\nThe patient shows partial compatibility. Administer with caution and monitor for 30-60 minutes post-vaccination. Consider pre-medication with antihistamine."
        else:
            recommendation = "❌ VACCINE NOT RECOMMENDED\n\nThe patient shows significant risk factors. Consider alternative vaccines or consult with a specialist before administration."
        
        # Add specific reasons
        if high_risk_factors:
            recommendation += "\n\nKey Risk Factors:\n"
            for hr in high_risk_factors:
                recommendation += f"• {hr['factor']}: {hr['severity']} ({hr['value']})\n"
        
        return {
            'recommendation': recommendation,
            'high_risk_factors': high_risk_factors,
            'summary': messages
        }
    
    @staticmethod
    def generate_chart_data(allergy_risk, side_effects, metabolic, genetic, patient_data, vaccine_data):
        """Generate data for visualization charts"""
        
        # Radar chart data (risk factors)
        risk_factors = {
            'labels': ['Allergy Risk', 'Side Effect Risk', 'Metabolic Risk', 'Genetic Risk', 'Overall Risk'],
            'values': [
                allergy_risk['risk_score'],
                side_effects['probability'],
                100 - metabolic['metabolic_score'],
                100 - genetic['score'],
                100 - (allergy_risk['risk_score'] + side_effects['probability']) / 2
            ]
        }
        
        # Bar chart data (ingredient analysis)
        ingredients = []
        try:
            ingredients = json.loads(vaccine_data.get('ingredients', '[]'))
        except:
            ingredients = []
        
        ingredient_analysis = {
            'labels': ingredients[:8],  # Limit to 8 for readability
            'values': []
        }
        
        for ing in ingredients[:8]:
            risk_val = 10  # Base risk
            for risk_ing, risk_data in PredictionEngine.INGREDIENT_RISK.items():
                if risk_ingredient.lower() in ing.lower():
                    risk_val = risk_data['risk'] * 100
            ingredient_analysis['values'].append(risk_val)
        
        # Pie chart data (risk breakdown)
        risk_breakdown = {
            'labels': ['Safe Factors', 'Moderate Risk', 'High Risk', 'Critical Risk'],
            'values': [
                100 - allergy_risk['risk_score'],
                20,
                15 if allergy_risk['risk_level'] in ['High', 'Critical'] else 5,
                0 if allergy_risk['risk_level'] != 'Critical' else 10
            ]
        }
        
        return {
            'radar': risk_factors,
            'bar': ingredient_analysis,
            'pie': risk_breakdown
        }
    
    @classmethod
    def predict(cls, patient_data, vaccine_data):
        """Run complete prediction analysis"""
        
        # Run all analyses
        allergy_risk = cls.predict_allergy_risk(patient_data, vaccine_data)
        side_effects = cls.predict_side_effects(patient_data, vaccine_data)
        metabolic = cls.analyze_metabolic_response(patient_data, vaccine_data)
        genetic = cls.analyze_genetic_compatibility(patient_data, vaccine_data)
        
        # Calculate compatibility score
        compatibility_score = cls.calculate_compatibility_score(
            allergy_risk, side_effects, metabolic, genetic
        )
        
        # Determine risk classification
        risk_classification = cls.determine_risk_classification(compatibility_score)
        
        # Generate recommendation
        recommendation = cls.generate_recommendation(
            allergy_risk, side_effects, metabolic, genetic,
            compatibility_score, risk_classification
        )
        
        # Generate chart data
        chart_data = cls.generate_chart_data(
            allergy_risk, side_effects, metabolic, genetic,
            patient_data, vaccine_data
        )
        
        return {
            'allergy_risk': allergy_risk,
            'side_effects': side_effects,
            'metabolic': metabolic,
            'genetic': genetic,
            'compatibility_score': compatibility_score,
            'risk_classification': risk_classification,
            'recommendation': recommendation,
            'chart_data': chart_data
        }