from datetime import datetime
from app import db

# Table d'association pour les offres consultées
history_jobs = db.Table('history_jobs',
    db.Column('history_id', db.Integer, db.ForeignKey('search_history.id'), primary_key=True),
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True)
)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Critères de recherche
    search_query = db.Column(db.String(200))
    location_filter = db.Column(db.String(100))
    work_type_filter = db.Column(db.String(20))
    salary_min_filter = db.Column(db.Integer)
    
    # Métadonnées
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    viewed_jobs = db.relationship('Job', secondary=history_jobs, lazy='subquery',
                                backref=db.backref('viewed_in_searches', lazy=True))
    
    def __repr__(self):
        return f"SearchHistory('{self.search_query}', '{self.search_date}')"
