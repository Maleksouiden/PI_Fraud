import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import re
import random
import time
import urllib.parse
from app import db
from app.models.job import Job
from app.models.profile import Skill
from app.services.fraud_detection import predict_job_fraud

def clean_company_name(company_name):
    """
    Nettoie le nom d'une entreprise en supprimant les caractères spéciaux et les mots inutiles.

    Args:
        company_name (str): Nom de l'entreprise à nettoyer

    Returns:
        str: Nom de l'entreprise nettoyé
    """
    if not company_name:
        return "Entreprise non spécifiée"

    # Supprimer les caractères spéciaux et les mots inutiles
    company_name = company_name.replace("·", "").replace("•", "").strip()
    company_name = re.sub(r'\s+', ' ', company_name)  # Remplacer les espaces multiples par un seul espace

    # Supprimer les suffixes courants
    suffixes = [
        r'\bSAS\b', r'\bSARL\b', r'\bSA\b', r'\bEURL\b', r'\bSNC\b', r'\bSCS\b', r'\bSCA\b',
        r'\bInc\b', r'\bLLC\b', r'\bLtd\b', r'\bLimited\b', r'\bCorp\b', r'\bCorporation\b',
        r'\bGmbH\b', r'\bAG\b', r'\bBV\b', r'\bPLC\b', r'\bSpA\b', r'\bOy\b', r'\bAB\b',
        r'\bGroup\b', r'\bGroupe\b', r'\bHolding\b', r'\bConsulting\b', r'\bConsultants\b'
    ]

    for suffix in suffixes:
        company_name = re.sub(suffix, '', company_name, flags=re.IGNORECASE)

    # Supprimer les caractères spéciaux à la fin
    company_name = re.sub(r'[,\.;:\-_]+$', '', company_name)

    # Supprimer les espaces en début et fin
    company_name = company_name.strip()

    # Si le nom est vide après nettoyage, retourner une valeur par défaut
    if not company_name:
        return "Entreprise non spécifiée"

    return company_name

def extract_salary_from_text(text):
    """
    Extrait le salaire à partir d'un texte.

    Args:
        text (str): Texte contenant potentiellement un salaire

    Returns:
        int or None: Salaire extrait ou None si aucun salaire n'est trouvé
    """
    # Recherche des motifs comme "50 000 €", "50k€", "50 000 euros"
    patterns = [
        r'(\d{1,3}(?:\s?\d{3})*)\s*[€kK]',  # 50 000 €, 50K
        r'(\d{1,3}(?:\s?\d{3})*)\s*euros',  # 50 000 euros
        r'(\d{1,2})[.,](\d{1,3})\s*[kK]',   # 50.5k, 50,5k
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 1:
                # Format "50 000 €"
                salary_str = match.group(1).replace(' ', '')
                try:
                    return int(salary_str)
                except ValueError:
                    pass
            elif len(match.groups()) == 2:
                # Format "50.5k"
                try:
                    return int(float(match.group(1) + '.' + match.group(2)) * 1000)
                except ValueError:
                    pass

    return None

def extract_work_type(description):
    """
    Détermine le type de travail à partir de la description.

    Args:
        description (str): Description du poste

    Returns:
        str: Type de travail (Présentiel, Télétravail, Mixte)
    """
    description = description.lower()

    if 'télétravail' in description or 'remote' in description or 'à distance' in description:
        if 'hybride' in description or 'mixte' in description or 'partiel' in description:
            return 'Mixte'
        return 'Télétravail'
    elif 'sur site' in description or 'présentiel' in description or 'sur place' in description:
        return 'Présentiel'
    else:
        return 'Non spécifié'

def extract_education_level(description):
    """
    Extrait le niveau d'études requis à partir de la description.

    Args:
        description (str): Description du poste

    Returns:
        str: Niveau d'études requis
    """
    description = description.lower()

    if 'bac+8' in description or 'doctorat' in description or 'phd' in description:
        return 'Bac+8'
    elif 'bac+5' in description or 'master' in description or 'ingénieur' in description:
        return 'Bac+5'
    elif 'bac+3' in description or 'licence' in description or 'bachelor' in description:
        return 'Bac+3'
    elif 'bac+2' in description or 'dut' in description or 'bts' in description:
        return 'Bac+2'
    elif 'bac' in description:
        return 'Bac'
    else:
        return 'Non spécifié'

def extract_experience_required(description):
    """
    Extrait le nombre d'années d'expérience requis à partir de la description.

    Args:
        description (str): Description du poste

    Returns:
        int or None: Nombre d'années d'expérience requis
    """
    # Recherche des motifs comme "5 ans d'expérience", "expérience de 5 ans"
    patterns = [
        r'(\d+)\s*(?:an(?:s|née)?(?:s)?)\s*d[\'"]expérience',
        r'expérience\s*(?:de|d[\'"])?\s*(\d+)\s*an(?:s|née)?(?:s)?',
        r'(\d+)\s*(?:an(?:s|née)?(?:s)?)\s*d[\'""]ancienneté',
    ]

    for pattern in patterns:
        match = re.search(pattern, description.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

    return None

def extract_skills_from_description(description):
    """
    Extrait les compétences potentielles à partir de la description.

    Args:
        description (str): Description du poste

    Returns:
        list: Liste des compétences extraites
    """
    # Liste de compétences techniques courantes
    common_skills = [
        # Langages de programmation
        'Python', 'Java', 'JavaScript', 'C++', 'C#', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Go', 'Rust',
        # Frameworks et bibliothèques
        'React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring', 'Laravel', 'Node.js', 'Express',
        'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy',
        # Bases de données
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Oracle', 'SQLite', 'Redis', 'Elasticsearch',
        # DevOps et Cloud
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Jenkins', 'Git', 'CI/CD',
        # Data Science et IA
        'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'Data Mining',
        'Big Data', 'Hadoop', 'Spark', 'Data Visualization', 'Tableau', 'Power BI',
        # Autres
        'Agile', 'Scrum', 'REST API', 'GraphQL', 'Microservices', 'UX/UI', 'Responsive Design'
    ]

    found_skills = []
    for skill in common_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', description, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills

def scrape_indeed_jobs(query='', location=''):
    """
    Scrape les offres d'emploi depuis Indeed.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche

    Returns:
        list: Liste des offres d'emploi scrapées
    """
    if not query:
        query = "développeur"

    # Construction de l'URL de recherche Indeed
    base_url = "https://fr.indeed.com/emplois"
    params = {
        'q': query,
        'l': location if location else 'France',
        'sort': 'date',  # Trier par date pour avoir les offres les plus récentes
        'fromage': '14'  # Offres des 14 derniers jours
    }

    url = f"{base_url}?{'&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://fr.indeed.com/",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Tentative de scraping d'Indeed avec l'URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche des éléments d'offre d'emploi
        job_cards = soup.select('div.job_seen_beacon')

        if not job_cards:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            job_cards = soup.select('div.jobsearch-ResultsList > div.cardOutline')

        if not job_cards:
            # Essayer un autre sélecteur si les précédents ne fonctionnent pas
            job_cards = soup.select('div[data-testid="job-card"]')

        if not job_cards:
            print("Aucun élément d'offre d'emploi trouvé sur Indeed.")
            return []

        print(f"Trouvé {len(job_cards)} offres d'emploi sur Indeed.")

        jobs = []
        for i, card in enumerate(job_cards[:20]):  # Limiter à 20 offres
            try:
                # Extraire le titre
                title_element = card.select_one('h2.jobTitle span') or card.select_one('a.jcs-JobTitle span')
                if not title_element:
                    title_element = card.select_one('h2 a') or card.select_one('h2')

                title = title_element.get_text(strip=True) if title_element else f"Poste {query} {i+1}"

                # Extraire le nom de l'entreprise
                company_element = card.select_one('span.companyName') or card.select_one('div.company_location > pre > span.companyName')
                if not company_element:
                    company_element = card.select_one('div[data-testid="company-name"]') or card.select_one('span[data-testid="company-name"]')

                company_name = company_element.get_text(strip=True) if company_element else "Entreprise non spécifiée"

                # Extraire le lieu
                location_element = card.select_one('div.companyLocation') or card.select_one('div[data-testid="text-location"]')
                location_val = location_element.get_text(strip=True) if location_element else location or "France"

                # Extraire le salaire
                salary_element = card.select_one('div.salary-snippet-container') or card.select_one('div[data-testid="attribute_snippet_testid"]')
                salary_text = salary_element.get_text(strip=True) if salary_element else ""
                salary = extract_salary_from_text(salary_text)

                # Extraire l'URL de l'offre
                link_element = card.select_one('h2.jobTitle a') or card.select_one('a.jcs-JobTitle') or card.select_one('h2 a')
                job_url = ""
                if link_element and 'href' in link_element.attrs:
                    job_url = link_element['href']
                    if job_url.startswith('/'):
                        job_url = f"https://fr.indeed.com{job_url}"
                else:
                    job_url = f"{url}&vjk={i}"

                # Extraire la description (snippet)
                description_element = card.select_one('div.job-snippet') or card.select_one('div[data-testid="job-snippet"]')
                description = description_element.get_text(strip=True) if description_element else f"Offre pour le poste de {title} chez {company_name} à {location_val}."

                # Extraire le type de travail (temps plein, partiel, etc.)
                metadata_elements = card.select('div.metadata') or card.select('div[data-testid="attribute_snippet_testid"]')
                work_type = None
                for element in metadata_elements:
                    text = element.get_text(strip=True).lower()
                    if any(type_keyword in text for type_keyword in ['temps plein', 'temps partiel', 'cdi', 'cdd', 'stage', 'freelance']):
                        work_type = element.get_text(strip=True)
                        break

                # Extraire les compétences à partir de la description
                skills = extract_skills_from_description(description)

                # Créer l'objet d'offre d'emploi
                job = {
                    'title': title,
                    'company_name': company_name,
                    'company_logo': f"https://logo.clearbit.com/{company_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
                    'description': description,
                    'location': location_val,
                    'salary': salary,
                    'work_type': work_type or 'Non spécifié',
                    'education_required': extract_education_level(description),
                    'experience_required': extract_experience_required(description),
                    'benefits': 'Non spécifié',
                    'application_link': job_url,
                    'source_url': job_url,
                    'skills': skills if skills else [query] if query else ['Non spécifié']
                }

                jobs.append(job)

                # Pause aléatoire pour éviter d'être bloqué
                time.sleep(random.uniform(0.2, 0.5))

            except Exception as e:
                print(f"Erreur lors de l'extraction de l'offre Indeed {i+1}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Erreur lors du scraping d'Indeed: {str(e)}")
        return []

def save_job_to_db(job_data):
    """
    Sauvegarde une offre d'emploi dans la base de données.

    Args:
        job_data (dict): Données de l'offre d'emploi

    Returns:
        tuple: (Job, bool) L'objet Job créé ou mis à jour et un booléen indiquant si l'offre est nouvelle
    """
    # Vérifier si l'offre existe déjà (par URL source)
    existing_job = Job.query.filter_by(source_url=job_data['source_url']).first()

    # Analyser l'offre pour détecter les fraudes
    fraud_result = predict_job_fraud(job_data)

    if existing_job:
        # Mise à jour de l'offre existante
        existing_job.title = job_data['title']
        existing_job.company_name = job_data['company_name']
        existing_job.company_logo = job_data['company_logo']
        existing_job.description = job_data['description']
        existing_job.location = job_data['location']
        existing_job.salary = job_data['salary']
        existing_job.work_type = job_data['work_type']
        existing_job.education_required = job_data['education_required']
        existing_job.experience_required = job_data['experience_required']
        existing_job.benefits = job_data['benefits']
        existing_job.application_link = job_data['application_link']
        existing_job.scraped_date = datetime.now(timezone.utc)

        # Mise à jour des informations de fraude (si les colonnes existent)
        try:
            if hasattr(existing_job, 'fraud_probability'):
                existing_job.fraud_probability = fraud_result['fraud_probability']
                existing_job.set_fraud_indicators(fraud_result['indicators'])
        except Exception as e:
            print(f"Avertissement: Impossible de mettre à jour les informations de fraude: {str(e)}")

        # Mise à jour des compétences
        existing_job.skills = []
        for skill_name in job_data['skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            existing_job.skills.append(skill)

        db.session.commit()
        return existing_job, False
    else:
        # Création d'une nouvelle offre
        new_job = Job(
            title=job_data['title'],
            company_name=job_data['company_name'],
            company_logo=job_data['company_logo'],
            description=job_data['description'],
            location=job_data['location'],
            salary=job_data['salary'],
            work_type=job_data['work_type'],
            education_required=job_data['education_required'],
            experience_required=job_data['experience_required'],
            benefits=job_data['benefits'],
            application_link=job_data['application_link'],
            source_url=job_data['source_url'],
            posted_date=datetime.now(timezone.utc),  # Dans une application réelle, on extrairait cette date du site
            scraped_date=datetime.now(timezone.utc)
        )

        # Définir les informations de fraude (si les colonnes existent)
        try:
            if hasattr(new_job, 'fraud_probability'):
                new_job.fraud_probability = fraud_result['fraud_probability']
                new_job.set_fraud_indicators(fraud_result['indicators'])
        except Exception as e:
            print(f"Avertissement: Impossible de définir les informations de fraude: {str(e)}")

        # Ajout des compétences
        for skill_name in job_data['skills']:
            skill = Skill.query.filter_by(name=skill_name).first()
            if not skill:
                skill = Skill(name=skill_name)
                db.session.add(skill)
            new_job.skills.append(skill)

        db.session.add(new_job)
        db.session.commit()
        return new_job, True

def generate_mock_jobs(query='', location='', count=20):
    """
    Génère des offres d'emploi fictives.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche
        count (int): Nombre d'offres à générer

    Returns:
        list: Liste des offres d'emploi fictives
    """
    print(f"Génération de {count} offres fictives pour '{query}' à '{location}'...")

    job_titles = [
        'Développeur Python', 'Développeur Full Stack', 'Data Scientist', 'DevOps Engineer',
        'Product Manager', 'UX/UI Designer', 'Chef de Projet IT', 'Architecte Logiciel',
        'Ingénieur QA', 'Administrateur Système', 'Développeur Mobile', 'Développeur Frontend',
        'Développeur Backend', 'Data Engineer', 'Business Intelligence Analyst', 'Scrum Master',
        'Développeur Java', 'Développeur .NET', 'Développeur PHP', 'Développeur Ruby'
    ]

    companies = [
        'TechCorp', 'WebAgency', 'DataInsight', 'CloudTech', 'AppMakers', 'SoftSolutions',
        'CodeMasters', 'DigitalWorks', 'InnovateTech', 'FutureSoft', 'SmartSystems', 'TechGenius',
        'ByteWorks', 'DevStudio', 'NetSolutions', 'InfoTech', 'GlobalSoft', 'TechInnovate',
        'CodeCrafters', 'DigitalMinds'
    ]

    locations = [
        'Paris, France', 'Lyon, France', 'Marseille, France', 'Toulouse, France', 'Bordeaux, France',
        'Lille, France', 'Nantes, France', 'Strasbourg, France', 'Montpellier, France', 'Nice, France'
    ]

    work_types = ['Présentiel', 'Télétravail', 'Mixte']

    education_levels = ['Bac', 'Bac+2', 'Bac+3', 'Bac+5', 'Bac+8']

    skill_sets = [
        ['Python', 'Django', 'Flask', 'SQL', 'Git'],
        ['JavaScript', 'React', 'Node.js', 'MongoDB', 'Express'],
        ['Python', 'R', 'Machine Learning', 'SQL', 'Tableau'],
        ['Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Terraform'],
        ['Swift', 'Kotlin', 'Flutter', 'React Native', 'Firebase'],
        ['HTML', 'CSS', 'JavaScript', 'Vue.js', 'Sass'],
        ['Java', 'Spring', 'Hibernate', 'Maven', 'JUnit'],
        ['C#', '.NET Core', 'Entity Framework', 'Azure', 'LINQ'],
        ['PHP', 'Laravel', 'Symfony', 'MySQL', 'Composer'],
        ['Ruby', 'Rails', 'PostgreSQL', 'RSpec', 'Sidekiq']
    ]

    benefits = [
        'Tickets restaurant, Mutuelle, RTT',
        'Horaires flexibles, Formation continue',
        'Prime annuelle, Télétravail partiel',
        'Participation, Intéressement, Télétravail occasionnel',
        'Smartphone fourni, Horaires flexibles',
        'Salle de sport, Cours de langues, Événements d\'équipe',
        'Assurance santé internationale, Plan d\'épargne entreprise',
        'Congés supplémentaires, Chèques vacances',
        'Budget formation, Conférences internationales',
        'Crèche d\'entreprise, Remboursement transport'
    ]

    # Générer des offres fictives diversifiées
    mock_jobs = []

    # Si une requête spécifique est fournie, ajouter quelques offres correspondantes
    if query:
        specific_count = min(5, count // 2)
        for i in range(specific_count):
            title = f"{job_titles[i % len(job_titles)]} spécialisé en {query}"
            company_name = companies[i % len(companies)]
            location_val = location or locations[i % len(locations)]
            work_type = work_types[i % len(work_types)]
            education = education_levels[i % len(education_levels)]
            skills = skill_sets[i % len(skill_sets)]
            benefit = benefits[i % len(benefits)]
            salary = 35000 + (i * 5000)
            experience = 1 + (i % 10)

            job = {
                'title': title,
                'company_name': company_name,
                'company_logo': f'https://example.com/logo{i+1}.png',
                'description': f'Nous recherchons un {title} pour rejoindre notre équipe. Vous travaillerez sur des projets innovants liés à {query}.',
                'location': location_val,
                'salary': salary,
                'work_type': work_type,
                'education_required': education,
                'experience_required': experience,
                'benefits': benefit,
                'application_link': f'https://example.com/apply{i+1}',
                'source_url': f'https://example.com/job{i+1}?q={query}',
                'skills': skills + [query] if query not in skills else skills,
                'is_mock': True  # Marquer comme offre fictive
            }
            mock_jobs.append(job)

    # Ajouter des offres génériques pour compléter
    generic_count = count - len(mock_jobs)
    for i in range(generic_count):
        idx = i % len(job_titles)
        title = job_titles[idx]
        company_name = companies[(i + 3) % len(companies)]
        location_val = location or locations[(i + 2) % len(locations)]
        work_type = work_types[i % len(work_types)]
        education = education_levels[i % len(education_levels)]
        skills = skill_sets[i % len(skill_sets)]
        benefit = benefits[i % len(benefits)]
        salary = 30000 + (i * 3000)
        experience = 1 + (i % 8)

        job = {
            'title': title,
            'company_name': company_name,
            'company_logo': f'https://example.com/logo{i+10}.png',
            'description': f'Rejoignez notre équipe en tant que {title}. Vous participerez à des projets passionnants dans un environnement dynamique.',
            'location': location_val,
            'salary': salary,
            'work_type': work_type,
            'education_required': education,
            'experience_required': experience,
            'benefits': benefit,
            'application_link': f'https://example.com/apply{i+10}',
            'source_url': f'https://example.com/job{i+10}',
            'skills': skills,
            'is_mock': True  # Marquer comme offre fictive
        }
        mock_jobs.append(job)

    return mock_jobs

def scrape_pole_emploi_jobs(query='', location=''):
    """
    Scrape les offres d'emploi depuis Pôle Emploi.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche

    Returns:
        list: Liste des offres d'emploi scrapées
    """
    if not query:
        query = "développeur"

    # Construction de l'URL de recherche Pôle Emploi
    base_url = "https://candidat.pole-emploi.fr/offres/recherche"
    params = {
        'motsCles': query,
        'lieux': location if location else 'FRANCE',
        'offresPartenaires': 'true',
        'rayon': '10',  # Rayon de recherche en km
        'tri': '0'  # Tri par pertinence
    }

    url = f"{base_url}?{'&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://candidat.pole-emploi.fr/",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Tentative de scraping de Pôle Emploi avec l'URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche des éléments d'offre d'emploi
        job_cards = soup.select('li.result')

        if not job_cards:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            job_cards = soup.select('div.result')

        if not job_cards:
            # Essayer un autre sélecteur si les précédents ne fonctionnent pas
            job_cards = soup.select('div.offre-container')

        if not job_cards:
            print("Aucun élément d'offre d'emploi trouvé sur Pôle Emploi.")
            return []

        print(f"Trouvé {len(job_cards)} offres d'emploi sur Pôle Emploi.")

        jobs = []
        for i, card in enumerate(job_cards[:20]):  # Limiter à 20 offres
            try:
                # Extraire le titre
                title_element = card.select_one('h2.t4') or card.select_one('h2.media-heading')
                title = title_element.get_text(strip=True) if title_element else f"Poste {query} {i+1}"

                # Extraire le nom de l'entreprise
                company_element = card.select_one('div.entreprise') or card.select_one('p.subtext')
                company_name = company_element.get_text(strip=True) if company_element else "Pôle Emploi"

                # Extraire le lieu
                location_element = card.select_one('span.location') or card.select_one('p.location')
                location_val = location_element.get_text(strip=True) if location_element else location or "France"

                # Extraire l'URL de l'offre
                link_element = card.select_one('a.media') or card.select_one('a.card-body')
                job_url = ""
                if link_element and 'href' in link_element.attrs:
                    job_url = link_element['href']
                    if job_url.startswith('/'):
                        job_url = f"https://candidat.pole-emploi.fr{job_url}"
                else:
                    # Essayer de trouver l'ID de l'offre
                    offer_id = None
                    if 'data-id' in card.attrs:
                        offer_id = card['data-id']
                    elif card.select_one('[data-id]'):
                        offer_id = card.select_one('[data-id]')['data-id']

                    if offer_id:
                        job_url = f"https://candidat.pole-emploi.fr/offres/recherche/detail/{offer_id}"
                    else:
                        job_url = url

                # Extraire la description (snippet)
                description_element = card.select_one('p.description') or card.select_one('div.description')
                description = description_element.get_text(strip=True) if description_element else f"Offre pour le poste de {title} chez {company_name} à {location_val}."

                # Extraire le type de contrat
                contract_element = card.select_one('span.contrat') or card.select_one('p.contrat')
                work_type = contract_element.get_text(strip=True) if contract_element else 'Non spécifié'

                # Extraire les compétences à partir de la description
                skills = extract_skills_from_description(description)

                # Créer l'objet d'offre d'emploi
                job = {
                    'title': title,
                    'company_name': company_name,
                    'company_logo': "https://www.pole-emploi.fr/themes/custom/pef/logo.svg",  # Logo Pôle Emploi par défaut
                    'description': description,
                    'location': location_val,
                    'salary': extract_salary_from_text(description),
                    'work_type': work_type,
                    'education_required': extract_education_level(description),
                    'experience_required': extract_experience_required(description),
                    'benefits': 'Non spécifié',
                    'application_link': job_url,
                    'source_url': job_url,
                    'skills': skills if skills else [query] if query else ['Non spécifié']
                }

                jobs.append(job)

                # Pause aléatoire pour éviter d'être bloqué
                time.sleep(random.uniform(0.2, 0.5))

            except Exception as e:
                print(f"Erreur lors de l'extraction de l'offre Pôle Emploi {i+1}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Erreur lors du scraping de Pôle Emploi: {str(e)}")
        return []

def scrape_linkedin_jobs(query='', location=''):
    """
    Scrape les offres d'emploi depuis LinkedIn.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche

    Returns:
        list: Liste des offres d'emploi scrapées
    """
    if not query:
        query = "développeur"

    # Construction de l'URL de recherche LinkedIn
    base_url = "https://www.linkedin.com/jobs/search"
    params = {
        'keywords': query,
        'location': location if location else 'France',
        'f_TPR': 'r2592000',  # Offres des 30 derniers jours
        'position': '1',
        'pageNum': '0'
    }

    url = f"{base_url}?{'&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.linkedin.com/",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Tentative de scraping de LinkedIn avec l'URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche des éléments d'offre d'emploi
        job_cards = soup.select('div.base-card')

        if not job_cards:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            job_cards = soup.select('li.jobs-search-results__list-item')

        if not job_cards:
            # Essayer un autre sélecteur si les précédents ne fonctionnent pas
            job_cards = soup.select('div.job-search-card')

        if not job_cards:
            print("Aucun élément d'offre d'emploi trouvé sur LinkedIn.")
            return []

        print(f"Trouvé {len(job_cards)} offres d'emploi sur LinkedIn.")

        jobs = []
        for i, card in enumerate(job_cards[:20]):  # Limiter à 20 offres
            try:
                # Extraire le titre
                title_element = card.select_one('h3.base-search-card__title') or card.select_one('h3.job-search-card__title')
                title = title_element.get_text(strip=True) if title_element else f"Poste {query} {i+1}"

                # Extraire le nom de l'entreprise (avec plusieurs sélecteurs possibles)
                company_element = card.select_one('h4.base-search-card__subtitle') or card.select_one('a.job-search-card__subtitle-link')
                if not company_element:
                    company_element = card.select_one('a.hidden-nested-link') or card.select_one('span.job-search-card__company-name')

                company_name = company_element.get_text(strip=True) if company_element else "Entreprise non spécifiée"

                # Nettoyer le nom de l'entreprise
                company_name = company_name.replace("·", "").strip()

                # Extraire le lieu
                location_element = card.select_one('span.job-search-card__location') or card.select_one('div.base-search-card__metadata')
                location_val = location_element.get_text(strip=True) if location_element else location or "France"

                # Extraire l'URL de l'offre
                link_element = card.select_one('a.base-card__full-link') or card.select_one('a.job-search-card__link')
                job_url = ""
                if link_element and 'href' in link_element.attrs:
                    job_url = link_element['href']
                else:
                    # Essayer de trouver l'ID de l'offre
                    job_id = None
                    if 'data-id' in card.attrs:
                        job_id = card['data-id']
                    elif 'data-job-id' in card.attrs:
                        job_id = card['data-job-id']
                    elif card.select_one('[data-job-id]'):
                        job_id = card.select_one('[data-job-id]')['data-job-id']

                    if job_id:
                        job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                    else:
                        job_url = url

                # Extraire la date de publication
                date_element = card.select_one('time.job-search-card__listdate') or card.select_one('time')
                posted_date = date_element.get_text(strip=True) if date_element else "Récemment"

                # Extraire la description (snippet)
                description = f"Offre pour le poste de {title} chez {company_name} à {location_val}. Publiée {posted_date}."

                # Créer l'objet d'offre d'emploi
                job = {
                    'title': title,
                    'company_name': company_name,
                    'company_logo': f"https://logo.clearbit.com/{company_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
                    'description': description,
                    'location': location_val,
                    'salary': None,  # LinkedIn n'affiche généralement pas les salaires dans les résultats de recherche
                    'work_type': 'Non spécifié',
                    'education_required': 'Non spécifié',
                    'experience_required': None,
                    'benefits': 'Non spécifié',
                    'application_link': job_url,
                    'source_url': job_url,
                    'skills': [query] if query else ['Non spécifié']
                }

                jobs.append(job)

                # Pause aléatoire pour éviter d'être bloqué
                time.sleep(random.uniform(0.2, 0.5))

            except Exception as e:
                print(f"Erreur lors de l'extraction de l'offre LinkedIn {i+1}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Erreur lors du scraping de LinkedIn: {str(e)}")
        return []

def scrape_monster_jobs(query='', location=''):
    """
    Scrape les offres d'emploi depuis Monster.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche

    Returns:
        list: Liste des offres d'emploi scrapées
    """
    if not query:
        query = "développeur"

    # Construction de l'URL de recherche Monster
    base_url = "https://www.monster.fr/emploi/recherche"
    params = {
        'q': query,
        'where': location if location else 'France',
        'page': '1'
    }

    url = f"{base_url}?{'&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://www.monster.fr/",
        "Sec-Ch-Ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        print(f"Tentative de scraping de Monster avec l'URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Recherche des éléments d'offre d'emploi
        job_cards = soup.select('div.job-cardstyle__JobCardComponent-sc-1mbmxes-0')

        if not job_cards:
            # Essayer un autre sélecteur si le premier ne fonctionne pas
            job_cards = soup.select('article.job-card')

        if not job_cards:
            # Essayer un autre sélecteur si les précédents ne fonctionnent pas
            job_cards = soup.select('div.results-card')

        if not job_cards:
            print("Aucun élément d'offre d'emploi trouvé sur Monster.")
            return []

        print(f"Trouvé {len(job_cards)} offres d'emploi sur Monster.")

        jobs = []
        for i, card in enumerate(job_cards[:20]):  # Limiter à 20 offres
            try:
                # Extraire le titre
                title_element = card.select_one('h2.job-cardstyle__JobCardTitle-sc-1mbmxes-2') or card.select_one('h3.job-card-title')
                title = title_element.get_text(strip=True) if title_element else f"Poste {query} {i+1}"

                # Extraire le nom de l'entreprise (avec plusieurs sélecteurs possibles)
                company_element = card.select_one('span.job-cardstyle__CompanyNameAndLocation-sc-1mbmxes-3') or card.select_one('div.company')
                if not company_element:
                    company_element = card.select_one('div.job-cardstyle__JobCardCompany-sc-1mbmxes-7') or card.select_one('span.name')

                company_text = company_element.get_text(strip=True) if company_element else "Entreprise non spécifiée"

                # Extraire le nom de l'entreprise (peut contenir le lieu)
                company_parts = company_text.split(' - ')
                company_name = company_parts[0] if company_parts else company_text

                # Extraire le lieu
                location_element = card.select_one('span.job-cardstyle__Location-sc-1mbmxes-4') or card.select_one('div.location')
                location_val = location_element.get_text(strip=True) if location_element else (company_parts[1] if len(company_parts) > 1 else location or "France")

                # Extraire l'URL de l'offre
                link_element = card.select_one('a.job-cardstyle__JobCardComponent-sc-1mbmxes-0') or card.select_one('a.job-card-link')
                job_url = ""
                if link_element and 'href' in link_element.attrs:
                    job_url = link_element['href']
                    if not job_url.startswith('http'):
                        job_url = f"https://www.monster.fr{job_url}"
                else:
                    job_url = url

                # Extraire la date de publication
                date_element = card.select_one('span.job-cardstyle__JobCardDate-sc-1mbmxes-5') or card.select_one('time')
                posted_date = date_element.get_text(strip=True) if date_element else "Récemment"

                # Extraire la description (snippet)
                description_element = card.select_one('span.job-cardstyle__JobCardSnippet-sc-1mbmxes-11') or card.select_one('p.job-card-snippet')
                description = description_element.get_text(strip=True) if description_element else f"Offre pour le poste de {title} chez {company_name} à {location_val}. Publiée {posted_date}."

                # Créer l'objet d'offre d'emploi
                job = {
                    'title': title,
                    'company_name': company_name,
                    'company_logo': f"https://logo.clearbit.com/{company_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com",
                    'description': description,
                    'location': location_val,
                    'salary': extract_salary_from_text(description),
                    'work_type': 'Non spécifié',
                    'education_required': 'Non spécifié',
                    'experience_required': extract_experience_required(description),
                    'benefits': 'Non spécifié',
                    'application_link': job_url,
                    'source_url': job_url,
                    'skills': extract_skills_from_description(description) or [query] if query else ['Non spécifié']
                }

                jobs.append(job)

                # Pause aléatoire pour éviter d'être bloqué
                time.sleep(random.uniform(0.2, 0.5))

            except Exception as e:
                print(f"Erreur lors de l'extraction de l'offre Monster {i+1}: {str(e)}")
                continue

        return jobs

    except Exception as e:
        print(f"Erreur lors du scraping de Monster: {str(e)}")
        return []

def scrape_jobs(query='', location=''):
    """
    Scrape les offres d'emploi depuis plusieurs sources et les sauvegarde en base de données.
    N'utilise que des offres réelles.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche

    Returns:
        int: Nombre de nouvelles offres ajoutées
    """
    all_jobs = []

    # Récupérer les offres depuis LinkedIn (priorité haute)
    linkedin_jobs = scrape_linkedin_jobs(query, location)
    if linkedin_jobs:
        print(f"Trouvé {len(linkedin_jobs)} offres sur LinkedIn pour '{query}' à '{location}'.")
        all_jobs.extend(linkedin_jobs)

    # Récupérer les offres depuis Monster
    monster_jobs = scrape_monster_jobs(query, location)
    if monster_jobs:
        print(f"Trouvé {len(monster_jobs)} offres sur Monster pour '{query}' à '{location}'.")
        all_jobs.extend(monster_jobs)

    # Récupérer les offres depuis Indeed
    indeed_jobs = scrape_indeed_jobs(query, location)
    if indeed_jobs:
        print(f"Trouvé {len(indeed_jobs)} offres sur Indeed pour '{query}' à '{location}'.")
        all_jobs.extend(indeed_jobs)

    # Si on n'a pas assez d'offres, essayer Pôle Emploi
    if len(all_jobs) < 15:
        pole_emploi_jobs = scrape_pole_emploi_jobs(query, location)
        if pole_emploi_jobs:
            print(f"Trouvé {len(pole_emploi_jobs)} offres sur Pôle Emploi pour '{query}' à '{location}'.")
            all_jobs.extend(pole_emploi_jobs)

    # Si aucune offre n'est trouvée, informer l'utilisateur
    if not all_jobs:
        print(f"Aucune offre trouvée pour '{query}' à '{location}'.")
        return 0

    print(f"Trouvé un total de {len(all_jobs)} offres réelles pour '{query}' à '{location}'.")

    # Filtrer les offres d'emploi avec des liens d'exemple
    filtered_jobs = []
    for job in all_jobs:
        # Vérifier si l'offre a un lien d'exemple
        if 'source_url' in job and job['source_url'] and 'example.com' not in job['source_url']:
            # Supprimer le marqueur is_mock s'il existe
            if 'is_mock' in job:
                job.pop('is_mock')

            # Nettoyer le nom de l'entreprise
            if 'company_name' in job and job['company_name']:
                job['company_name'] = clean_company_name(job['company_name'])

            filtered_jobs.append(job)

    print(f"Après filtrage des offres fictives: {len(filtered_jobs)} offres réelles sur {len(all_jobs)} offres trouvées.")

    # Si aucune offre réelle n'est trouvée après filtrage
    if not filtered_jobs:
        print(f"Aucune offre réelle trouvée pour '{query}' à '{location}' après filtrage.")
        return 0

    # Sauvegarder les offres en base de données
    new_jobs_count = 0
    for job_data in filtered_jobs:
        _, is_new = save_job_to_db(job_data)
        if is_new:
            new_jobs_count += 1

    return new_jobs_count
