# scripts/seed_gamification.py
"""
Seed initial gamification data (achievements, power-ups, etc.)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Achievement
from app.gamification_models import PowerUp, StreakReward, DailyChallenge
from datetime import date

def seed_achievements():
    """Create initial achievements"""
    achievements = [
        # Quiz-based achievements
        {
            'name': 'Første skritt',
            'description': 'Fullfør din første quiz',
            'category': 'Quiz',
            'points': 10,
            'requirement_type': 'quiz_count',
            'requirement_value': 1
        },
        {
            'name': 'Quiz-entusiast',
            'description': 'Fullfør 10 quizer',
            'category': 'Quiz',
            'points': 25,
            'requirement_type': 'quiz_count',
            'requirement_value': 10
        },
        {
            'name': 'Quiz-mester',
            'description': 'Fullfør 50 quizer',
            'category': 'Quiz',
            'points': 50,
            'requirement_type': 'quiz_count',
            'requirement_value': 50
        },
        {
            'name': 'Quiz-legende',
            'description': 'Fullfør 100 quizer',
            'category': 'Quiz',
            'points': 100,
            'requirement_type': 'quiz_count',
            'requirement_value': 100
        },
        
        # Perfect score achievements
        {
            'name': 'Perfeksjonist',
            'description': 'Få 100% på en quiz',
            'category': 'Perfekt score',
            'points': 20,
            'requirement_type': 'perfect_quiz',
            'requirement_value': 1
        },
        {
            'name': 'Feilfri',
            'description': 'Få 100% på 5 quizer',
            'category': 'Perfekt score',
            'points': 50,
            'requirement_type': 'perfect_quiz',
            'requirement_value': 5
        },
        {
            'name': 'Geni',
            'description': 'Få 100% på 20 quizer',
            'category': 'Perfekt score',
            'points': 100,
            'requirement_type': 'perfect_quiz',
            'requirement_value': 20
        },
        
        # Streak achievements
        {
            'name': 'Konsistent',
            'description': 'Hold en 3-dagers streak',
            'category': 'Streak',
            'points': 15,
            'requirement_type': 'streak_days',
            'requirement_value': 3
        },
        {
            'name': 'Dedikert',
            'description': 'Hold en 7-dagers streak',
            'category': 'Streak',
            'points': 30,
            'requirement_type': 'streak_days',
            'requirement_value': 7
        },
        {
            'name': 'Ustoppelig',
            'description': 'Hold en 30-dagers streak',
            'category': 'Streak',
            'points': 100,
            'requirement_type': 'streak_days',
            'requirement_value': 30
        },
        {
            'name': 'Streak-legende',
            'description': 'Hold en 100-dagers streak',
            'category': 'Streak',
            'points': 250,
            'requirement_type': 'streak_days',
            'requirement_value': 100
        },
        
        # Question count achievements
        {
            'name': 'Nysgjerrig',
            'description': 'Besvar 50 spørsmål',
            'category': 'Spørsmål',
            'points': 15,
            'requirement_type': 'total_questions',
            'requirement_value': 50
        },
        {
            'name': 'Kunnskapssøker',
            'description': 'Besvar 500 spørsmål',
            'category': 'Spørsmål',
            'points': 50,
            'requirement_type': 'total_questions',
            'requirement_value': 500
        },
        {
            'name': 'Encyklopedi',
            'description': 'Besvar 2000 spørsmål',
            'category': 'Spørsmål',
            'points': 150,
            'requirement_type': 'total_questions',
            'requirement_value': 2000
        },
        
        # Accuracy achievements
        {
            'name': 'Skarpskytter',
            'description': 'Oppnå 80% nøyaktighet (min 50 spørsmål)',
            'category': 'Nøyaktighet',
            'points': 40,
            'requirement_type': 'accuracy',
            'requirement_value': 80
        },
        {
            'name': 'Presisjon',
            'description': 'Oppnå 90% nøyaktighet (min 50 spørsmål)',
            'category': 'Nøyaktighet',
            'points': 80,
            'requirement_type': 'accuracy',
            'requirement_value': 90
        },
        {
            'name': 'Laser-fokus',
            'description': 'Oppnå 95% nøyaktighet (min 50 spørsmål)',
            'category': 'Nøyaktighet',
            'points': 150,
            'requirement_type': 'accuracy',
            'requirement_value': 95
        },
        
        # Level achievements
        {
            'name': 'Nivå 5',
            'description': 'Nå nivå 5',
            'category': 'Nivå',
            'points': 25,
            'requirement_type': 'level',
            'requirement_value': 5
        },
        {
            'name': 'Nivå 10',
            'description': 'Nå nivå 10',
            'category': 'Nivå',
            'points': 50,
            'requirement_type': 'level',
            'requirement_value': 10
        },
        {
            'name': 'Nivå 25',
            'description': 'Nå nivå 25',
            'category': 'Nivå',
            'points': 100,
            'requirement_type': 'level',
            'requirement_value': 25
        },
        {
            'name': 'Nivå 50',
            'description': 'Nå nivå 50',
            'category': 'Nivå',
            'points': 200,
            'requirement_type': 'level',
            'requirement_value': 50
        },
        
        # Speed achievements
        {
            'name': 'Lynrask',
            'description': 'Fullfør en 20-spørsmåls quiz på under 5 minutter',
            'category': 'Hastighet',
            'points': 30,
            'requirement_type': 'speed_demon',
            'requirement_value': 300  # 5 minutes in seconds
        },
        {
            'name': 'Turbo',
            'description': 'Fullfør en 20-spørsmåls quiz på under 3 minutter',
            'category': 'Hastighet',
            'points': 60,
            'requirement_type': 'speed_demon',
            'requirement_value': 180  # 3 minutes in seconds
        },
        
        # Category mastery
        {
            'name': 'Skilt-ekspert',
            'description': 'Få over 90% på 10 trafikkskilt-quizer',
            'category': 'Mestring',
            'points': 50,
            'requirement_type': 'category_master',
            'requirement_value': 10
        },
        {
            'name': 'Regel-guru',
            'description': 'Få over 90% på 10 trafikkregler-quizer',
            'category': 'Mestring',
            'points': 50,
            'requirement_type': 'category_master',
            'requirement_value': 10
        },
    ]
    
    for achievement_data in achievements:
        achievement = Achievement.query.filter_by(name=achievement_data['name']).first()
        if not achievement:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    
    db.session.commit()
    print(f"Created {len(achievements)} achievements")


def seed_power_ups():
    """Create initial power-ups"""
    power_ups = [
        {
            'name': 'Dobbel XP',
            'description': 'Få dobbelt så mye XP i 30 minutter',
            'icon': 'double-xp',
            'cost_xp': 200,
            'effect_type': 'double_xp',
            'effect_duration': 30
        },
        {
            'name': 'Streak Freeze',
            'description': 'Behold din streak selv om du går glipp av en dag',
            'icon': 'freeze',
            'cost_xp': 150,
            'effect_type': 'streak_freeze',
            'effect_duration': 0
        },
        {
            'name': 'Hint',
            'description': 'Få et hint på et vanskelig spørsmål',
            'icon': 'hint',
            'cost_xp': 50,
            'effect_type': 'hint',
            'effect_duration': 0
        },
        {
            'name': 'Tidsforlenger',
            'description': 'Få 50% mer tid på neste quiz',
            'icon': 'time',
            'cost_xp': 100,
            'effect_type': 'time_extend',
            'effect_duration': 0
        },
        {
            'name': 'Andre sjanse',
            'description': 'Få mulighet til å svare på nytt hvis du svarer feil',
            'icon': 'retry',
            'cost_xp': 75,
            'effect_type': 'second_chance',
            'effect_duration': 0
        },
        {
            'name': 'XP Boost',
            'description': 'Få 50% mer XP i 1 time',
            'icon': 'boost',
            'cost_xp': 100,
            'effect_type': 'xp_boost',
            'effect_duration': 60
        }
    ]
    
    for power_up_data in power_ups:
        power_up = PowerUp.query.filter_by(name=power_up_data['name']).first()
        if not power_up:
            power_up = PowerUp(**power_up_data)
            db.session.add(power_up)
    
    db.session.commit()
    print(f"Created {len(power_ups)} power-ups")


def seed_streak_rewards():
    """Create streak milestone rewards"""
    # First, get streak achievements
    streak_achievements = Achievement.query.filter_by(requirement_type='streak_days').all()
    achievement_map = {a.requirement_value: a.id for a in streak_achievements}
    
    streak_rewards = [
        {
            'streak_days': 3,
            'reward_name': '3-dagers streak',
            'xp_bonus': 50,
            'badge_id': achievement_map.get(3),
            'description': 'Gratulerer med 3 dager på rad!'
        },
        {
            'streak_days': 7,
            'reward_name': 'Ukentlig streak',
            'xp_bonus': 100,
            'badge_id': achievement_map.get(7),
            'description': 'En hel uke med øving!'
        },
        {
            'streak_days': 14,
            'reward_name': 'To-ukers streak',
            'xp_bonus': 200,
            'description': 'To uker med dedikert øving!'
        },
        {
            'streak_days': 30,
            'reward_name': 'Månedlig streak',
            'xp_bonus': 500,
            'badge_id': achievement_map.get(30),
            'description': 'En hel måned med daglig øving!'
        },
        {
            'streak_days': 50,
            'reward_name': '50-dagers streak',
            'xp_bonus': 750,
            'description': 'Halvveis til 100!'
        },
        {
            'streak_days': 100,
            'reward_name': 'Århundre streak',
            'xp_bonus': 1500,
            'badge_id': achievement_map.get(100),
            'description': '100 dager med ren dedikasjon!'
        }
    ]
    
    for reward_data in streak_rewards:
        reward = StreakReward.query.filter_by(streak_days=reward_data['streak_days']).first()
        if not reward:
            reward = StreakReward(**reward_data)
            db.session.add(reward)
    
    db.session.commit()
    print(f"Created {len(streak_rewards)} streak rewards")


def seed_daily_challenges():
    """Create some sample daily challenges for today"""
    challenges = [
        {
            'title': 'Quiz-mester',
            'description': 'Fullfør 3 quizer i dag',
            'challenge_type': 'quiz',
            'requirement_value': 3,
            'xp_reward': 50,
            'date': date.today()
        },
        {
            'title': 'Perfeksjonist',
            'description': 'Få 100% på en quiz',
            'challenge_type': 'perfect_score',
            'requirement_value': 1,
            'xp_reward': 75,
            'date': date.today()
        },
        {
            'title': 'Trafikkskilt-fokus',
            'description': 'Ta 2 trafikkskilt-quizer',
            'challenge_type': 'quiz',
            'requirement_value': 2,
            'xp_reward': 60,
            'category': 'Trafikkskilt',
            'date': date.today()
        }
    ]
    
    for challenge_data in challenges:
        challenge = DailyChallenge.query.filter_by(
            title=challenge_data['title'],
            date=challenge_data['date']
        ).first()
        if not challenge:
            challenge = DailyChallenge(**challenge_data)
            db.session.add(challenge)
    
    db.session.commit()
    print(f"Created {len(challenges)} daily challenges")


def main():
    """Main function to seed all gamification data"""
    app = create_app()
    
    with app.app_context():
        print("Seeding gamification data...")
        
        seed_achievements()
        seed_power_ups()
        seed_streak_rewards()
        seed_daily_challenges()
        
        print("Gamification data seeded successfully!")


if __name__ == "__main__":
    main()
