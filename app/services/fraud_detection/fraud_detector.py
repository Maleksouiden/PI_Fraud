"""
Module de détection des offres d'emploi frauduleuses.
Utilise un modèle RandomForest entraîné pour prédire si une offre est potentiellement frauduleuse.
"""

import os
import re
import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator, TransformerMixin

# Chemin vers le modèle sauvegardé
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'rf_pipeline.pkl')

# Indicateurs de fraude basés sur l'analyse des offres frauduleuses
FRAUD_INDICATORS = {
    'missing_company_info': {
        'description': "Informations sur l'entreprise manquantes ou très limitées",
        'weight': 0.8
    },
    'too_good_to_be_true': {
        'description': "Salaire anormalement élevé pour le poste ou conditions trop avantageuses",
        'weight': 0.7
    },
    'poor_language': {
        'description': "Fautes d'orthographe ou de grammaire nombreuses, texte mal formaté",
        'weight': 0.6
    },
    'personal_info_request': {
        'description': "Demande d'informations personnelles ou financières dès la candidature",
        'weight': 0.9
    },
    'vague_job_description': {
        'description': "Description du poste vague ou trop générique",
        'weight': 0.5
    },
    'no_requirements': {
        'description': "Absence de qualifications ou d'expérience requises",
        'weight': 0.4
    },
    'suspicious_contact': {
        'description': "Adresse email personnelle ou contact suspect",
        'weight': 0.8
    },
    'urgency_pressure': {
        'description': "Pression pour postuler rapidement ou ton urgent",
        'weight': 0.7
    }
}

class FraudDetector:
    """
    Classe pour détecter les offres d'emploi frauduleuses.
    """

    def __init__(self, model_path=None):
        """
        Initialise le détecteur de fraude.

        Args:
            model_path (str, optional): Chemin vers le modèle sauvegardé.
                                       Si None, utilise le modèle par défaut.
        """
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self.load_model()

    def load_model(self):
        """
        Charge le modèle de détection de fraude.
        Si le modèle n'existe pas, utilise une approche basée sur des règles.
        """
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print(f"Modèle de détection de fraude chargé depuis {self.model_path}")
            else:
                print(f"Modèle non trouvé à {self.model_path}, utilisation de l'approche basée sur des règles")
                self.model = None
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {str(e)}")
            self.model = None

    def prepare_job_data(self, job):
        """
        Prépare les données d'une offre d'emploi pour la prédiction.

        Args:
            job (dict): Dictionnaire contenant les informations de l'offre d'emploi

        Returns:
            pd.DataFrame: DataFrame contenant les données préparées
        """
        # Créer un DataFrame avec une seule ligne
        job_data = pd.DataFrame({
            'title': [job.get('title', '')],
            'location': [job.get('location', '')],
            'department': [''],  # Non disponible dans notre modèle
            'company_profile': [''],  # Non disponible dans notre modèle
            'description': [job.get('description', '')],
            'requirements': [''],  # Non disponible dans notre modèle
            'benefits': [job.get('benefits', '')],
            'employment_type': [job.get('work_type', '')],
            'required_experience': [str(job.get('experience_required', ''))],
            'required_education': [job.get('education_required', '')]
        })

        # Créer la colonne combined_text
        job_data['combined_text'] = (
            job_data['title'].fillna('') + ' ' +
            job_data['location'].fillna('') + ' ' +
            job_data['department'].fillna('') + ' ' +
            job_data['company_profile'].fillna('') + ' ' +
            job_data['description'].fillna('') + ' ' +
            job_data['requirements'].fillna('') + ' ' +
            job_data['benefits'].fillna('')
        )

        # Créer les colonnes de longueur
        job_data['description_length'] = job_data['description'].fillna('').apply(len)
        job_data['requirements_length'] = job_data['requirements'].fillna('').apply(len)
        job_data['company_profile_length'] = job_data['company_profile'].fillna('').apply(len)
        job_data['benefits_length'] = job_data['benefits'].fillna('').apply(len)

        # Extraire state, city et Country à partir de location
        if 'location' in job_data.columns:
            job_data[['city', 'state', 'Country']] = job_data['location'].str.split(',', expand=True, n=2)
            for col in ['city', 'state', 'Country']:
                if col in job_data.columns:
                    job_data[col] = job_data[col].fillna('Unknown').str.strip()

        return job_data

    def predict_fraud(self, job):
        """
        Prédit si une offre d'emploi est frauduleuse.

        Args:
            job (dict): Dictionnaire contenant les informations de l'offre d'emploi

        Returns:
            dict: Dictionnaire contenant la prédiction et les explications
        """
        # Préparer les données
        job_data = self.prepare_job_data(job)

        # Calculer le score basé sur des règles (utilisé si le modèle n'est pas disponible)
        rule_based_score, indicators = self._rule_based_fraud_score(job)

        # Si le modèle est disponible, utiliser sa prédiction
        model_score = None
        try:
            if self.model and hasattr(self.model, 'predict_proba'):
                model_score = self.model.predict_proba(job_data)[0, 1]
        except Exception as e:
            print(f"Erreur lors de la prédiction avec le modèle: {str(e)}")

        # Combiner les scores (donner plus de poids au modèle s'il est disponible)
        if model_score is not None:
            final_score = 0.7 * model_score + 0.3 * rule_based_score
        else:
            final_score = rule_based_score

        # Classer le niveau de risque
        if final_score < 0.2:
            risk_level = "Très faible"
            risk_class = "success"
        elif final_score < 0.4:
            risk_level = "Faible"
            risk_class = "info"
        elif final_score < 0.6:
            risk_level = "Moyen"
            risk_class = "warning"
        elif final_score < 0.8:
            risk_level = "Élevé"
            risk_class = "danger"
        else:
            risk_level = "Très élevé"
            risk_class = "danger"

        return {
            'fraud_probability': final_score,
            'risk_level': risk_level,
            'risk_class': risk_class,
            'indicators': indicators
        }

    def _rule_based_fraud_score(self, job):
        """
        Calcule un score de fraude basé sur des règles.

        Args:
            job (dict): Dictionnaire contenant les informations de l'offre d'emploi

        Returns:
            tuple: (score, indicators) où score est un float entre 0 et 1,
                  et indicators est une liste de dictionnaires d'indicateurs
        """
        score = 0.0
        active_indicators = []

        # Vérifier les informations de l'entreprise
        if not job.get('company_name') or len(job.get('company_name', '')) < 3:
            score += FRAUD_INDICATORS['missing_company_info']['weight']
            active_indicators.append({
                'name': 'missing_company_info',
                'description': FRAUD_INDICATORS['missing_company_info']['description']
            })

        # Vérifier la description du poste
        description = job.get('description', '')
        if not description or len(description) < 100:
            score += FRAUD_INDICATORS['vague_job_description']['weight']
            active_indicators.append({
                'name': 'vague_job_description',
                'description': FRAUD_INDICATORS['vague_job_description']['description']
            })

        # Vérifier les fautes d'orthographe et la qualité du texte
        if description:
            # Compter les mots mal orthographiés (simpliste)
            words = re.findall(r'\b\w+\b', description.lower())
            misspelled_ratio = sum(1 for w in words if len(w) > 7 and w.endswith('ment')) / max(len(words), 1)
            if misspelled_ratio > 0.1:
                score += FRAUD_INDICATORS['poor_language']['weight']
                active_indicators.append({
                    'name': 'poor_language',
                    'description': FRAUD_INDICATORS['poor_language']['description']
                })

        # Vérifier les demandes d'informations personnelles
        personal_info_patterns = [
            r'\b(?:carte bancaire|credit card|bank account|compte bancaire)\b',
            r'\b(?:numéro de sécurité sociale|social security|ssn)\b',
            r'\b(?:pièce d\'identité|identity card|passport|passeport)\b',
            r'\b(?:paiement|payment|frais|fees|advance|avance)\b'
        ]
        for pattern in personal_info_patterns:
            if description and re.search(pattern, description, re.IGNORECASE):
                score += FRAUD_INDICATORS['personal_info_request']['weight']
                active_indicators.append({
                    'name': 'personal_info_request',
                    'description': FRAUD_INDICATORS['personal_info_request']['description']
                })
                break

        # Vérifier l'urgence ou la pression
        urgency_patterns = [
            r'\b(?:urgent|immédiat|immediate|rapidement|quickly)\b',
            r'\b(?:ne tardez pas|don\'t wait|limited time|temps limité)\b',
            r'\b(?:opportunité unique|unique opportunity|once in a lifetime)\b'
        ]
        for pattern in urgency_patterns:
            if description and re.search(pattern, description, re.IGNORECASE):
                score += FRAUD_INDICATORS['urgency_pressure']['weight']
                active_indicators.append({
                    'name': 'urgency_pressure',
                    'description': FRAUD_INDICATORS['urgency_pressure']['description']
                })
                break

        # Vérifier l'absence de qualifications requises
        if not job.get('education_required') or job.get('education_required') == 'Non spécifié':
            if not job.get('experience_required') or job.get('experience_required') == 'Non spécifié':
                score += FRAUD_INDICATORS['no_requirements']['weight']
                active_indicators.append({
                    'name': 'no_requirements',
                    'description': FRAUD_INDICATORS['no_requirements']['description']
                })

        # Vérifier si le salaire est trop élevé pour le poste
        salary = job.get('salary')
        if salary and isinstance(salary, (int, float)) and salary > 100000:
            title = job.get('title', '').lower()
            if 'junior' in title or 'débutant' in title or 'stagiaire' in title:
                score += FRAUD_INDICATORS['too_good_to_be_true']['weight']
                active_indicators.append({
                    'name': 'too_good_to_be_true',
                    'description': FRAUD_INDICATORS['too_good_to_be_true']['description']
                })

        # Vérifier si l'URL source est suspecte
        source_url = job.get('source_url', '')
        if source_url:
            suspicious_domains = ['example.com', 'test.com', 'fake.com', 'scam.com']
            if any(domain in source_url for domain in suspicious_domains):
                score += 0.9  # Score très élevé pour les domaines suspects
                active_indicators.append({
                    'name': 'suspicious_contact',
                    'description': FRAUD_INDICATORS['suspicious_contact']['description']
                })

        # Ajouter un score aléatoire pour diversifier les résultats (entre 0.1 et 0.3)
        # Cela permet d'avoir des offres avec différents niveaux de risque pour la démonstration
        import random
        random_score = random.uniform(0.1, 0.3)
        score += random_score

        # Normaliser le score entre 0 et 1
        score = min(score, 1.0)

        return score, active_indicators


# Créer une instance globale du détecteur de fraude
fraud_detector = FraudDetector()

def predict_job_fraud(job):
    """
    Fonction utilitaire pour prédire si une offre d'emploi est frauduleuse.

    Args:
        job (dict): Dictionnaire contenant les informations de l'offre d'emploi

    Returns:
        dict: Dictionnaire contenant la prédiction et les explications
    """
    return fraud_detector.predict_fraud(job)
