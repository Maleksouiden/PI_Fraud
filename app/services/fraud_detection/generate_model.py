"""
Script pour générer un modèle de base pour la détection de fraude.
Ce script est utilisé pour créer un modèle de base si le modèle entraîné n'est pas disponible.
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier

def generate_basic_model():
    """
    Génère un modèle de base pour la détection de fraude.
    """
    # Créer un ensemble de données fictif plus varié pour l'entraînement
    data = {
        'title': [
            'Développeur Python',
            'Data Scientist',
            'Ingénieur DevOps',
            'Assistant Manager',
            'Développeur Full Stack',
            'Ingénieur Logiciel',
            'Administrateur Système',
            'Responsable Marketing Digital',
            'Travail à domicile - Gains rapides',
            'Opportunité exceptionnelle - Revenus illimités'
        ],
        'location': [
            'Paris, France',
            'Lyon, France',
            'Marseille, France',
            'Toulouse, France',
            'Bordeaux, France',
            'Lille, France',
            'Nantes, France',
            'Strasbourg, France',
            'Travail à distance',
            'Partout en France'
        ],
        'department': [
            'IT',
            'Data',
            'IT',
            'Management',
            'Développement',
            'Ingénierie',
            'Infrastructure',
            'Marketing',
            'Non spécifié',
            'Tous départements'
        ],
        'company_profile': [
            'Entreprise de logiciels',
            'Startup data',
            'Grande entreprise',
            'Petite entreprise',
            'Agence web',
            'Éditeur de logiciels',
            'ESN',
            'Agence marketing',
            '',
            'Entreprise internationale'
        ],
        'description': [
            'Nous recherchons un développeur Python expérimenté pour rejoindre notre équipe.',
            'Poste de data scientist pour analyser des données et créer des modèles.',
            'Ingénieur DevOps pour gérer notre infrastructure cloud.',
            'Assistant manager pour aider à la gestion quotidienne.',
            'Développeur Full Stack pour travailler sur nos applications web et mobiles.',
            'Ingénieur logiciel pour concevoir et développer nos produits.',
            'Administrateur système pour gérer notre infrastructure IT.',
            'Responsable marketing digital pour développer notre présence en ligne.',
            'Travaillez depuis chez vous et gagnez jusqu\'à 5000€ par semaine sans expérience requise!',
            'Opportunité unique! Revenus illimités, formation offerte, contactez-nous rapidement!'
        ],
        'requirements': [
            'Python, Django, Flask',
            'Python, R, Machine Learning',
            'Docker, Kubernetes, AWS',
            'Excel, Word, Communication',
            'JavaScript, React, Node.js',
            'Java, Spring, Hibernate',
            'Linux, Windows Server, Networking',
            'SEO, SEM, Google Analytics',
            'Aucune expérience requise',
            'Motivation et détermination'
        ],
        'benefits': [
            'Tickets restaurant, Mutuelle',
            'Télétravail, Formation',
            'RTT, Participation',
            'Horaires flexibles',
            'Prime annuelle, CE',
            'Intéressement, PEE',
            'Assurance santé, Retraite',
            'Formation continue, Évènements',
            'Revenus exceptionnels',
            'Liberté financière'
        ],
        'employment_type': [
            'CDI',
            'CDI',
            'CDD',
            'CDI',
            'CDI',
            'CDI',
            'CDI',
            'CDI',
            'Indépendant',
            'Freelance'
        ],
        'required_experience': [
            '3-5 ans',
            '2-3 ans',
            '5-7 ans',
            '1-2 ans',
            '3-5 ans',
            '5+ ans',
            '3-5 ans',
            '2-4 ans',
            'Aucune',
            'Tous niveaux'
        ],
        'required_education': [
            "Bac+5",
            "Bac+5",
            "Bac+3",
            "Bac+2",
            "Bac+5",
            "Bac+5",
            "Bac+3",
            "Bac+3",
            "Aucun diplôme requis",
            "Peu importe"
        ],
        'fraudulent': [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,  # Offre frauduleuse
            1   # Offre frauduleuse
        ]
    }

    df = pd.DataFrame(data)

    # Créer la colonne combined_text
    df['combined_text'] = df['title'] + ' ' + df['location'] + ' ' + df['department'] + ' ' + \
                         df['company_profile'] + ' ' + df['description'] + ' ' + \
                         df['requirements'] + ' ' + df['benefits']

    # Créer les colonnes de longueur
    df['description_length'] = df['description'].apply(len)
    df['requirements_length'] = df['requirements'].apply(len)
    df['company_profile_length'] = df['company_profile'].apply(len)
    df['benefits_length'] = df['benefits'].apply(len)

    # Extraire state, city et Country à partir de location
    try:
        # Utiliser une approche plus robuste
        df['city'] = df['location'].apply(lambda x: x.split(',')[0].strip() if ',' in x else x.strip())
        df['state'] = df['location'].apply(lambda x: x.split(',')[1].strip() if ',' in x and len(x.split(',')) > 1 else 'Unknown')
        df['Country'] = df['location'].apply(lambda x: x.split(',')[2].strip() if ',' in x and len(x.split(',')) > 2 else 'Unknown')
    except Exception as e:
        print(f"Avertissement: Impossible d'extraire les informations de localisation: {str(e)}")
        df['city'] = 'Unknown'
        df['state'] = 'Unknown'
        df['Country'] = 'Unknown'

    # Séparer features et target
    y = df['fraudulent']
    X = df.drop(columns=['fraudulent'])

    # Définir les types de colonnes
    text_feature = 'combined_text'
    cat_features = ['employment_type', 'required_experience', 'required_education',
                    'city', 'state', 'Country']
    num_features = ['description_length', 'requirements_length',
                    'company_profile_length', 'benefits_length']

    # Préprocesseur
    preprocessor = ColumnTransformer(transformers=[
        # TF-IDF sur le texte
        ('tfidf', TfidfVectorizer(max_features=1000), text_feature),
        # OneHot sur catégorielles
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features),
        # Standardisation sur numériques
        ('scaler', StandardScaler(), num_features)
    ], remainder='drop')

    # Pipeline avec RandomForest
    pipeline = Pipeline([
        ('preproc', preprocessor),
        ('clf', RandomForestClassifier(
            n_estimators=10,
            max_depth=3,
            random_state=42
        ))
    ])

    # Entraînement sur les données fictives
    pipeline.fit(X, y)

    # Sauvegarder le modèle
    model_path = os.path.join(os.path.dirname(__file__), 'rf_pipeline.pkl')
    joblib.dump(pipeline, model_path)
    print(f"Modèle de base sauvegardé dans {model_path}")

    return pipeline

if __name__ == "__main__":
    generate_basic_model()
