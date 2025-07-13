# app/gamification/quiz_integration.py
"""
Integration between quiz system and gamification
"""
from app.gamification.services import GamificationService
from app.models import QuizSession, User
from datetime import datetime


def process_quiz_completion(user, quiz_session):
    """
    Process gamification rewards after quiz completion
    
    Args:
        user: User instance
        quiz_session: Completed QuizSession instance
    
    Returns:
        dict: Information about rewards earned
    """
    rewards = {
        'xp_earned': 0,
        'achievements': [],
        'level_ups': [],
        'daily_challenges': []
    }
    
    question_count = quiz_session.total_questions
    
    # Base XP for completing a quiz (scaled by question count)
    base_xp = GamificationService.get_xp_reward('quiz_complete', question_count=question_count)
    rewards['xp_earned'] += base_xp
    
    # XP for correct answers
    correct_xp = quiz_session.correct_answers * GamificationService.get_xp_reward('question_correct')
    rewards['xp_earned'] += correct_xp
    
    # Perfect score bonus (scaled by question count)
    if quiz_session.score == 100:
        perfect_xp = GamificationService.get_xp_reward('quiz_perfect', question_count=question_count)
        rewards['xp_earned'] += perfect_xp
    
    # Award XP
    level_ups = GamificationService.award_xp(
        user,
        rewards['xp_earned'],
        'quiz',
        f'Fullførte quiz: {quiz_session.correct_answers}/{quiz_session.total_questions} riktige'
    )
    rewards['level_ups'] = level_ups
    
    # Update daily challenges
    completed_challenges = GamificationService.update_daily_challenge_progress(
        user,
        'quiz',
        1,
        quiz_session.category
    )
    rewards['daily_challenges'].extend(completed_challenges)
    
    # Check for perfect score challenges
    if quiz_session.score == 100:
        perfect_challenges = GamificationService.update_daily_challenge_progress(
            user,
            'perfect_score',
            1
        )
        rewards['daily_challenges'].extend(perfect_challenges)
    
    # Check and update streak
    GamificationService.check_and_update_streak(user)
    
    # Check for achievements
    context = {
        'quiz_time': quiz_session.time_spent_seconds,
        'category': quiz_session.category,
        'score': quiz_session.score
    }
    
    new_achievements = GamificationService.check_achievements(user, context)
    rewards['achievements'] = new_achievements
    
    # Update tournament scores if user is participating
    from app.gamification_models import WeeklyTournament, TournamentParticipant
    active_tournaments = TournamentParticipant.query.filter_by(
        user_id=user.id
    ).join(WeeklyTournament).filter(
        WeeklyTournament.is_active == True,
        WeeklyTournament.start_date <= datetime.utcnow(),
        WeeklyTournament.end_date >= datetime.utcnow()
    ).all()
    
    for participant in active_tournaments:
        tournament = participant.tournament
        
        # Calculate tournament score based on quiz performance
        tournament_score = 0
        if tournament.tournament_type == 'accuracy':
            tournament_score = int(quiz_session.score)
        elif tournament.tournament_type == 'speed':
            # Faster completion = higher score
            if quiz_session.time_spent_seconds > 0:
                tournament_score = int(10000 / quiz_session.time_spent_seconds)
        elif tournament.tournament_type == 'marathon':
            # Points for each quiz completed
            tournament_score = 10 + (quiz_session.correct_answers * 2)
        else:  # default
            tournament_score = int(quiz_session.score * 0.5 + (quiz_session.correct_answers * 5))
        
        # Update tournament score
        GamificationService.update_tournament_score(user, tournament.id, tournament_score)
    
    return rewards


def get_active_powerups(user):
    """
    Get user's active power-ups for quiz
    
    Args:
        user: User instance
    
    Returns:
        dict: Active power-ups and their effects
    """
    from app.gamification_models import UserPowerUp
    from datetime import datetime
    
    active_powerups = {
        'double_xp': False,
        'xp_boost': False,
        'time_extend': False,
        'second_chance': False,
        'hint_available': 0
    }
    
    # Get user's active power-ups
    user_powerups = UserPowerUp.query.filter_by(
        user_id=user.id,
        used_at=None
    ).all()
    
    for powerup in user_powerups:
        if powerup.powerup.effect_type == 'hint':
            active_powerups['hint_available'] += powerup.quantity
        elif powerup.powerup.effect_type == 'time_extend':
            active_powerups['time_extend'] = True
        elif powerup.powerup.effect_type == 'second_chance':
            active_powerups['second_chance'] = True
    
    # Check for active timed power-ups
    active_timed = UserPowerUp.query.filter_by(
        user_id=user.id
    ).filter(
        UserPowerUp.used_at != None,
        UserPowerUp.expires_at > datetime.utcnow()
    ).all()
    
    for powerup in active_timed:
        if powerup.powerup.effect_type == 'double_xp':
            active_powerups['double_xp'] = True
        elif powerup.powerup.effect_type == 'xp_boost':
            active_powerups['xp_boost'] = True
    
    return active_powerups


def use_powerup(user, powerup_type):
    """
    Use a power-up
    
    Args:
        user: User instance
        powerup_type: Type of power-up to use
    
    Returns:
        bool: Success status
    """
    from app.gamification_models import UserPowerUp, PowerUp
    from app import db
    from datetime import datetime, timedelta
    
    # Find user's power-up
    user_powerup = UserPowerUp.query.join(PowerUp).filter(
        UserPowerUp.user_id == user.id,
        PowerUp.effect_type == powerup_type,
        UserPowerUp.used_at == None
    ).first()
    
    if not user_powerup:
        return False
    
    # Mark as used
    user_powerup.used_at = datetime.utcnow()
    
    # Set expiration for timed power-ups
    if user_powerup.powerup.effect_duration > 0:
        user_powerup.expires_at = datetime.utcnow() + timedelta(
            minutes=user_powerup.powerup.effect_duration
        )
    
    # Reduce quantity
    user_powerup.quantity -= 1
    if user_powerup.quantity <= 0:
        db.session.delete(user_powerup)
    
    db.session.commit()
    return True
