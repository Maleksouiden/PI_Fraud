# JobMatch - Plateforme de recherche d'emploi avec détection de fraude

JobMatch est une plateforme de recherche d'emploi innovante qui combine un système de matching intelligent avec un détecteur de fraude avancé pour protéger les utilisateurs contre les offres d'emploi frauduleuses.

![JobMatch Logo](app/static/img/logo.png)

## Fonctionnalités principales

### 1. Recherche et filtrage d'offres d'emploi
- Recherche par mots-clés et localisation
- Filtrage par type de contrat, salaire, compétences, niveau d'éducation, etc.
- Scraping en temps réel depuis LinkedIn, Indeed, Monster et Pôle Emploi

### 2. Système de matching intelligent
- Calcul de compatibilité entre profils utilisateurs et offres d'emploi
- Prise en compte des compétences, de la localisation, du type de travail, du salaire, etc.
- Recommandations personnalisées basées sur le profil de l'utilisateur

### 3. Détection de fraude
- Analyse des offres d'emploi pour détecter les signes de fraude
- Modèle de machine learning (RandomForest) pour la classification
- Indicateurs de fraude détaillés avec explications
- Niveaux de risque (Très faible à Très élevé)

### 4. Gestion de profil utilisateur
- Création et modification de profil
- Ajout de compétences, d'expériences et de préférences
- Téléchargement de CV et de photo de profil

### 5. Historique de recherche
- Suivi des recherches effectuées
- Historique des offres consultées

## Technologies utilisées

- **Backend**: Flask (Python)
- **Base de données**: SQLite avec SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Machine Learning**: scikit-learn (RandomForest, TF-IDF)
- **Web Scraping**: BeautifulSoup, Requests

## Architecture du projet

```
app/
├── models/             # Modèles de données
├── routes/             # Gestionnaires de routes
├── services/           # Services métier
│   ├── fraud_detection/  # Système de détection de fraude
│   └── job_scraper.py    # Scraping d'offres d'emploi
├── static/             # Fichiers statiques (CSS, JS, images)
├── templates/          # Templates HTML
└── __init__.py         # Initialisation de l'application

instance/              # Données spécifiques à l'instance (base de données)
run.py                 # Point d'entrée de l'application
```

## Système de détection de fraude

Le système de détection de fraude utilise une approche hybride :

1. **Modèle de machine learning** : Un classifieur RandomForest entraîné sur des données d'offres d'emploi légitimes et frauduleuses.

2. **Analyse basée sur des règles** : Détection de signaux d'alerte comme :
   - Absence d'informations sur l'entreprise
   - Salaires anormalement élevés
   - Qualité linguistique médiocre
   - Demandes d'informations personnelles
   - Descriptions de poste vagues
   - Absence d'exigences
   - Informations de contact suspectes
   - Tactiques d'urgence ou de pression

Chaque offre reçoit un score de probabilité de fraude et est classée selon son niveau de risque.

## Système de matching

Le système de matching calcule un score de compatibilité entre un profil utilisateur et une offre d'emploi en fonction de plusieurs critères :

- Correspondance des compétences (35% du score)
- Correspondance de localisation (15% du score)
- Correspondance du type de travail (15% du score)
- Correspondance de salaire (10% du score)
- Correspondance du niveau d'éducation (10% du score)
- Score de base et bonus (15% du score)

## Installation et démarrage

### Prérequis
- Python 3.8+
- pip

### Installation

1. Cloner le dépôt
```bash
git clone https://github.com/Maleksouiden/PI_Fraud.git
cd PI_Fraud
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Initialiser la base de données
```bash
python init_db.py
```

4. Lancer l'application
```bash
python run.py
```

5. Accéder à l'application dans votre navigateur
```
http://localhost:5000
```

## Captures d'écran

### Page d'accueil
![Page d'accueil](screenshots/home.png)

### Liste des offres d'emploi
![Liste des offres](screenshots/job_list.png)

### Détail d'une offre avec détection de fraude
![Détail d'une offre](screenshots/job_detail.png)

### Profil utilisateur
![Profil utilisateur](screenshots/profile.png)

## Contributeurs

- Malek Souiden

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
