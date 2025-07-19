#!/usr/bin/env python3
"""
Initialize XP rewards table with recommended values
Run this script to populate the xp_rewards table with optimal scaling factors
"""

from app import create_app, db
from app.gamification_models import XPReward

def init_xp_rewards():
    """Initialize XP rewards table with recommended values"""
    
    xp_rewards_data = [
        # Basic Quiz Rewards
        {
            'reward_type': 'question_correct',
            'base_value': 2,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'XP per correct answer (fixed rate)'
        },
        {
            'reward_type': 'quiz_complete',
            'base_value': 5,
            'scaling_factor': 0.5,
            'max_value': 50,
            'description': 'Quiz completion bonus: base + (questions * 0.5)'
        },
        {
            'reward_type': 'quiz_perfect',
            'base_value': 0,
            'scaling_factor': 1.5,
            'max_value': 100,
            'description': 'Perfect score bonus: questions * 1.5'
        },
        
        # Streak Rewards
        {
            'reward_type': 'question_streak_5',
            'base_value': 5,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': '5 consecutive correct answers'
        },
        {
            'reward_type': 'question_streak_10',
            'base_value': 15,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': '10 consecutive correct answers'
        },
        
        # Daily Activities
        {
            'reward_type': 'daily_login',
            'base_value': 5,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Daily login bonus'
        },
        {
            'reward_type': 'daily_challenge',
            'base_value': 25,
            'scaling_factor': 1.0,
            'max_value': 75,
            'description': 'Daily challenge completion'
        },
        
        # Video & Learning
        {
            'reward_type': 'video_complete',
            'base_value': 0,
            'scaling_factor': 2.0,
            'max_value': 30,
            'description': 'Video completion: duration_minutes * 2'
        },
        {
            'reward_type': 'learning_path_complete',
            'base_value': 100,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Complete learning module'
        },
        
        # Tournaments & Social
        {
            'reward_type': 'tournament_participation',
            'base_value': 20,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Tournament participation'
        },
        {
            'reward_type': 'tournament_top3',
            'base_value': 100,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Tournament top 3 finish'
        },
        {
            'reward_type': 'tournament_win',
            'base_value': 250,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Tournament victory'
        },
        {
            'reward_type': 'friend_challenge_win',
            'base_value': 30,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Win friend challenge'
        },
        
        # Achievement unlock (variable based on achievement itself)
        {
            'reward_type': 'achievement_unlock',
            'base_value': 0,
            'scaling_factor': 1.0,
            'max_value': None,
            'description': 'Achievement unlock (XP defined per achievement)'
        }
    ]
    
    print("Initializing XP rewards table...")
    
    for reward_data in xp_rewards_data:
        # Check if reward already exists
        existing = XPReward.query.filter_by(reward_type=reward_data['reward_type']).first()
        
        if existing:
            print(f"Updating existing reward: {reward_data['reward_type']}")
            existing.base_value = reward_data['base_value']
            existing.scaling_factor = reward_data['scaling_factor']
            existing.max_value = reward_data['max_value']
            existing.description = reward_data['description']
        else:
            print(f"Creating new reward: {reward_data['reward_type']}")
            new_reward = XPReward(**reward_data)
            db.session.add(new_reward)
    
    try:
        db.session.commit()
        print("✅ XP rewards table initialized successfully!")
        
        # Display the rewards
        print("\n📊 Current XP Rewards Configuration:")
        print("-" * 60)
        all_rewards = XPReward.query.order_by(XPReward.reward_type).all()
        for reward in all_rewards:
            max_val = f" (max: {reward.max_value})" if reward.max_value else ""
            print(f"{reward.reward_type:25} | {reward.base_value:3}xp × {reward.scaling_factor}{max_val}")
        
        print("\n🎯 Example XP Calculations:")
        print("-" * 40)
        print("5-question perfect quiz:")
        print(f"  • Correct answers: 5 × 2 = 10 XP")
        print(f"  • Completion: 5 + (5 × 0.5) = 8 XP") 
        print(f"  • Perfect bonus: 5 × 1.5 = 8 XP")
        print(f"  • Total: 26 XP")
        print()
        print("20-question perfect quiz:")
        print(f"  • Correct answers: 20 × 2 = 40 XP")
        print(f"  • Completion: 5 + (20 × 0.5) = 15 XP")
        print(f"  • Perfect bonus: 20 × 1.5 = 30 XP") 
        print(f"  • Total: 85 XP")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error initializing XP rewards: {e}")
        return False
    
    return True

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        init_xp_rewards()
