"""
Configuration pour les différents scrapers de sites d'emploi.
Ce fichier centralise les paramètres de configuration pour faciliter la maintenance.
"""

# Configuration des sélecteurs CSS et paramètres pour chaque site
SCRAPER_CONFIG = {
    'indeed': {
        'base_url': 'https://fr.indeed.com/emplois',
        'selectors': {
            'cards': ['div.job_seen_beacon', 'div.cardOutline', 'div[data-testid="job-card"]'],
            'title': ['h2.jobTitle span', 'a.jcs-JobTitle span', 'h2 a', 'h2'],
            'company': ['span.companyName', 'div.company_location > pre > span.companyName', 
                       'div[data-testid="company-name"]', 'span[data-testid="company-name"]',
                       '.company-name', '.companyInfo'],
            'location': ['div.companyLocation', 'div[data-testid="text-location"]'],
            'salary': ['div.salary-snippet-container', 'div[data-testid="attribute_snippet_testid"]'],
            'link': ['h2.jobTitle a', 'a.jcs-JobTitle', 'h2 a'],
            'description': ['div.job-snippet', 'div[data-testid="job-snippet"]'],
            'metadata': ['div.metadata', 'div[data-testid="attribute_snippet_testid"]']
        },
        'params': {
            'q': '{query}',
            'l': '{location}',
            'sort': 'date',
            'fromage': '1'  # Offres des dernières 24 heures
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://fr.indeed.com/',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        },
        'rate_limit': {'calls': 5, 'period': 60}  # 5 appels par minute
    },
    'linkedin': {
        'base_url': 'https://www.linkedin.com/jobs/search',
        'selectors': {
            'cards': ['div.base-card', 'li.jobs-search-results__list-item', 'div.job-search-card'],
            'title': ['h3.base-search-card__title', 'h3.job-search-card__title'],
            'company': ['h4.base-search-card__subtitle', 'a.job-search-card__subtitle-link', 
                       'a.hidden-nested-link', 'span.job-search-card__company-name'],
            'location': ['span.job-search-card__location', 'div.base-search-card__metadata'],
            'link': ['a.base-card__full-link', 'a.job-search-card__link'],
            'date': ['time.job-search-card__listdate', 'time']
        },
        'params': {
            'keywords': '{query}',
            'location': '{location}',
            'f_TPR': 'r86400',  # Offres des dernières 24 heures
            'position': '1',
            'pageNum': '0'
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.linkedin.com/',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        },
        'rate_limit': {'calls': 3, 'period': 60}  # 3 appels par minute (plus restrictif)
    },
    'monster': {
        'base_url': 'https://www.monster.fr/emploi/recherche',
        'selectors': {
            'cards': ['div.job-cardstyle__JobCardComponent', 'div.results-card'],
            'title': ['h3.job-cardstyle__JobCardTitle', 'a.title'],
            'company': ['span.job-cardstyle__CompanyName', 'div.company'],
            'location': ['span.job-cardstyle__Location', 'div.location'],
            'link': ['a.job-cardstyle__JobCardComponent', 'a.title']
        },
        'params': {
            'q': '{query}',
            'where': '{location}',
            'page': '1',
            'recency': '1'  # Offres des dernières 24 heures
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://www.monster.fr/',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        },
        'rate_limit': {'calls': 5, 'period': 60}  # 5 appels par minute
    },
    'pole_emploi': {
        'base_url': 'https://candidat.pole-emploi.fr/offres/recherche',
        'selectors': {
            'cards': ['li.result', 'div.result', 'div.offre-container'],
            'title': ['h2.t4', 'h2.media-heading'],
            'company': ['div.entreprise', 'p.subtext'],
            'location': ['span.location', 'p.location'],
            'link': ['a.media', 'a.card-body'],
            'description': ['p.description', 'div.description'],
            'contract': ['span.contrat', 'p.contrat']
        },
        'params': {
            'motsCles': '{query}',
            'lieux': '{location}',
            'offresPartenaires': 'true',
            'rayon': '10',
            'tri': '1',
            'typeContrat': '',
            'qualification': '',
            'periodeEmission': '1'  # Offres des dernières 24 heures
        },
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'https://candidat.pole-emploi.fr/',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        },
        'rate_limit': {'calls': 5, 'period': 60}  # 5 appels par minute
    }
}

# Patterns pour l'extraction de données
EXTRACTION_PATTERNS = {
    'salary': [
        # Format "50 000 €"
        (r'(\d{1,3}(?:\s?\d{3})*)\s*[€kK]', lambda m: int(m.group(1).replace(' ', ''))),
        # Format "50 000 euros"
        (r'(\d{1,3}(?:\s?\d{3})*)\s*euros', lambda m: int(m.group(1).replace(' ', ''))),
        # Format "50.5k", "50,5k"
        (r'(\d{1,2})[.,](\d{1,3})\s*[kK]', lambda m: int(float(m.group(1) + '.' + m.group(2)) * 1000)),
        # Format "50k-65k" (fourchette)
        (r'(\d{1,2})[.,]?(\d{0,3})\s*[kK][-–]\s*(\d{1,2})[.,]?(\d{0,3})\s*[kK]', 
         lambda m: (int(float(m.group(1) + '.' + (m.group(2) or '0')) * 1000), 
                    int(float(m.group(3) + '.' + (m.group(4) or '0')) * 1000)))
    ],
    'experience': [
        # Format "5 ans d'expérience"
        (r'(\d+)\s*(?:an(?:s|née)?(?:s)?)\s*d[\'"]expérience', lambda m: int(m.group(1))),
        # Format "expérience de 5 ans"
        (r'expérience\s*(?:de|d[\'"])?\s*(\d+)\s*an(?:s|née)?(?:s)?', lambda m: int(m.group(1))),
        # Format "5 ans d'ancienneté"
        (r'(\d+)\s*(?:an(?:s|née)?(?:s)?)\s*d[\'""]ancienneté', lambda m: int(m.group(1)))
    ]
}

# Liste des compétences techniques courantes
COMMON_SKILLS = [
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
