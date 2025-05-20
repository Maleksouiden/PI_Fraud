import re
from app.models.user import User

def validate_registration(username, email, password, confirm_password):
    """
    Valide les données d'inscription d'un utilisateur.
    
    Args:
        username (str): Nom d'utilisateur
        email (str): Adresse email
        password (str): Mot de passe
        confirm_password (str): Confirmation du mot de passe
        
    Returns:
        str: Message d'erreur ou None si les données sont valides
    """
    # Vérifier que tous les champs sont remplis
    if not username or not email or not password or not confirm_password:
        return "Tous les champs sont obligatoires."
    
    # Vérifier la longueur du nom d'utilisateur
    if len(username) < 3 or len(username) > 20:
        return "Le nom d'utilisateur doit contenir entre 3 et 20 caractères."
    
    # Vérifier le format de l'email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return "L'adresse email n'est pas valide."
    
    # Vérifier si le nom d'utilisateur existe déjà
    if User.query.filter_by(username=username).first():
        return "Ce nom d'utilisateur est déjà pris."
    
    # Vérifier si l'email existe déjà
    if User.query.filter_by(email=email).first():
        return "Cette adresse email est déjà utilisée."
    
    # Vérifier la longueur du mot de passe
    if len(password) < 6:
        return "Le mot de passe doit contenir au moins 6 caractères."
    
    # Vérifier que les mots de passe correspondent
    if password != confirm_password:
        return "Les mots de passe ne correspondent pas."
    
    # Toutes les validations sont passées
    return None

def validate_login(email, password):
    """
    Valide les données de connexion d'un utilisateur.
    
    Args:
        email (str): Adresse email
        password (str): Mot de passe
        
    Returns:
        tuple: (User, error_message) - L'utilisateur si les données sont valides, sinon None et un message d'erreur
    """
    # Vérifier que tous les champs sont remplis
    if not email or not password:
        return None, "Tous les champs sont obligatoires."
    
    # Rechercher l'utilisateur par email
    user = User.query.filter_by(email=email).first()
    if not user:
        return None, "Email ou mot de passe incorrect."
    
    # Vérifier le mot de passe
    if not user.check_password(password):
        return None, "Email ou mot de passe incorrect."
    
    # Toutes les validations sont passées
    return user, None
