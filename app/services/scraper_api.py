"""
API pour le scraping d'offres d'emploi.
"""

import logging
from app.services.scraper.scraper_manager import ScraperManager

# Configuration du logger
logger = logging.getLogger('scraper')

def scrape_jobs(query='', location='', parallel=True):
    """
    Scrape les offres d'emploi depuis plusieurs sources et les sauvegarde en base de données.
    N'utilise que des offres réelles.

    Args:
        query (str): Terme de recherche
        location (str): Lieu de recherche
        parallel (bool): Si True, exécute les scrapers en parallèle

    Returns:
        int: Nombre de nouvelles offres ajoutées
    """
    # Créer une instance du gestionnaire de scrapers
    scraper_manager = ScraperManager()
    
    # Lancer le scraping
    return scraper_manager.scrape_all(query, location, parallel)
