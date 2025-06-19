"""
Subscription enforcement decorators and utilities
Ensures users can only access features according to their subscription plan
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, jsonify, request
from flask_login import current_user
from app.services.payment_service import SubscriptionService


def subscription_required(required_feature):
    """
    Decorator to check if user has access to a specific feature
    Usage: @subscription_required('has_video_access')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Du må logge inn for å få tilgang til denne funksjonen', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if user has the required feature
            has_access = SubscriptionService.user_has_feature(current_user.id, required_feature)
            
            if not has_access:
                # Get user's current plan for better error message
                current_plan = SubscriptionService.get_user_plan(current_user.id)
                
                if request.is_json:
                    return jsonify({
                        'error': 'Insufficient subscription',
                        'message': 'Du trenger en Premium eller Pro plan for tilgang til denne funksjonen',
                        'current_plan': current_plan,
                        'required_feature': required_feature
                    }), 403
                
                flash(f'Denne funksjonen krever Premium eller Pro plan. Du har {current_plan.title()} plan.', 'warning')
                return redirect(url_for('subscription.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def quiz_limit_check(quiz_type='practice'):
    """
    Decorator to check quiz limits for free users
    Usage: @quiz_limit_check('practice') or @quiz_limit_check('exam')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Du må logge inn for å ta quiz', 'warning')
                return redirect(url_for('auth.login'))
            
            # Check if user can take this type of quiz
            can_take, message = SubscriptionService.can_user_take_quiz(current_user.id, quiz_type)
            
            if not can_take:
                if request.is_json:
                    return jsonify({
                        'error': 'Quiz limit reached',
                        'message': message,
                        'quiz_type': quiz_type
                    }), 403
                
                flash(message, 'warning')
                return redirect(url_for('subscription.plans'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def video_access_required(f):
    """
    Decorator specifically for video access
    Usage: @video_access_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn for å se videoer', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user can watch videos
        can_watch, message = SubscriptionService.can_user_watch_video(current_user.id)
        
        if not can_watch:
            if request.is_json:
                return jsonify({
                    'error': 'Video access denied',
                    'message': message
                }), 403
            
            flash(message, 'warning')
            return redirect(url_for('subscription.plans'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin access
    Usage: @admin_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            flash('Du har ikke tilgang til admin-funksjoner', 'error')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def pro_feature_required(f):
    """
    Decorator specifically for Pro plan features
    Usage: @pro_feature_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Du må logge inn', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user has Pro plan features
        user_plan = SubscriptionService.get_user_plan(current_user.id)
        
        if user_plan != 'pro':
            if request.is_json:
                return jsonify({
                    'error': 'Pro plan required',
                    'message': 'Denne funksjonen krever Pro plan',
                    'current_plan': user_plan
                }), 403
            
            flash('Denne funksjonen krever Pro plan', 'warning')
            return redirect(url_for('subscription.plans'))
        
        return f(*args, **kwargs)
    return decorated_function
