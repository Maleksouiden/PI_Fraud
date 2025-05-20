"""
Script pour mettre à jour la base de données avec les champs de détection de fraude.
"""

import os
import sys
import sqlite3

def update_database():
    """
    Met à jour la base de données pour ajouter les colonnes de détection de fraude.
    """
    # Chemin vers la base de données
    # Essayer plusieurs chemins possibles
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'instance', 'jobmatch.db'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), 'instance', 'jobmatch.db'),
        'instance/jobmatch.db',
        '../instance/jobmatch.db',
        '../../instance/jobmatch.db',
        '../../../instance/jobmatch.db'
    ]

    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        print("Base de données non trouvée. Voici les chemins essayés:")
        for path in possible_paths:
            print(f"- {path}")
        return False

    print(f"Base de données trouvée à {db_path}")

    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Vérifier si la table job existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job'")
        if not cursor.fetchone():
            print("La table 'job' n'existe pas dans la base de données.")
            conn.close()
            return False

        # Vérifier si les colonnes existent déjà
        cursor.execute("PRAGMA table_info(job)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Ajouter les colonnes si elles n'existent pas
        if 'fraud_probability' not in column_names:
            print("Ajout de la colonne 'fraud_probability'...")
            cursor.execute("ALTER TABLE job ADD COLUMN fraud_probability FLOAT DEFAULT 0.0")

        if 'fraud_indicators' not in column_names:
            print("Ajout de la colonne 'fraud_indicators'...")
            cursor.execute("ALTER TABLE job ADD COLUMN fraud_indicators TEXT")

        # Valider les modifications
        conn.commit()
        conn.close()

        print("Base de données mise à jour avec succès!")
        return True

    except Exception as e:
        print(f"Erreur lors de la mise à jour de la base de données: {str(e)}")
        return False

if __name__ == "__main__":
    update_database()
