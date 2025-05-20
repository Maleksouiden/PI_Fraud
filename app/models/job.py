from datetime import datetime
import json
from app import db

# Table d'association pour les compétences requises
job_skills = db.Table('job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skill.id'), primary_key=True)
)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Informations de base
    title = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    company_logo = db.Column(db.String(255))
    description = db.Column(db.Text, nullable=False)

    # Détails du poste
    location = db.Column(db.String(100))
    salary = db.Column(db.Integer)
    work_type = db.Column(db.String(20))  # Présentiel, télétravail, mixte

    # Exigences
    education_required = db.Column(db.String(50))
    experience_required = db.Column(db.Integer)

    # Avantages
    benefits = db.Column(db.Text)

    # Métadonnées
    application_link = db.Column(db.String(255))
    source_url = db.Column(db.String(255))
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    scraped_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Détection de fraude
    # Utiliser nullable=True pour que les colonnes soient optionnelles
    fraud_probability = db.Column(db.Float, default=0.0, nullable=True)
    fraud_indicators = db.Column(db.Text, nullable=True)  # Stocké en JSON

    # Relations
    skills = db.relationship('Skill', secondary=job_skills, lazy='subquery',
                           backref=db.backref('jobs', lazy=True))

    def __repr__(self):
        return f"Job('{self.title}', '{self.company_name}')"

    def get_fraud_indicators(self):
        """
        Récupère les indicateurs de fraude sous forme de liste de dictionnaires.

        Returns:
            list: Liste des indicateurs de fraude
        """
        # Vérifier si l'attribut existe (pour la compatibilité avec les anciennes bases de données)
        if not hasattr(self, 'fraud_indicators') or not self.fraud_indicators:
            return []

        try:
            return json.loads(self.fraud_indicators)
        except:
            return []

    def set_fraud_indicators(self, indicators):
        """
        Définit les indicateurs de fraude à partir d'une liste de dictionnaires.

        Args:
            indicators (list): Liste des indicateurs de fraude
        """
        # Vérifier si l'attribut existe (pour la compatibilité avec les anciennes bases de données)
        if not hasattr(self, 'fraud_indicators'):
            return

        if indicators is None:
            self.fraud_indicators = None
        else:
            self.fraud_indicators = json.dumps(indicators)

    def get_fraud_risk_level(self):
        """
        Détermine le niveau de risque de fraude en fonction de la probabilité.

        Returns:
            tuple: (niveau de risque, classe CSS)
        """
        # Vérifier si l'attribut existe (pour la compatibilité avec les anciennes bases de données)
        if not hasattr(self, 'fraud_probability') or self.fraud_probability is None:
            return "Inconnu", "secondary"

        if self.fraud_probability < 0.2:
            return "Très faible", "success"
        elif self.fraud_probability < 0.4:
            return "Faible", "info"
        elif self.fraud_probability < 0.6:
            return "Moyen", "warning"
        elif self.fraud_probability < 0.8:
            return "Élevé", "danger"
        else:
            return "Très élevé", "danger"
