"""
Script pour initialiser la base de données avec les nouvelles colonnes.
"""

import os
import sys
from app import create_app, db
from app.models.job import Job
from app.models.profile import Profile, Skill
from app.models.user import User
from app.models.search_history import SearchHistory

def init_db():
    """
    Initialise la base de données avec les nouvelles colonnes.
    """
    app = create_app()
    with app.app_context():
        # Créer les tables
        db.create_all()

        print("Base de données initialisée avec succès!")

        # Vérifier si les tables ont été créées
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables créées: {tables}")

        # Vérifier les colonnes de la table job
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        columns = inspector.get_columns('job')
        column_names = [column['name'] for column in columns]
        print(f"Colonnes de la table job: {column_names}")

        # Ajouter les colonnes de détection de fraude si elles n'existent pas
        if 'fraud_probability' not in column_names:
            print("Ajout de la colonne 'fraud_probability'...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE job ADD COLUMN fraud_probability FLOAT DEFAULT 0.0"))
                conn.commit()

        if 'fraud_indicators' not in column_names:
            print("Ajout de la colonne 'fraud_indicators'...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE job ADD COLUMN fraud_indicators TEXT"))
                conn.commit()

        # Vérifier à nouveau les colonnes
        inspector = inspect(db.engine)
        columns = inspector.get_columns('job')
        column_names = [column['name'] for column in columns]
        print(f"Colonnes de la table job après mise à jour: {column_names}")

        return True

if __name__ == "__main__":
    init_db()
