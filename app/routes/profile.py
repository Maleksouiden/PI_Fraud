import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.profile import Profile, Skill

profile = Blueprint('profile', __name__)

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, folder):
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Créer un nom de fichier unique
        unique_filename = f"{current_user.id}_{filename}"
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, unique_filename)
        file.save(file_path)
        
        # Retourner le chemin relatif pour stockage en base de données
        return os.path.join(folder, unique_filename)
    return None

@profile.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    # Vérifier si l'utilisateur a déjà un profil
    if current_user.profile:
        return redirect(url_for('profile.edit_profile'))
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        title = request.form.get('title')
        years_experience = request.form.get('years_experience', type=int)
        education_level = request.form.get('education_level')
        desired_salary = request.form.get('desired_salary', type=int)
        desired_location = request.form.get('desired_location')
        work_type = request.form.get('work_type')
        skills_input = request.form.get('skills')
        
        # Validation des données
        if not first_name or not last_name:
            flash('Le prénom et le nom sont obligatoires.', 'danger')
            return render_template('profile/create.html')
        
        # Création du profil
        profile = Profile(
            user_id=current_user.id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            title=title,
            years_experience=years_experience,
            education_level=education_level,
            desired_salary=desired_salary,
            desired_location=desired_location,
            work_type=work_type
        )
        
        # Traitement des compétences
        if skills_input:
            skills_list = [s.strip() for s in skills_input.split(',')]
            for skill_name in skills_list:
                # Vérifier si la compétence existe déjà
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                profile.skills.append(skill)
        
        # Traitement du CV
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and allowed_file(resume_file.filename, {'pdf', 'doc', 'docx'}):
                resume_path = save_file(resume_file, 'resumes')
                if resume_path:
                    profile.resume_path = resume_path
        
        # Traitement de la photo
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and allowed_file(photo_file.filename, {'jpg', 'jpeg', 'png'}):
                photo_path = save_file(photo_file, 'photos')
                if photo_path:
                    profile.photo_path = photo_path
        
        db.session.add(profile)
        db.session.commit()
        
        flash('Votre profil a été créé avec succès!', 'success')
        return redirect(url_for('jobs.home'))
    
    return render_template('profile/create.html')

@profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Vérifier si l'utilisateur a un profil
    if not current_user.profile:
        return redirect(url_for('profile.create_profile'))
    
    profile = current_user.profile
    
    if request.method == 'POST':
        # Mise à jour des données du profil
        profile.first_name = request.form.get('first_name')
        profile.last_name = request.form.get('last_name')
        profile.phone = request.form.get('phone')
        profile.address = request.form.get('address')
        profile.title = request.form.get('title')
        profile.years_experience = request.form.get('years_experience', type=int)
        profile.education_level = request.form.get('education_level')
        profile.desired_salary = request.form.get('desired_salary', type=int)
        profile.desired_location = request.form.get('desired_location')
        profile.work_type = request.form.get('work_type')
        
        # Mise à jour des compétences
        skills_input = request.form.get('skills')
        if skills_input:
            # Supprimer les compétences actuelles
            profile.skills = []
            
            # Ajouter les nouvelles compétences
            skills_list = [s.strip() for s in skills_input.split(',')]
            for skill_name in skills_list:
                skill = Skill.query.filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    db.session.add(skill)
                profile.skills.append(skill)
        
        # Mise à jour du CV
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file and resume_file.filename and allowed_file(resume_file.filename, {'pdf', 'doc', 'docx'}):
                resume_path = save_file(resume_file, 'resumes')
                if resume_path:
                    profile.resume_path = resume_path
        
        # Mise à jour de la photo
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and photo_file.filename and allowed_file(photo_file.filename, {'jpg', 'jpeg', 'png'}):
                photo_path = save_file(photo_file, 'photos')
                if photo_path:
                    profile.photo_path = photo_path
        
        db.session.commit()
        flash('Votre profil a été mis à jour avec succès!', 'success')
        return redirect(url_for('profile.view_profile'))
    
    # Préparer la liste des compétences pour l'affichage
    skills_str = ', '.join([skill.name for skill in profile.skills])
    
    return render_template('profile/edit.html', profile=profile, skills=skills_str)

@profile.route('/profile')
@login_required
def view_profile():
    # Vérifier si l'utilisateur a un profil
    if not current_user.profile:
        flash('Veuillez créer votre profil.', 'info')
        return redirect(url_for('profile.create_profile'))
    
    return render_template('profile/view.html', profile=current_user.profile)
