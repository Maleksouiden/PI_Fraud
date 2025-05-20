"""
Scraper pour Pôle Emploi.
"""

import logging
import time
import random
from datetime import datetime, timezone

from app.config.scraper_config import SCRAPER_CONFIG
from app.services.scraper.base_scraper import BaseScraper
from app.services.scraper.utils import (
    format_url, extract_salary, extract_experience, 
    extract_skills, clean_company_name
)

# Configuration du logger
logger = logging.getLogger('scraper')

class PoleEmploiScraper(BaseScraper):
    """
    Scraper pour Pôle Emploi.
    """
    
    def __init__(self):
        """
        Initialise le scraper Pôle Emploi.
        """
        super().__init__(SCRAPER_CONFIG['pole_emploi'])
        self.name = "pole_emploi"
        
    def scrape(self, query, location):
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
            
        # Construire l'URL
        url = format_url(
            self.config['base_url'],
            self.config['params'],
            query,
            location if location else 'FRANCE'
        )
        
        # Récupérer la page
        soup = self._get_page(url)
        if not soup:
            logger.error(f"Impossible de récupérer la page Pôle Emploi: {url}")
            return []
            
        # Extraire les cartes d'offres
        job_cards = self._extract_job_cards(soup)
        logger.info(f"Trouvé {len(job_cards)} offres d'emploi sur Pôle Emploi")
        
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
                logger.error(f"Erreur lors de l'extraction de l'offre Pôle Emploi {i+1}: {str(e)}")
                continue
                
        return jobs
        
    def _build_job_data(self, card, query, location, base_url):
        """
        Construit un dictionnaire de données d'offre d'emploi à partir d'une carte Pôle Emploi.
        
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
        company_name = self._extract_text(card, selectors['company'], "Pôle Emploi")
        company_name = clean_company_name(company_name)
        
        # Extraire le lieu
        location_val = self._extract_text(card, selectors['location'], location or "France")
        
        # Extraire l'URL de l'offre
        job_url = self._extract_attribute(card, selectors['link'], 'href', "")
        if job_url and job_url.startswith('/'):
            job_url = f"https://candidat.pole-emploi.fr{job_url}"
        elif not job_url:
            # Essayer de trouver l'ID de l'offre
            offer_id = None
            if 'data-id' in card.attrs:
                offer_id = card['data-id']
            elif card.select_one('[data-id]'):
                offer_id = card.select_one('[data-id]')['data-id']
                
            if offer_id:
                job_url = f"https://candidat.pole-emploi.fr/offres/recherche/detail/{offer_id}"
            else:
                job_url = base_url
                
        # Extraire la description
        description = self._extract_text(card, selectors['description'], f"Offre pour le poste de {title} chez {company_name} à {location_val}.")
        
        # Extraire le type de contrat
        work_type = self._extract_text(card, selectors['contract'], 'Non spécifié')
        
        # Extraire les compétences
        skills = extract_skills(description)
        
        # Créer l'objet d'offre d'emploi
        job = {
            'title': title,
            'company_name': company_name,
            'company_logo': "https://www.pole-emploi.fr/themes/custom/pef/logo.svg",  # Logo Pôle Emploi par défaut
            'description': description,
            'location': location_val,
            'salary': extract_salary(description),
            'work_type': work_type,
            'education_required': self._extract_education_level(description),
            'experience_required': extract_experience(description),
            'benefits': 'Non spécifié',
            'application_link': job_url,
            'source_url': job_url,
            'skills': skills if skills else [query] if query else ['Non spécifié'],
            'source': 'Pôle Emploi',
            'scraped_date': datetime.now(timezone.utc).replace(year=2023)
        }
        
        return job
        
    def _extract_education_level(self, description):
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
