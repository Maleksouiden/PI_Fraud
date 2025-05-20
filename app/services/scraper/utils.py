"""
Utilitaires pour le scraping d'offres d'emploi.
"""

import re
import logging
import time
import urllib.parse
from urllib.robotparser import RobotFileParser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from app.config.scraper_config import EXTRACTION_PATTERNS, COMMON_SKILLS

# Configuration du logger
logger = logging.getLogger('scraper')
logger.setLevel(logging.INFO)

# Vérifier si le logger a déjà des handlers pour éviter les doublons
if not logger.handlers:
    handler = logging.FileHandler('scraper.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def create_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 503, 504)):
    """
    Crée une session HTTP avec gestion automatique des retries.
    
    Args:
        retries (int): Nombre de tentatives en cas d'échec
        backoff_factor (float): Facteur de temporisation entre les tentatives
        status_forcelist (tuple): Liste des codes HTTP qui déclenchent un retry
        
    Returns:
        requests.Session: Session HTTP configurée
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def safe_select(element, selectors):
    """
    Tente d'appliquer plusieurs sélecteurs CSS et retourne le premier résultat trouvé.
    
    Args:
        element: Élément BeautifulSoup à interroger
        selectors (list): Liste de sélecteurs CSS à essayer
        
    Returns:
        BeautifulSoup element ou None: Premier élément trouvé ou None si aucun match
    """
    if not element:
        return None
        
    for selector in selectors:
        result = element.select_one(selector)
        if result:
            return result
    return None

def check_robots_permission(url, user_agent):
    """
    Vérifie si le scraping est autorisé selon le fichier robots.txt du site.
    
    Args:
        url (str): URL à vérifier
        user_agent (str): User-Agent à utiliser pour la vérification
        
    Returns:
        bool: True si le scraping est autorisé, False sinon
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        rp = RobotFileParser()
        rp.set_url(f"{base_url}/robots.txt")
        rp.read()
        
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification du robots.txt pour {url}: {str(e)}")
        # En cas d'erreur, on suppose que c'est autorisé
        return True

def check_blocked(soup, url):
    """
    Vérifie si la page indique que nous sommes bloqués.
    
    Args:
        soup (BeautifulSoup): Objet BeautifulSoup de la page
        url (str): URL de la page
        
    Returns:
        bool: True si nous sommes bloqués, False sinon
    """
    if not soup:
        return True
        
    # Vérifier le titre de la page
    blocked_titles = ['Access Denied', 'Bot detected', 'Captcha', 'Security check', 'Forbidden']
    title = soup.title.string if soup.title else ''
    
    if any(bt.lower() in title.lower() for bt in blocked_titles):
        logger.warning(f"Détection de blocage sur {url}: {title}")
        return True
        
    # Vérifier les éléments de captcha courants
    captcha_selectors = ['#captcha', '.captcha', '#recaptcha', '.g-recaptcha']
    if any(soup.select_one(selector) for selector in captcha_selectors):
        logger.warning(f"Captcha détecté sur {url}")
        return True
        
    return False

def extract_salary(text):
    """
    Extrait le salaire à partir d'un texte en utilisant plusieurs patterns.
    
    Args:
        text (str): Texte contenant potentiellement un salaire
        
    Returns:
        int, tuple ou None: Salaire extrait, fourchette de salaire ou None
    """
    if not text:
        return None
        
    for pattern, processor in EXTRACTION_PATTERNS['salary']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return processor(match)
            except (ValueError, IndexError):
                continue
                
    return None

def extract_experience(text):
    """
    Extrait le nombre d'années d'expérience requis à partir d'un texte.
    
    Args:
        text (str): Texte contenant potentiellement une exigence d'expérience
        
    Returns:
        int ou None: Nombre d'années d'expérience ou None
    """
    if not text:
        return None
        
    for pattern, processor in EXTRACTION_PATTERNS['experience']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return processor(match)
            except (ValueError, IndexError):
                continue
                
    return None

def extract_skills(text):
    """
    Extrait les compétences techniques à partir d'un texte.
    
    Args:
        text (str): Texte contenant potentiellement des compétences
        
    Returns:
        list: Liste des compétences trouvées
    """
    if not text:
        return []
        
    found_skills = []
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
            
    return found_skills

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

def rate_limit(config):
    """
    Applique une limitation de débit selon la configuration.
    
    Args:
        config (dict): Configuration de limitation de débit
    """
    if not config:
        return
        
    calls = config.get('calls', 5)
    period = config.get('period', 60)
    
    # Calculer le temps d'attente entre chaque appel
    wait_time = period / calls
    
    # Attendre
    time.sleep(wait_time)

def format_url(base_url, params, query, location):
    """
    Formate une URL avec les paramètres de recherche.
    
    Args:
        base_url (str): URL de base
        params (dict): Paramètres de l'URL
        query (str): Terme de recherche
        location (str): Lieu de recherche
        
    Returns:
        str: URL formatée
    """
    # Remplacer les placeholders dans les paramètres
    formatted_params = {}
    for key, value in params.items():
        if isinstance(value, str):
            value = value.format(query=query, location=location)
        formatted_params[key] = value
    
    # Construire l'URL
    param_strings = []
    for key, value in formatted_params.items():
        param_strings.append(f"{key}={urllib.parse.quote(str(value))}")
    
    return f"{base_url}?{'&'.join(param_strings)}"
