"""
Package de détection de fraude pour les offres d'emploi.
"""

from .fraud_detector import predict_job_fraud, fraud_detector

__all__ = ['predict_job_fraud', 'fraud_detector']
