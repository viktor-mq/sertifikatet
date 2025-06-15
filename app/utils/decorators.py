# app/utils/decorators.py
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn for å få tilgang til denne siden.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user is admin (you can modify this check based on your User model)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            # Alternative check: username-based
            if current_user.username != 'Viktor':
                flash('Du har ikke tilgang til denne siden.', 'danger')
                return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def subscription_required(tier=None):
    """Decorator to require a specific subscription tier or higher"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Du må logge inn for å få tilgang til denne funksjonen.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check subscription tier
            user_tier = getattr(current_user, 'subscription_tier', 'free')
            
            # Define tier hierarchy
            tier_hierarchy = {
                'free': 0,
                'premium': 1,
                'pro': 2
            }
            
            # If no specific tier required, just need to be logged in
            if tier is None:
                return f(*args, **kwargs)
            
            # Check if user's tier is sufficient
            if tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(tier, 0):
                return f(*args, **kwargs)
            else:
                flash(f'Denne funksjonen krever {tier} abonnement eller høyere.', 'info')
                return redirect(url_for('main.dashboard'))
        
        return decorated_function
    return decorator


def gamification_required(f):
    """Decorator to ensure user has gamification profile"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn for å få tilgang til denne siden.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user has progress/gamification profile
        if not hasattr(current_user, 'progress') or not current_user.progress:
            # Could auto-create it here or redirect to setup
            flash('Gamification-profil ikke funnet. Kontakt support.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function
