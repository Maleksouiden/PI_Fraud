from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models.user import User
from app.services.auth_service import validate_registration, validate_login

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('jobs.home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation des données
        error = validate_registration(username, email, password, confirm_password)
        if error:
            flash(error, 'danger')
            return render_template('auth/signup.html')
        
        # Création du nouvel utilisateur
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Votre compte a été créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('jobs.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Validation des données
        user, error = validate_login(email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')
        
        # Connexion de l'utilisateur
        login_user(user, remember=remember)
        
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        # Redirection vers la page de création de profil si l'utilisateur n'a pas encore de profil
        if not user.profile:
            flash('Veuillez compléter votre profil pour continuer.', 'info')
            return redirect(url_for('profile.create_profile'))
        
        return redirect(url_for('jobs.home'))
    
    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Vérification si le nom d'utilisateur ou l'email existe déjà
        if username != current_user.username and User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return redirect(url_for('auth.account'))
        
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('auth.account'))
        
        # Mise à jour des informations
        current_user.username = username
        current_user.email = email
        
        db.session.commit()
        flash('Votre compte a été mis à jour avec succès!', 'success')
        return redirect(url_for('auth.account'))
    
    return render_template('auth/account.html')
