from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.job import Job
from app.models.search_history import SearchHistory
from app.services.scraper_api import scrape_jobs
from app.services.job_matcher import match_jobs_to_profile

jobs = Blueprint('jobs', __name__)

@jobs.route('/')
def home():
    # Page d'accueil
    return render_template('jobs/home.html')

@jobs.route('/jobs')
# Temporairement désactivé pour le développement
# @login_required
def job_list():
    # Récupération des paramètres de filtrage
    query = request.args.get('query', '')
    location = request.args.get('location', '')
    work_type = request.args.get('work_type', '')
    salary_min = request.args.get('salary_min', type=int)
    skills_input = request.args.get('skills', '')
    education = request.args.get('education', '')
    experience_max = request.args.get('experience_max', type=int)
    ignore_profile = 'ignore_profile' in request.args

    # Paramètres de filtrage pour la détection de fraude
    fraud_max = request.args.get('fraud_max', type=float)
    hide_fraud = 'hide_fraud' in request.args

    # Construction de la requête de base
    job_query = Job.query

    # Application des filtres
    if query:
        job_query = job_query.filter(Job.title.ilike(f'%{query}%') |
                                     Job.description.ilike(f'%{query}%') |
                                     Job.company_name.ilike(f'%{query}%'))

    if location:
        job_query = job_query.filter(Job.location.ilike(f'%{location}%'))

    if work_type:
        job_query = job_query.filter(Job.work_type == work_type)

    if salary_min:
        job_query = job_query.filter(Job.salary >= salary_min)

    if education:
        job_query = job_query.filter(Job.education_required == education)

    if experience_max is not None:
        job_query = job_query.filter((Job.experience_required <= experience_max) | (Job.experience_required.is_(None)))

    # Filtrage par risque de fraude (si la colonne existe)
    try:
        if hasattr(Job, 'fraud_probability'):
            if fraud_max is not None:
                job_query = job_query.filter(Job.fraud_probability <= fraud_max)
            elif hide_fraud:
                # Si hide_fraud est activé, masquer les offres avec une probabilité de fraude > 0.6
                job_query = job_query.filter(Job.fraud_probability <= 0.6)
    except Exception as e:
        print(f"Avertissement: Impossible de filtrer par risque de fraude: {str(e)}")

    # Récupération des offres
    all_jobs = job_query.all()

    # Filtrer les offres avec des liens d'exemple
    filtered_jobs = []
    for job in all_jobs:
        if job.source_url and 'example.com' not in job.source_url:
            filtered_jobs.append(job)

    # Utiliser les offres filtrées
    all_jobs = filtered_jobs

    # Filtrage par compétences (nécessite un post-traitement car c'est une relation many-to-many)
    if skills_input:
        skills_list = [s.strip().lower() for s in skills_input.split(',')]
        filtered_jobs = []
        for job in all_jobs:
            job_skills = [skill.name.lower() for skill in job.skills]
            # Vérifier si au moins une compétence correspond
            if any(skill in job_skills for skill in skills_list):
                filtered_jobs.append(job)
        all_jobs = filtered_jobs

    # Si l'utilisateur a un profil et ne souhaite pas l'ignorer, trier les offres par score de correspondance
    if current_user.is_authenticated and current_user.profile and not ignore_profile:
        # Calculer le score de correspondance pour chaque offre
        scored_jobs = [(job, current_user.profile.match_score(job)) for job in all_jobs]
        # Trier par score décroissant
        scored_jobs.sort(key=lambda x: x[1], reverse=True)
        # Extraire les offres triées
        jobs_list = [job for job, score in scored_jobs]
        # Préparer les scores pour l'affichage
        job_scores = {job.id: score for job, score in scored_jobs}
    else:
        # Sans profil ou si l'utilisateur souhaite ignorer son profil, pas de tri personnalisé
        jobs_list = all_jobs
        job_scores = {}

    # Enregistrement de la recherche dans l'historique
    if current_user.is_authenticated and (query or location or work_type or salary_min or skills_input or education or experience_max or fraud_max or hide_fraud):
        search_history = SearchHistory(
            user_id=current_user.id,
            search_query=query,
            location_filter=location,
            work_type_filter=work_type,
            salary_min_filter=salary_min
        )
        db.session.add(search_history)
        db.session.commit()

    return render_template('jobs/list.html',
                          jobs=jobs_list,
                          job_scores=job_scores,
                          query=query,
                          location=location,
                          work_type=work_type,
                          salary_min=salary_min,
                          skills=skills_input,
                          education=education,
                          experience_max=experience_max,
                          ignore_profile=ignore_profile,
                          fraud_max=fraud_max,
                          hide_fraud=hide_fraud)

@jobs.route('/jobs/<int:job_id>')
# Temporairement désactivé pour le développement
# @login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)

    # Ajouter l'offre à l'historique de recherche le plus récent
    if current_user.is_authenticated:
        # Récupérer l'historique de recherche le plus récent
        search_history = SearchHistory.query.filter_by(user_id=current_user.id).order_by(
            SearchHistory.search_date.desc()).first()

        if search_history and job not in search_history.viewed_jobs:
            search_history.viewed_jobs.append(job)
            db.session.commit()

    # Calculer le score de correspondance si l'utilisateur a un profil
    match_score = None
    if current_user.is_authenticated and current_user.profile:
        match_score = current_user.profile.match_score(job)

    # Récupérer les informations de fraude
    fraud_indicators = job.get_fraud_indicators()
    fraud_risk_level, fraud_risk_class = job.get_fraud_risk_level()

    return render_template('jobs/detail.html',
                          job=job,
                          match_score=match_score,
                          fraud_indicators=fraud_indicators,
                          fraud_risk_level=fraud_risk_level,
                          fraud_risk_class=fraud_risk_class)

@jobs.route('/jobs/refresh')
# Temporairement désactivé pour le développement
# @login_required
def refresh_jobs():
    # Commenté pour le développement
    # if not current_user.is_authenticated:
    #     flash('Vous devez être connecté pour effectuer cette action.', 'danger')
    #     return redirect(url_for('auth.login'))

    # Récupérer les paramètres de recherche s'ils sont fournis
    query = request.args.get('query', '')
    location = request.args.get('location', '')

    # Si aucun paramètre n'est fourni, demander à l'utilisateur de spécifier des termes de recherche
    if not query and not location:
        flash('Veuillez spécifier des termes de recherche pour trouver des offres d\'emploi réelles.', 'info')
        return redirect(url_for('jobs.job_list'))
    else:
        # Lancer le scraping avec les paramètres fournis
        try:
            flash(f'Recherche d\'offres d\'emploi réelles pour "{query}" à "{location}" en cours... Cette opération peut prendre quelques instants.', 'info')

            print(f"Scraping en temps réel pour '{query}' à '{location}'...")
            new_jobs_count = scrape_jobs(query, location)

            if new_jobs_count > 0:
                flash(f'{new_jobs_count} nouvelles offres d\'emploi réelles ont été scrapées pour "{query}" à "{location}".', 'success')
            else:
                flash(f'Aucune nouvelle offre d\'emploi trouvée pour "{query}" à "{location}". Essayez avec d\'autres termes de recherche ou vérifiez les offres existantes.', 'warning')
        except Exception as e:
            flash(f'Erreur lors du scraping des offres: {str(e)}', 'danger')

    return redirect(url_for('jobs.job_list', query=query, location=location))

@jobs.route('/jobs/match')
@login_required
def match_jobs():
    # Vérifier si l'utilisateur a un profil
    if not current_user.profile:
        flash('Vous devez créer un profil pour utiliser cette fonctionnalité.', 'info')
        return redirect(url_for('profile.create_profile'))

    # Récupérer les offres correspondant au profil
    matched_jobs = match_jobs_to_profile(current_user.profile)

    # Filtrer les offres avec des liens d'exemple
    filtered_jobs = []
    for job in matched_jobs:
        if job.source_url and 'example.com' not in job.source_url:
            filtered_jobs.append(job)

    # Utiliser les offres filtrées
    matched_jobs = filtered_jobs

    # Calculer les scores de correspondance
    scored_jobs = [(job, current_user.profile.match_score(job)) for job in matched_jobs]
    scored_jobs.sort(key=lambda x: x[1], reverse=True)

    jobs_list = [job for job, score in scored_jobs]
    job_scores = {job.id: score for job, score in scored_jobs}

    return render_template('jobs/match.html',
                          jobs=jobs_list,
                          job_scores=job_scores)
