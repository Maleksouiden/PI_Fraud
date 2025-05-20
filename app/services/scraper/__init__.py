"""
Module de scraping d'offres d'emploi.
"""

from app.services.scraper.base_scraper import BaseScraper
from app.services.scraper.indeed_scraper import IndeedScraper
from app.services.scraper.linkedin_scraper import LinkedInScraper
from app.services.scraper.monster_scraper import MonsterScraper
from app.services.scraper.pole_emploi_scraper import PoleEmploiScraper
from app.services.scraper.scraper_manager import ScraperManager

__all__ = [
    'BaseScraper',
    'IndeedScraper',
    'LinkedInScraper',
    'MonsterScraper',
    'PoleEmploiScraper',
    'ScraperManager'
]
