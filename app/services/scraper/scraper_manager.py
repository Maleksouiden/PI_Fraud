"""
Gestionnaire de scrapers d'offres d'emploi.
"""

import logging
import concurrent.futures
from datetime import datetime, timezone

from app.models.job import Job
from app.models.profile import Skill
from app import db
from app.services.fraud_detection import predict_job_fraud
from app.services.scraper.indeed_scraper import IndeedScraper
from app.services.scraper.linkedin_scraper import LinkedInScraper
from app.services.scraper.monster_scraper import MonsterScraper
from app.services.scraper.pole_emploi_scraper import PoleEmploiScraper

# Configuration du logger
logger = logging.getLogger('scraper')

class ScraperManager:
    """
    Gestionnaire de scrapers d'offres d'emploi.
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire de scrapers.
        """
        self.scrapers = {
            'indeed': IndeedScraper(),
            'linkedin': LinkedInScraper(),
            'monster': MonsterScraper(),
            'pole_emploi': PoleEmploiScraper()
        }
        
    def scrape_all(self, query='', location='', parallel=True):
        """
        Scrape les offres d'emploi depuis tous les sites configurés.
        
        Args:
            query (str): Terme de recherche
            location (str): Lieu de recherche
            parallel (bool): Si True, exécute les scrapers en parallèle
            
        Returns:
            int: Nombre de nouvelles offres ajoutées
        """
        logger.info(f"Démarrage du scraping pour '{query}' à '{location}'")
        
        all_jobs = []
        
        if parallel:
            # Exécution parallèle des scrapers
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.scrapers)) as executor:
                future_to_scraper = {
                    executor.submit(scraper.scrape, query, location): name
                    for name, scraper in self.scrapers.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_scraper):
                    scraper_name = future_to_scraper[future]
                    try:
                        jobs = future.result()
                        logger.info(f"Scraper {scraper_name}: {len(jobs)} offres trouvées")
                        all_jobs.extend(jobs)
                    except Exception as e:
                        logger.error(f"Erreur avec le scraper {scraper_name}: {str(e)}")
        else:
            # Exécution séquentielle des scrapers
            for name, scraper in self.scrapers.items():
                try:
                    jobs = scraper.scrape(query, location)
                    logger.info(f"Scraper {name}: {len(jobs)} offres trouvées")
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Erreur avec le scraper {name}: {str(e)}")
                    
        # Filtrer les offres d'emploi avec des liens d'exemple
        filtered_jobs = []
        for job in all_jobs:
            # Vérifier si l'offre a un lien d'exemple
            if 'source_url' in job and job['source_url'] and 'example.com' not in job['source_url']:
                filtered_jobs.append(job)
                
        logger.info(f"Après filtrage: {len(filtered_jobs)} offres réelles sur {len(all_jobs)} offres trouvées")
        
        # Si aucune offre réelle n'est trouvée après filtrage
        if not filtered_jobs:
            logger.warning(f"Aucune offre réelle trouvée pour '{query}' à '{location}' après filtrage")
            return 0
            
        # Sauvegarder les offres en base de données
        new_jobs_count = self._save_jobs_to_db(filtered_jobs)
        logger.info(f"{new_jobs_count} nouvelles offres ajoutées à la base de données")
        
        return new_jobs_count
        
    def _save_jobs_to_db(self, jobs_data):
        """
        Sauvegarde les offres d'emploi en base de données avec une approche optimisée.
        
        Args:
            jobs_data (list): Liste des données d'offres d'emploi
            
        Returns:
            int: Nombre de nouvelles offres ajoutées
        """
        # Récupérer toutes les compétences existantes
        existing_skills = {skill.name: skill for skill in Skill.query.all()}
        
        # Récupérer toutes les URLs sources existantes
        existing_urls = {job.source_url for job in Job.query.all()}
        
        # Préparer les nouvelles compétences à ajouter
        new_skills = {}
        for job_data in jobs_data:
            for skill_name in job_data.get('skills', []):
                if skill_name not in existing_skills and skill_name not in new_skills:
                    new_skill = Skill(name=skill_name)
                    new_skills[skill_name] = new_skill
                    db.session.add(new_skill)
        
        # Sauvegarder les nouvelles compétences
        if new_skills:
            db.session.commit()
            logger.info(f"Ajout de {len(new_skills)} nouvelles compétences")
            
            # Mettre à jour le dictionnaire des compétences existantes
            existing_skills.update(new_skills)
        
        # Compteur de nouvelles offres
        new_jobs_count = 0
        
        # Traiter chaque offre
        for job_data in jobs_data:
            # Vérifier si l'offre existe déjà
            if job_data['source_url'] in existing_urls:
                # Mise à jour de l'offre existante
                self._update_existing_job(job_data, existing_skills)
            else:
                # Création d'une nouvelle offre
                self._create_new_job(job_data, existing_skills)
                new_jobs_count += 1
                existing_urls.add(job_data['source_url'])
        
        # Sauvegarder les modifications
        db.session.commit()
        
        return new_jobs_count
        
    def _update_existing_job(self, job_data, existing_skills):
        """
        Met à jour une offre d'emploi existante.
        
        Args:
            job_data (dict): Données de l'offre d'emploi
            existing_skills (dict): Dictionnaire des compétences existantes
        """
        existing_job = Job.query.filter_by(source_url=job_data['source_url']).first()
        
        if not existing_job:
            return
            
        # Mise à jour des champs
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
        existing_job.scraped_date = datetime.now(timezone.utc).replace(year=2023)
        
        # Analyser l'offre pour détecter les fraudes
        fraud_result = predict_job_fraud(job_data)
        
        # Mise à jour des informations de fraude
        try:
            if hasattr(existing_job, 'fraud_probability'):
                existing_job.fraud_probability = fraud_result['fraud_probability']
                existing_job.set_fraud_indicators(fraud_result['indicators'])
        except Exception as e:
            logger.warning(f"Impossible de mettre à jour les informations de fraude: {str(e)}")
        
        # Mise à jour des compétences
        existing_job.skills = []
        for skill_name in job_data['skills']:
            if skill_name in existing_skills:
                existing_job.skills.append(existing_skills[skill_name])
        
    def _create_new_job(self, job_data, existing_skills):
        """
        Crée une nouvelle offre d'emploi.
        
        Args:
            job_data (dict): Données de l'offre d'emploi
            existing_skills (dict): Dictionnaire des compétences existantes
        """
        # Analyser l'offre pour détecter les fraudes
        fraud_result = predict_job_fraud(job_data)
        
        # Création de la nouvelle offre
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
            posted_date=datetime.now(timezone.utc).replace(year=2023),
            scraped_date=datetime.now(timezone.utc).replace(year=2023)
        )
        
        # Définir les informations de fraude
        try:
            if hasattr(new_job, 'fraud_probability'):
                new_job.fraud_probability = fraud_result['fraud_probability']
                new_job.set_fraud_indicators(fraud_result['indicators'])
        except Exception as e:
            logger.warning(f"Impossible de définir les informations de fraude: {str(e)}")
        
        # Ajout des compétences
        for skill_name in job_data['skills']:
            if skill_name in existing_skills:
                new_job.skills.append(existing_skills[skill_name])
        
        db.session.add(new_job)
