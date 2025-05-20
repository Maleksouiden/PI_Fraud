"""
Classe de base pour les scrapers d'offres d'emploi.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from app.services.scraper.utils import (
    create_session, safe_select, check_robots_permission, 
    check_blocked, rate_limit, format_url, extract_salary,
    extract_experience, extract_skills, clean_company_name
)

# Configuration du logger
logger = logging.getLogger('scraper')

class BaseScraper(ABC):
    """
    Classe de base pour tous les scrapers d'offres d'emploi.
    """
    
    def __init__(self, config):
        """
        Initialise le scraper avec sa configuration.
        
        Args:
            config (dict): Configuration du scraper
        """
        self.config = config
        self.session = create_session()
        self.name = "base"  # À surcharger dans les classes dérivées
        
    @abstractmethod
    def scrape(self, query, location):
        """
        Méthode abstraite à implémenter dans les classes dérivées.
        
        Args:
            query (str): Terme de recherche
            location (str): Lieu de recherche
            
        Returns:
            list: Liste des offres d'emploi scrapées
        """
        pass
        
    def _get_page(self, url):
        """
        Récupère une page web et la parse avec BeautifulSoup.
        
        Args:
            url (str): URL à récupérer
            
        Returns:
            BeautifulSoup ou None: Objet BeautifulSoup de la page ou None en cas d'erreur
        """
        try:
            # Vérifier si le scraping est autorisé
            user_agent = self.config['headers'].get('User-Agent', 'Mozilla/5.0')
            if not check_robots_permission(url, user_agent):
                logger.warning(f"Scraping non autorisé pour {url} selon robots.txt")
                return None
                
            # Appliquer la limitation de débit
            rate_limit(self.config.get('rate_limit'))
                
            # Effectuer la requête
            logger.info(f"Récupération de {url}")
            response = self.session.get(url, headers=self.config['headers'], timeout=10)
            response.raise_for_status()
            
            # Parser la page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Vérifier si nous sommes bloqués
            if check_blocked(soup, url):
                logger.error(f"Accès bloqué pour {url}")
                return None
                
            return soup
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de {url}: {str(e)}")
            return None
            
    def _extract_job_cards(self, soup):
        """
        Extrait les cartes d'offres d'emploi d'une page.
        
        Args:
            soup (BeautifulSoup): Objet BeautifulSoup de la page
            
        Returns:
            list: Liste des cartes d'offres d'emploi
        """
        if not soup:
            return []
            
        selectors = self.config['selectors']['cards']
        
        for selector in selectors:
            cards = soup.select(selector)
            if cards:
                logger.info(f"Trouvé {len(cards)} offres avec le sélecteur '{selector}'")
                return cards
                
        logger.warning(f"Aucune offre trouvée avec les sélecteurs {selectors}")
        return []
        
    def _extract_text(self, element, selectors, default=""):
        """
        Extrait le texte d'un élément en utilisant plusieurs sélecteurs.
        
        Args:
            element: Élément BeautifulSoup
            selectors (list): Liste de sélecteurs CSS
            default (str): Valeur par défaut si aucun élément n'est trouvé
            
        Returns:
            str: Texte extrait ou valeur par défaut
        """
        result = safe_select(element, selectors)
        return result.get_text(strip=True) if result else default
        
    def _extract_attribute(self, element, selectors, attribute, default=""):
        """
        Extrait un attribut d'un élément en utilisant plusieurs sélecteurs.
        
        Args:
            element: Élément BeautifulSoup
            selectors (list): Liste de sélecteurs CSS
            attribute (str): Nom de l'attribut à extraire
            default (str): Valeur par défaut si aucun élément n'est trouvé
            
        Returns:
            str: Attribut extrait ou valeur par défaut
        """
        result = safe_select(element, selectors)
        return result.get(attribute, default) if result else default
        
    def _build_job_data(self, card, query, location, base_url):
        """
        Construit un dictionnaire de données d'offre d'emploi à partir d'une carte.
        
        Args:
            card: Élément BeautifulSoup représentant une carte d'offre d'emploi
            query (str): Terme de recherche
            location (str): Lieu de recherche
            base_url (str): URL de base du site
            
        Returns:
            dict: Données de l'offre d'emploi
        """
        # Cette méthode doit être implémentée dans les classes dérivées
        # car chaque site a une structure différente
        pass
