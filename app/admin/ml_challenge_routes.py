# app/admin/ml_challenge_routes.py
"""
Admin routes for managing ML-driven daily challenges.
Provides oversight and configuration for automated challenge generation.
"""
from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from . import admin_bp
from ..gamification.ml_challenge_service import ml_challenge_service
from ..gamification.challenge_types import ChallengeType, CategoryRegistry
from ..gamification_models import DailyChallenge, UserDailyChallenge
from ..models import User
from .. import db
import logging

logger = logging.getLogger(__name__)


@admin_bp.route('/api/ml-challenges/overview', methods=['GET'])
@login_required
def get_ml_challenges_overview():
    """Get overview statistics for ML challenge system"""
    try:
        # Get performance stats for last 30 days
        performance_stats = ml_challenge_service.get_challenge_performance_stats(days=30)
        
        # Get ML service status
        ml_status = ml_challenge_service.ml_service.get_ml_status() if hasattr(ml_challenge_service.ml_service, 'get_ml_status') else {}
        
        # Get recent challenge generation activity
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        recent_challenges = DailyChallenge.query.filter(
            DailyChallenge.date >= week_ago,
            DailyChallenge.date <= today
        ).order_by(DailyChallenge.date.desc()).limit(20).all()
        
        # Categorize challenges
        ml_challenges = [c for c in recent_challenges if c.title.startswith('[ML]')]
        manual_challenges = [c for c in recent_challenges if not c.title.startswith('[ML]')]
        
        return jsonify({
            'success': True,
            'overview': {
                'total_challenges_week': len(recent_challenges),
                'ml_generated_week': len(ml_challenges),
                'manual_created_week': len(manual_challenges),
                'ml_enabled': ml_challenge_service.ml_service.is_ml_enabled(),
                'performance_stats': performance_stats,
                'ml_status': ml_status
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ML challenges overview: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/ml-challenges/generate', methods=['POST'])
@login_required
def generate_ml_challenges():
    """Manually trigger ML challenge generation for today"""
    try:
        data = request.get_json() or {}
        target_date = data.get('target_date')
        
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Generate challenges for all users
        results = ml_challenge_service.generate_daily_challenges_for_all_users(target_date)
        
        # Log admin action
        from ..security.admin_security import AdminSecurityService
        AdminSecurityService.log_admin_action(
            current_user,
            f"Manually triggered ML challenge generation for {target_date}: {results}"
        )
        
        return jsonify({
            'success': True,
            'message': f'Generated challenges for {target_date}',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error generating ML challenges: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/ml-challenges/performance', methods=['GET'])
@login_required
def get_ml_challenge_performance():
    """Get detailed performance analytics for ML challenges"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get performance stats
        performance_stats = ml_challenge_service.get_challenge_performance_stats(days)
        
        # Get completion rates by challenge type
        start_date = date.today() - timedelta(days=days)
        
        challenges = DailyChallenge.query.filter(
            DailyChallenge.date >= start_date,
            DailyChallenge.is_active == True
        ).all()
        
        # Group by challenge type and ML vs manual
        type_stats = {}
        
        for challenge in challenges:
            is_ml = challenge.title.startswith('[ML]')
            challenge_type = challenge.challenge_type
            
            key = f"{challenge_type}_{'ml' if is_ml else 'manual'}"
            
            if key not in type_stats:
                type_stats[key] = {
                    'total_assigned': 0,
                    'total_completed': 0,
                    'completion_rate': 0
                }
            
            # Count user assignments
            user_challenges = UserDailyChallenge.query.filter_by(
                challenge_id=challenge.id
            ).all()
            
            completed = len([uc for uc in user_challenges if uc.completed])
            
            type_stats[key]['total_assigned'] += len(user_challenges)
            type_stats[key]['total_completed'] += completed
            
            if type_stats[key]['total_assigned'] > 0:
                type_stats[key]['completion_rate'] = type_stats[key]['total_completed'] / type_stats[key]['total_assigned']
        
        return jsonify({
            'success': True,
            'performance': {
                'overview': performance_stats,
                'by_type': type_stats,
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ML challenge performance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/ml-challenges/settings', methods=['GET', 'POST'])
@login_required
def ml_challenge_settings():
    """Get or update ML challenge generation settings"""
    try:
        if request.method == 'GET':
            # Get current settings
            settings = {
                'ml_enabled': ml_challenge_service.ml_service.is_ml_enabled(),
                'fallback_enabled': True,  # Always available
                'auto_generation_enabled': True,  # TODO: Add to settings
                'challenge_types_enabled': {
                    'quiz': True,
                    'perfect_score': True,
                    'category_focus': True,
                    'streak': True,
                    'speed_challenge': False,  # TODO: Add implementation
                    'accuracy_challenge': True
                },
                'categories_enabled': {cat: True for cat in CategoryRegistry.get_all_categories()},
                'difficulty_range': {'min': 0.2, 'max': 0.9},
                'xp_multiplier': 1.0  # TODO: Add to settings
            }
            
            return jsonify({
                'success': True,
                'settings': settings
            })
            
        else:  # POST
            data = request.get_json()
            
            # Update settings (simplified for now)
            # TODO: Implement proper settings persistence
            
            # Log admin action
            from ..security.admin_security import AdminSecurityService
            AdminSecurityService.log_admin_action(
                current_user,
                f"Updated ML challenge settings: {data}"
            )
            
            return jsonify({
                'success': True,
                'message': 'Settings updated successfully'
            })
            
    except Exception as e:
        logger.error(f"Error handling ML challenge settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/ml-challenges/test-user/<int:user_id>', methods=['POST'])
@login_required
def test_ml_challenge_for_user(user_id):
    """Test ML challenge generation for a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Generate test challenge (don't save to database)
        challenge_config = ml_challenge_service.generate_personalized_challenge(
            user_id=user_id,
            target_date=date.today()
        )
        
        if challenge_config:
            # Get user's ML analysis for context
            weak_areas = ml_challenge_service.ml_service.get_weak_areas(user_id)
            skill_assessment = ml_challenge_service.ml_service.get_skill_assessment(user_id)
            
            result = {
                'challenge_generated': True,
                'challenge': {
                    'title': challenge_config.title,
                    'description': challenge_config.description,
                    'type': challenge_config.challenge_type,
                    'requirement': challenge_config.requirement_value,
                    'xp_reward': challenge_config.xp_reward,
                    'bonus_reward': challenge_config.bonus_reward,
                    'category': challenge_config.category,
                    'difficulty': challenge_config.difficulty_level\n                },\n                'user_analysis': {\n                    'weak_areas': weak_areas,\n                    'skill_level': skill_assessment.get('overall_skill_level', 0.5),\n                    'confidence': skill_assessment.get('confidence_level', 0.5),\n                    'total_questions': skill_assessment.get('total_practice_questions', 0)\n                }\n            }\n        else:\n            result = {\n                'challenge_generated': False,\n                'reason': 'Could not generate challenge for this user'\n            }\n        \n        # Log admin action\n        from ..security.admin_security import AdminSecurityService\n        AdminSecurityService.log_admin_action(\n            current_user,\n            f\"Tested ML challenge generation for user {user.username} ({user_id})\"\n        )\n        \n        return jsonify({\n            'success': True,\n            'user': {\n                'id': user.id,\n                'username': user.username,\n                'total_xp': user.total_xp\n            },\n            'result': result\n        })\n        \n    except Exception as e:\n        logger.error(f\"Error testing ML challenge for user {user_id}: {e}\")\n        return jsonify({'success': False, 'message': str(e)}), 500\n\n\n@admin_bp.route('/api/ml-challenges/categories', methods=['GET'])\n@login_required\ndef get_challenge_categories():\n    \"\"\"Get available challenge categories with Norwegian names\"\"\"\n    try:\n        categories = []\n        \n        for category_key in CategoryRegistry.get_all_categories():\n            categories.append({\n                'key': category_key,\n                'name': CategoryRegistry.get_category_name(category_key),\n                'description': CategoryRegistry.get_category_description(category_key),\n                'difficulty_weight': CategoryRegistry.get_difficulty_weight(category_key)\n            })\n        \n        return jsonify({\n            'success': True,\n            'categories': categories\n        })\n        \n    except Exception as e:\n        logger.error(f\"Error getting challenge categories: {e}\")\n        return jsonify({'success': False, 'message': str(e)}), 500\n\n\n@admin_bp.route('/api/ml-challenges/types', methods=['GET'])\n@login_required\ndef get_challenge_types():\n    \"\"\"Get available challenge types with configurations\"\"\"\n    try:\n        from ..gamification.challenge_types import ChallengeTypeRegistry\n        \n        types = []\n        \n        for challenge_type in ChallengeType:\n            config = ChallengeTypeRegistry.get_config(challenge_type)\n            types.append({\n                'key': challenge_type.value,\n                'name': config.name,\n                'description': config.description,\n                'base_xp': config.base_xp,\n                'scaling_factor': config.scaling_factor,\n                'requirement_range': config.requirement_range,\n                'category_specific': config.category_specific,\n                'ml_weight': config.ml_weight\n            })\n        \n        return jsonify({\n            'success': True,\n            'challenge_types': types\n        })\n        \n    except Exception as e:\n        logger.error(f\"Error getting challenge types: {e}\")\n        return jsonify({'success': False, 'message': str(e)}), 500\n\n\n@admin_bp.route('/api/ml-challenges/recent', methods=['GET'])\n@login_required\ndef get_recent_ml_challenges():\n    \"\"\"Get recent ML-generated challenges\"\"\"\n    try:\n        days = request.args.get('days', 7, type=int)\n        limit = request.args.get('limit', 50, type=int)\n        \n        start_date = date.today() - timedelta(days=days)\n        \n        challenges = DailyChallenge.query.filter(\n            DailyChallenge.date >= start_date,\n            DailyChallenge.title.like('[ML]%')\n        ).order_by(DailyChallenge.date.desc(), DailyChallenge.id.desc()).limit(limit).all()\n        \n        challenge_data = []\n        \n        for challenge in challenges:\n            # Get completion stats\n            user_challenges = UserDailyChallenge.query.filter_by(\n                challenge_id=challenge.id\n            ).all()\n            \n            total_assigned = len(user_challenges)\n            completed = len([uc for uc in user_challenges if uc.completed])\n            completion_rate = completed / total_assigned if total_assigned > 0 else 0\n            \n            challenge_data.append({\n                'id': challenge.id,\n                'title': challenge.title,\n                'description': challenge.description,\n                'type': challenge.challenge_type,\n                'category': challenge.category,\n                'requirement_value': challenge.requirement_value,\n                'xp_reward': challenge.xp_reward,\n                'bonus_reward': challenge.bonus_reward,\n                'date': challenge.date.isoformat(),\n                'is_active': challenge.is_active,\n                'stats': {\n                    'total_assigned': total_assigned,\n                    'completed': completed,\n                    'completion_rate': completion_rate\n                }\n            })\n        \n        return jsonify({\n            'success': True,\n            'challenges': challenge_data,\n            'total_found': len(challenge_data),\n            'period_days': days\n        })\n        \n    except Exception as e:\n        logger.error(f\"Error getting recent ML challenges: {e}\")\n        return jsonify({'success': False, 'message': str(e)}), 500\n\n\n@admin_bp.route('/api/ml-challenges/stats', methods=['GET'])\n@login_required\ndef get_ml_challenge_stats():\n    \"\"\"Get comprehensive ML challenge statistics\"\"\"\n    try:\n        # Basic counts\n        total_ml_challenges = DailyChallenge.query.filter(\n            DailyChallenge.title.like('[ML]%')\n        ).count()\n        \n        total_manual_challenges = DailyChallenge.query.filter(\n            ~DailyChallenge.title.like('[ML]%')\n        ).count()\n        \n        # Active users with ML data\n        users_with_ml_data = 0\n        try:\n            from ..ml.models import UserSkillProfile\n            users_with_ml_data = UserSkillProfile.query.with_entities(\n                UserSkillProfile.user_id\n            ).distinct().count()\n        except Exception:\n            pass\n        \n        # Today's generation status\n        today = date.today()\n        today_challenges = DailyChallenge.query.filter_by(\n            date=today,\n            is_active=True\n        ).all()\n        \n        today_ml = len([c for c in today_challenges if c.title.startswith('[ML]')])\n        today_manual = len([c for c in today_challenges if not c.title.startswith('[ML]')])\n        \n        return jsonify({\n            'success': True,\n            'stats': {\n                'total_ml_challenges': total_ml_challenges,\n                'total_manual_challenges': total_manual_challenges,\n                'users_with_ml_data': users_with_ml_data,\n                'total_active_users': User.query.filter_by(is_active=True).count(),\n                'today_ml_challenges': today_ml,\n                'today_manual_challenges': today_manual,\n                'ml_system_status': {\n                    'enabled': ml_challenge_service.ml_service.is_ml_enabled(),\n                    'service_initialized': hasattr(ml_challenge_service.ml_service, '_initialized') and ml_challenge_service.ml_service._initialized\n                }\n            }\n        })\n        \n    except Exception as e:\n        logger.error(f\"Error getting ML challenge stats: {e}\")\n        return jsonify({'success': False, 'message': str(e)}), 500\n