from app.models.job import Job

def match_jobs_to_profile(profile, min_score=10, limit=100):  # Réduire le score minimum et augmenter la limite
    """
    Trouve les offres d'emploi qui correspondent le mieux au profil de l'utilisateur.

    Args:
        profile: Le profil de l'utilisateur
        min_score (int): Score minimum de correspondance (0-100)
        limit (int): Nombre maximum d'offres à retourner

    Returns:
        list: Liste des offres d'emploi correspondantes
    """
    # Récupérer toutes les offres d'emploi
    all_jobs = Job.query.all()

    # Filtrer les offres avec des liens d'exemple
    real_jobs = []
    for job in all_jobs:
        if job.source_url and 'example.com' not in job.source_url:
            real_jobs.append(job)

    # Utiliser les offres réelles
    all_jobs = real_jobs

    # Calculer le score de correspondance pour chaque offre
    scored_jobs = []
    for job in all_jobs:
        score = profile.match_score(job)
        if score >= min_score:
            scored_jobs.append((job, score))

    # Trier par score décroissant
    scored_jobs.sort(key=lambda x: x[1], reverse=True)

    # Limiter le nombre de résultats
    top_jobs = [job for job, _ in scored_jobs[:limit]]

    return top_jobs

def filter_jobs_by_criteria(jobs, criteria):
    """
    Filtre une liste d'offres d'emploi selon des critères spécifiques.

    Args:
        jobs (list): Liste des offres d'emploi
        criteria (dict): Critères de filtrage

    Returns:
        list: Liste des offres d'emploi filtrées
    """
    filtered_jobs = jobs

    # Filtrer par titre
    if 'title' in criteria and criteria['title']:
        filtered_jobs = [job for job in filtered_jobs if criteria['title'].lower() in job.title.lower()]

    # Filtrer par lieu
    if 'location' in criteria and criteria['location']:
        filtered_jobs = [job for job in filtered_jobs if criteria['location'].lower() in job.location.lower()]

    # Filtrer par type de travail
    if 'work_type' in criteria and criteria['work_type']:
        filtered_jobs = [job for job in filtered_jobs if job.work_type == criteria['work_type']]

    # Filtrer par salaire minimum
    if 'salary_min' in criteria and criteria['salary_min']:
        filtered_jobs = [job for job in filtered_jobs if job.salary and job.salary >= criteria['salary_min']]

    # Filtrer par niveau d'études
    if 'education' in criteria and criteria['education']:
        filtered_jobs = [job for job in filtered_jobs if job.education_required == criteria['education']]

    # Filtrer par expérience requise
    if 'experience_max' in criteria and criteria['experience_max'] is not None:
        filtered_jobs = [job for job in filtered_jobs if job.experience_required and job.experience_required <= criteria['experience_max']]

    # Filtrer par compétences
    if 'skills' in criteria and criteria['skills']:
        required_skills = set(criteria['skills'])
        filtered_jobs = [
            job for job in filtered_jobs if
            any(skill.name.lower() in required_skills for skill in job.skills)
        ]

    return filtered_jobs
