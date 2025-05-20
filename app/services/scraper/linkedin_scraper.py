"""
Scraper pour LinkedIn.
"""

import logging
import time
import random
from datetime import datetime, timezone

from app.config.scraper_config import SCRAPER_CONFIG
from app.services.scraper.base_scraper import BaseScraper
from app.services.scraper.utils import (
    format_url, extract_experience, extract_skills, clean_company_name
)

# Configuration du logger
logger = logging.getLogger('scraper')

class LinkedInScraper(BaseScraper):
    """
    Scraper pour LinkedIn.
    """
    
    def __init__(self):
        """
        Initialise le scraper LinkedIn.
        """
        super().__init__(SCRAPER_CONFIG['linkedin'])
        self.name = "linkedin"
        
    def scrape(self, query, location):
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
            
        # Construire l'URL
        url = format_url(
            self.config['base_url'],
            self.config['params'],
            query,
            location if location else 'France'
        )
        
        # Récupérer la page
        soup = self._get_page(url)
        if not soup:
            logger.error(f"Impossible de récupérer la page LinkedIn: {url}")
            return []
            
        # Extraire les cartes d'offres
        job_cards = self._extract_job_cards(soup)
        logger.info(f"Trouvé {len(job_cards)} offres d'emploi sur LinkedIn")
        
        # Extraire les données de chaque carte
        jobs = []
        for i, card in enumerate(job_cards[:20]):  # Limiter à 20 offres
            try:
                job_data = self._build_job_data(card, query, location, url)
                if job_data:
                    jobs.append(job_data)
                    
                # Pause aléatoire pour éviter d'être bloqué
                time.sleep(random.uniform(0.2, 0.5))
                
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction de l'offre LinkedIn {i+1}: {str(e)}")
                continue
                
        return jobs
        
    def _build_job_data(self, card, query, location, base_url):
        """
        Construit un dictionnaire de données d'offre d'emploi à partir d'une carte LinkedIn.
        
        Args:
            card: Élément BeautifulSoup représentant une carte d'offre d'emploi
            query (str): Terme de recherche
            location (str): Lieu de recherche
            base_url (str): URL de base du site
            
        Returns:
            dict: Données de l'offre d'emploi
        """
        selectors = self.config['selectors']
        
        # Extraire le titre
        title = self._extract_text(card, selectors['title'], f"Poste {query}")
        
        # Extraire le nom de l'entreprise
        company_name = self._extract_text(card, selectors['company'], "Entreprise non spécifiée")
        company_name = clean_company_name(company_name)
        
        # Extraire le lieu
        location_val = self._extract_text(card, selectors['location'], location or "France")
        
        # Extraire l'URL de l'offre
        job_url = self._extract_attribute(card, selectors['link'], 'href', "")
        
        # Si pas d'URL, essayer de trouver l'ID de l'offre
        if not job_url:
            job_id = card.get('data-id') or card.get('data-job-id')
            if not job_id and card.select_one('[data-job-id]'):
                job_id = card.select_one('[data-job-id]').get('data-job-id')
                
            if job_id:
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            else:
                job_url = base_url
                
        # Extraire la date de publication
        posted_date = self._extract_text(card, selectors['date'], "Récemment")
        
        # Créer une description
        description = f"Offre pour le poste de {title} chez {company_name} à {location_val}. Publiée {posted_date}."
        
        # Extraire les compétences
        skills = extract_skills(description)
        
        # Nettoyer le nom de l'entreprise pour le logo
        clean_company_for_logo = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        if len(clean_company_for_logo) < 3:
            clean_company_for_logo = "company"  # Fallback pour les noms trop courts
            
        # Créer l'objet d'offre d'emploi
        job = {
            'title': title,
            'company_name': company_name,
            'company_logo': f"https://logo.clearbit.com/{clean_company_for_logo}.com",
            'description': description,
            'location': location_val,
            'salary': None,  # LinkedIn n'affiche généralement pas les salaires
            'work_type': 'Non spécifié',
            'education_required': 'Non spécifié',
            'experience_required': extract_experience(description),
            'benefits': 'Non spécifié',
            'application_link': job_url,
            'source_url': job_url,
            'skills': skills if skills else [query] if query else ['Non spécifié'],
            'source': 'LinkedIn',
            'scraped_date': datetime.now(timezone.utc).replace(year=2023)
        }
        
        return job
