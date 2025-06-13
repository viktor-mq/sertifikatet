# app/auth/routes.py
from flask import render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.orm import Query
from . import auth_bp
from .. import db
from ..models import User, UserProgress, QuizSession
from flask_login import login_user, logout_user, login_required, current_user


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash(f'Velkommen tilbake, {user.full_name or user.username}!', 'success')
            # Redirect to dashboard or intended page
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Ugyldig brukernavn eller passord', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        # Validate inputs
        if not all([username, email, password]):
            flash('Alle felt må fylles ut', 'error')
            return redirect(url_for('auth.register'))
            
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Brukernavnet er allerede tatt', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('E-postadressen er allerede registrert', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create user progress record
        user_progress = UserProgress(user_id=user.id)
        db.session.add(user_progress)
        
        db.session.commit()
        
        # Auto-login after registration
        login_user(user)
        
        flash('Velkommen til TeoriTest! La oss starte din læringsreise.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Du har blitt logget ut. Vi sees!', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = current_user
    
    # Get user progress and statistics
    progress = user.progress
    recent_sessions = (
        QuizSession.query
        .filter_by(user_id=current_user.id)
        .order_by(QuizSession.completed_at.desc())
        .limit(5)
        .all()
    )
    achievements = user.achievements
    
    # Calculate statistics
    total_score = 0
    if progress and progress.total_questions_answered > 0:
        total_score = (progress.correct_answers / progress.total_questions_answered) * 100
    
    return render_template('auth/profile.html', 
                         user=user, 
                         progress=progress,
                         recent_sessions=recent_sessions,
                         achievements=achievements,
                         total_score=total_score)
