# app/gamification/routes.py
from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
from . import gamification_bp
from .services import GamificationService
from app import db
from app.models import User, Achievement, UserAchievement
from app.gamification_models import (
    UserLevel, DailyChallenge, UserDailyChallenge,
    WeeklyTournament, TournamentParticipant, PowerUp, UserPowerUp,
    FriendChallenge, XPTransaction
)


@gamification_bp.route('/dashboard')
@login_required
def dashboard():
    """Gamification dashboard"""
    
    # Calculate everything directly from total_xp (single source of truth)
    total_xp = current_user.total_xp or 0
    current_level = GamificationService.calculate_level_from_xp(total_xp)
    xp_for_current_level = GamificationService.calculate_total_xp_for_level(current_level)
    xp_for_next_level = GamificationService.calculate_total_xp_for_level(current_level + 1)
    
    # Create user_level object for template
    user_level = type('UserLevel', (), {
        'current_level': current_level,
        'current_xp': total_xp - xp_for_current_level,
        'next_level_xp': xp_for_next_level - xp_for_current_level,
        'total_xp': total_xp
    })()
    
    # Get daily challenges
    daily_challenges = GamificationService.get_daily_challenges(current_user)
    
    # Get active tournaments
    active_tournaments = WeeklyTournament.query.filter(
        WeeklyTournament.is_active == True,
        WeeklyTournament.end_date > datetime.utcnow()
    ).all()
    
    # Get user's tournament participations
    user_tournaments = TournamentParticipant.query.filter_by(
        user_id=current_user.id
    ).join(WeeklyTournament).filter(
        WeeklyTournament.is_active == True
    ).all()
    
    # Get recent achievements
    recent_achievements = UserAchievement.query.filter_by(
        user_id=current_user.id
    ).order_by(UserAchievement.earned_at.desc()).limit(5).all()
    
    # Get leaderboard rankings
    rankings = GamificationService.get_user_ranking(current_user, 'weekly')
    
    # Get available power-ups
    power_ups = PowerUp.query.filter_by(is_active=True).all()
    user_powerups = UserPowerUp.query.filter_by(
        user_id=current_user.id,
        used_at=None
    ).all()
    
    # Get recent XP transactions
    recent_xp = XPTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(XPTransaction.created_at.desc()).limit(10).all()
    
    return render_template('gamification/dashboard.html',
                         user_level=user_level,
                         daily_challenges=daily_challenges,
                         active_tournaments=active_tournaments,
                         user_tournaments=user_tournaments,
                         recent_achievements=recent_achievements,
                         rankings=rankings,
                         power_ups=power_ups,
                         user_powerups=user_powerups,
                         recent_xp=recent_xp)


@gamification_bp.route('/achievements')
@login_required
def achievements():
    """View all achievements"""
    from app.services.achievement_service import AchievementService
    
    # Use the updated AchievementService
    achievement_service = AchievementService()
    user_achievements = achievement_service.get_user_achievements(current_user.id)
    
    # Group achievements by category
    achievements_by_category = {}
    for achievement in user_achievements:
        category = achievement['category'] or 'Generelt'
        if category not in achievements_by_category:
            achievements_by_category[category] = []
        achievements_by_category[category].append(achievement)
    
    # Calculate progress
    total_achievements = len(user_achievements)
    earned_achievements = len([a for a in user_achievements if a['earned']])
    progress_percentage = (earned_achievements / total_achievements * 100) if total_achievements > 0 else 0
    
    return render_template('progress/achievements.html',
                         achievements_by_category=achievements_by_category,
                         total_achievements=total_achievements,
                         earned_achievements=earned_achievements,
                         progress_percentage=progress_percentage)


@gamification_bp.route('/leaderboard')
@login_required
def leaderboard():
    """View leaderboards"""
    period = request.args.get('period', 'weekly')
    
    # Get rankings for different periods
    weekly_rankings = GamificationService.get_user_ranking(current_user, 'weekly')
    monthly_rankings = GamificationService.get_user_ranking(current_user, 'monthly')
    alltime_rankings = GamificationService.get_user_ranking(current_user, 'all-time')
    
    # Get category-specific leaderboards
    category_leaders = {}
    categories = ['Trafikkskilt', 'Trafikkregler', 'Farlige situasjoner']
    
    for category in categories:
        # Get top performers in each category
        top_users = db.session.query(
            User.id,
            User.username,
            db.func.avg(QuizSession.score).label('avg_score'),
            db.func.count(QuizSession.id).label('quiz_count')
        ).join(QuizSession).filter(
            QuizSession.category == category,
            QuizSession.completed_at != None
        ).group_by(User.id).having(
            db.func.count(QuizSession.id) >= 5  # Min 5 quizzes
        ).order_by(db.func.avg(QuizSession.score).desc()).limit(10).all()
        
        category_leaders[category] = top_users
    
    return render_template('gamification/leaderboard.html',
                         weekly_rankings=weekly_rankings,
                         monthly_rankings=monthly_rankings,
                         alltime_rankings=alltime_rankings,
                         category_leaders=category_leaders,
                         current_period=period)


@gamification_bp.route('/tournaments')
@login_required
def tournaments():
    """View all tournaments"""
    # Get active tournaments
    active_tournaments = WeeklyTournament.query.filter(
        WeeklyTournament.is_active == True,
        WeeklyTournament.end_date > datetime.utcnow()
    ).order_by(WeeklyTournament.start_date).all()
    
    # Get upcoming tournaments
    upcoming_tournaments = WeeklyTournament.query.filter(
        WeeklyTournament.start_date > datetime.utcnow()
    ).order_by(WeeklyTournament.start_date).limit(5).all()
    
    # Get user's tournament history
    user_tournaments = TournamentParticipant.query.filter_by(
        user_id=current_user.id
    ).join(WeeklyTournament).order_by(
        WeeklyTournament.start_date.desc()
    ).limit(10).all()
    
    # Get tournament winners
    recent_winners = db.session.query(
        TournamentParticipant, User, WeeklyTournament
    ).join(User).join(WeeklyTournament).filter(
        TournamentParticipant.rank == 1,
        WeeklyTournament.end_date < datetime.utcnow()
    ).order_by(WeeklyTournament.end_date.desc()).limit(5).all()
    
    return render_template('gamification/tournaments.html',
                         active_tournaments=active_tournaments,
                         upcoming_tournaments=upcoming_tournaments,
                         user_tournaments=user_tournaments,
                         recent_winners=recent_winners)


@gamification_bp.route('/tournament/<int:tournament_id>')
@login_required
def tournament_detail(tournament_id):
    """View tournament details and rankings"""
    tournament = WeeklyTournament.query.get_or_404(tournament_id)
    
    # Get participants and rankings
    participants = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id
    ).join(User).order_by(TournamentParticipant.score.desc()).all()
    
    # Check if user is participating
    user_participant = TournamentParticipant.query.filter_by(
        user_id=current_user.id,
        tournament_id=tournament_id
    ).first()
    
    # Calculate prize distribution
    total_participants = len(participants)
    prizes = []
    if tournament.prize_pool_xp > 0:
        prizes = [
            {'rank': 1, 'xp': int(tournament.prize_pool_xp * 0.5)},
            {'rank': 2, 'xp': int(tournament.prize_pool_xp * 0.3)},
            {'rank': 3, 'xp': int(tournament.prize_pool_xp * 0.2)},
        ]
    
    return render_template('gamification/tournament_detail.html',
                         tournament=tournament,
                         participants=participants,
                         user_participant=user_participant,
                         prizes=prizes,
                         total_participants=total_participants)


@gamification_bp.route('/tournament/<int:tournament_id>/join', methods=['POST'])
@login_required
def join_tournament(tournament_id):
    """Join a tournament"""
    success, message = GamificationService.join_tournament(current_user, tournament_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('gamification.tournament_detail', tournament_id=tournament_id))


@gamification_bp.route('/daily-challenges')
@login_required
def daily_challenges():
    """View daily challenges"""
    # Get today's challenges
    challenges = GamificationService.get_daily_challenges(current_user)
    
    # Get challenge history
    challenge_history = UserDailyChallenge.query.filter_by(
        user_id=current_user.id
    ).join(DailyChallenge).order_by(
        DailyChallenge.date.desc()
    ).limit(30).all()
    
    # Calculate statistics
    total_completed = UserDailyChallenge.query.filter_by(
        user_id=current_user.id,
        completed=True
    ).count()
    
    total_xp_earned = db.session.query(
        db.func.sum(UserDailyChallenge.xp_earned)
    ).filter_by(
        user_id=current_user.id
    ).scalar() or 0
    
    return render_template('gamification/daily_challenges.html',
                         challenges=challenges,
                         challenge_history=challenge_history,
                         total_completed=total_completed,
                         total_xp_earned=total_xp_earned)


@gamification_bp.route('/power-ups')
@login_required
def power_ups():
    """View and purchase power-ups"""
    # Get all available power-ups
    available_power_ups = PowerUp.query.filter_by(is_active=True).all()
    
    # Get user's power-ups
    user_powerups = UserPowerUp.query.filter_by(
        user_id=current_user.id
    ).all()
    
    # Group user's power-ups
    owned_powerups = {}
    active_powerups = []
    
    for up in user_powerups:
        if up.used_at is None:
            if up.power_up_id not in owned_powerups:
                owned_powerups[up.power_up_id] = 0
            owned_powerups[up.power_up_id] += up.quantity
        elif up.expires_at and up.expires_at > datetime.utcnow():
            active_powerups.append(up)
    
    return render_template('gamification/power_ups.html',
                         available_power_ups=available_power_ups,
                         owned_powerups=owned_powerups,
                         active_powerups=active_powerups,
                         user_xp=current_user.total_xp)


@gamification_bp.route('/power-up/<int:power_up_id>/buy', methods=['POST'])
@login_required
def buy_power_up(power_up_id):
    """Purchase a power-up"""
    power_up = PowerUp.query.get_or_404(power_up_id)
    
    # Check if user has enough XP
    if current_user.total_xp < power_up.cost_xp:
        flash(f'Du trenger {power_up.cost_xp} XP for å kjøpe {power_up.name}', 'error')
        return redirect(url_for('gamification.power_ups'))
    
    # Deduct XP
    GamificationService.award_xp(
        current_user,
        -power_up.cost_xp,
        'power_up_purchase',
        f'Kjøpte: {power_up.name}',
        power_up.id
    )
    
    # Add power-up to user's inventory
    user_power_up = UserPowerUp(
        user_id=current_user.id,
        power_up_id=power_up.id
    )
    db.session.add(user_power_up)
    db.session.commit()
    
    flash(f'{power_up.name} kjøpt!', 'success')
    return redirect(url_for('gamification.power_ups'))


@gamification_bp.route('/api/xp-progress')
@login_required
def xp_progress():
    """Get XP progress data for charts"""
    # Get XP transactions for the last 30 days
    transactions = XPTransaction.query.filter_by(
        user_id=current_user.id
    ).filter(
        XPTransaction.created_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(XPTransaction.created_at).all()
    
    # Group by day
    daily_xp = {}
    for transaction in transactions:
        date_key = transaction.created_at.date().isoformat()
        if date_key not in daily_xp:
            daily_xp[date_key] = 0
        daily_xp[date_key] += transaction.amount
    
    return jsonify({
        'daily_xp': daily_xp,
        'total_xp': current_user.total_xp,
        'current_level': current_user.level_info.current_level if current_user.level_info else 1
    })


@gamification_bp.route('/api/check-achievements', methods=['POST'])
@login_required
def check_achievements():
    """Check for new achievements"""
    context = request.json
    new_achievements = GamificationService.check_achievements(current_user, context)
    
    return jsonify({
        'new_achievements': [
            {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'points': achievement.points,
                'icon': achievement.icon_filename
            }
            for achievement in new_achievements
        ]
    })


@gamification_bp.route('/api/level-info')
@login_required
def get_level_info():
    """Get current user level and XP info for real-time updates"""
    
    # Single source of truth: user.total_xp
    total_xp = current_user.total_xp or 0
    
    # Calculate everything dynamically
    current_level = GamificationService.calculate_level_from_xp(total_xp)
    xp_for_current_level = GamificationService.calculate_total_xp_for_level(current_level)
    xp_for_next_level = GamificationService.calculate_total_xp_for_level(current_level + 1)
    
    # Progress within current level
    current_xp = total_xp - xp_for_current_level
    next_level_xp = xp_for_next_level - xp_for_current_level
    
    # Progress percentage
    progress_percentage = int((current_xp / next_level_xp) * 100) if next_level_xp > 0 else 0
    
    return jsonify({
        'current_level': current_level,
        'current_xp': current_xp,
        'next_level_xp': next_level_xp,
        'total_xp': total_xp,
        'progress_percentage': progress_percentage
    })


@gamification_bp.route('/api/calculate-xp')
@login_required 
def calculate_xp():
    """Calculate XP for given parameters (for testing/preview)"""
    correct_answers = request.args.get('correct', type=int, default=0)
    total_questions = request.args.get('total', type=int, default=1)
    score = request.args.get('score', type=int, default=0)
    
    calculation = GamificationService.calculate_quiz_xp(correct_answers, total_questions, score)
    
    return jsonify({
        'total_xp': calculation['total_xp'],
        'breakdown': calculation['breakdown'],
        'example_url': f'/gamification/api/calculate-xp?correct=5&total=5&score=100'
    })
