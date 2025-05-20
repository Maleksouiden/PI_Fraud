from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.search_history import SearchHistory

history = Blueprint('history', __name__)

@history.route('/history')
@login_required
def search_history():
    # Récupérer l'historique de recherche de l'utilisateur
    user_history = SearchHistory.query.filter_by(user_id=current_user.id).order_by(
        SearchHistory.search_date.desc()).all()
    
    return render_template('jobs/history.html', history=user_history)

@history.route('/history/<int:history_id>')
@login_required
def history_detail(history_id):
    # Récupérer l'historique spécifique
    search_history = SearchHistory.query.get_or_404(history_id)
    
    # Vérifier que l'historique appartient à l'utilisateur connecté
    if search_history.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à accéder à cet historique.', 'danger')
        return redirect(url_for('history.search_history'))
    
    return render_template('jobs/history_detail.html', history=search_history)

@history.route('/history/<int:history_id>/delete')
@login_required
def delete_history(history_id):
    # Récupérer l'historique spécifique
    search_history = SearchHistory.query.get_or_404(history_id)
    
    # Vérifier que l'historique appartient à l'utilisateur connecté
    if search_history.user_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à supprimer cet historique.', 'danger')
        return redirect(url_for('history.search_history'))
    
    # Supprimer l'historique
    db.session.delete(search_history)
    db.session.commit()
    
    flash('L\'historique de recherche a été supprimé avec succès.', 'success')
    return redirect(url_for('history.search_history'))

@history.route('/history/clear')
@login_required
def clear_history():
    # Supprimer tout l'historique de l'utilisateur
    SearchHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    flash('Votre historique de recherche a été entièrement supprimé.', 'success')
    return redirect(url_for('history.search_history'))
