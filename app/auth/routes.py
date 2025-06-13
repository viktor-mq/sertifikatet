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
from ..utils.email import (send_verification_email, send_password_reset_email, 
                          verify_email_token, verify_reset_token)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Check if email is verified
            if not user.is_verified:
                flash('Du må bekrefte e-postadressen din før du kan logge inn. Sjekk innboksen din.', 'warning')
                return redirect(url_for('auth.login'))
            
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
        
        # Send verification email
        send_verification_email(user)
        
        flash('Registrering vellykket! Vi har sendt en bekreftelse til din e-postadresse. '
              'Vennligst sjekk innboksen din for å aktivere kontoen.', 'success')
        return redirect(url_for('auth.login'))
    
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


@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Verify email address with token"""
    email = verify_email_token(token)
    
    if not email:
        flash('Bekreftelseslenken er ugyldig eller utløpt.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Ingen bruker funnet med denne e-postadressen.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('E-postadressen din er allerede bekreftet.', 'info')
        return redirect(url_for('auth.login'))
    
    # Verify the user
    user.is_verified = True
    db.session.commit()
    
    flash('E-postadressen din er nå bekreftet! Du kan logge inn.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        # Always show success message to prevent email enumeration
        flash('Hvis denne e-postadressen er registrert, vil du motta en e-post '
              'med instruksjoner for å tilbakestille passordet.', 'info')
        
        if user:
            send_password_reset_email(user)
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    email = verify_reset_token(token)
    
    if not email:
        flash('Tilbakestillingslenken er ugyldig eller utløpt.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Ingen bruker funnet.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 8:
            flash('Passordet må være minst 8 tegn langt.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passordene er ikke like.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        flash('Passordet ditt har blitt oppdatert! Du kan nå logge inn.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/resend-verification')
def resend_verification():
    """Resend verification email"""
    if current_user.is_authenticated:
        if current_user.is_verified:
            flash('E-postadressen din er allerede bekreftet.', 'info')
        else:
            send_verification_email(current_user)
            flash('En ny bekreftelsese-post har blitt sendt.', 'success')
    else:
        flash('Du må logge inn før du kan be om ny bekreftelse.', 'error')
    
    return redirect(url_for('auth.login'))
