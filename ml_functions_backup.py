

# ========================================
# ML CONTEXT AND API FUNCTIONS
# ========================================

def get_ml_context():
    """Get ML context data for admin dashboard"""
    try:
        # Try to import ML modules
        try:
            from ..ml.service import ml_service
            from ..ml.models import UserSkillProfile, QuestionDifficultyProfile, AdaptiveQuizSession, LearningAnalytics, MLModel
            ml_available = True
        except ImportError:
            ml_available = False
        
        if not ml_available:
            # Return fallback data when ML is not available
            return {
                'ml_status': {
                    'ml_enabled': False,
                    'algorithm_version': '1.0',
                    'error': 'ML modules not available'
                },
                'ml_stats': {
                    'total_users': User.query.count(),
                    'active_profiles': 0,
                    'adaptive_sessions': 0
                },
                'ml_config': {
                    'learning_rate': 0.05,
                    'adaptation_strength': 0.5,
                    'collect_response_times': True,
                    'track_confidence': True,
                    'analyze_patterns': True,
                    'update_frequency': 'daily'
                },
                'skill_distribution': {},
                'top_categories': [],
                'problem_areas': [],
                'model_performance': {},
                'recent_ml_activity': []
            }
        
        # Get ML status
        ml_status = {
            'ml_enabled': ml_service.is_ml_enabled() if ml_available else False,
            'algorithm_version': '2.1',
            'error': None
        }
        
        # Get ML statistics
        total_users = User.query.count()
        active_profiles = UserSkillProfile.query.distinct(UserSkillProfile.user_id).count() if ml_available else 0
        adaptive_sessions = AdaptiveQuizSession.query.count() if ml_available else 0
        
        ml_stats = {
            'total_users': total_users,
            'active_profiles': active_profiles,
            'adaptive_sessions': adaptive_sessions
        }
        
        # Mock configuration (in a real system, this would come from database)
        ml_config = {
            'learning_rate': 0.05,
            'adaptation_strength': 0.5,
            'collect_response_times': True,
            'track_confidence': True,
            'analyze_patterns': True,
            'update_frequency': 'daily'
        }
        
        # Get skill distribution
        skill_distribution = {}
        if ml_available and active_profiles > 0:
            try:
                # Get skill levels based on accuracy scores
                skill_data = db.session.query(
                    db.func.case(
                        (UserSkillProfile.accuracy_score >= 0.8, 'Expert'),
                        (UserSkillProfile.accuracy_score >= 0.6, 'Advanced'),
                        (UserSkillProfile.accuracy_score >= 0.4, 'Intermediate'),
                        else_='Beginner'
                    ).label('skill_level'),
                    db.func.count(UserSkillProfile.user_id.distinct()).label('count')
                ).group_by('skill_level').all()
                
                skill_distribution = {level: count for level, count in skill_data}
            except Exception as e:
                print(f"[ML] Error getting skill distribution: {e}")
        
        # Get top performing categories
        top_categories = []
        if ml_available and active_profiles > 0:
            try:
                category_performance = db.session.query(
                    UserSkillProfile.category,
                    db.func.avg(UserSkillProfile.accuracy_score).label('avg_score'),
                    db.func.count(UserSkillProfile.id).label('profile_count')
                ).group_by(UserSkillProfile.category).having(
                    db.func.count(UserSkillProfile.id) >= 5  # At least 5 profiles
                ).order_by(db.desc('avg_score')).limit(5).all()
                
                top_categories = [{
                    'name': category,
                    'avg_score': float(avg_score)
                } for category, avg_score, _ in category_performance]
            except Exception as e:
                print(f"[ML] Error getting top categories: {e}")
        
        # Get problem areas (low performing categories)
        problem_areas = []
        if ml_available and active_profiles > 0:
            try:
                problem_performance = db.session.query(
                    UserSkillProfile.category,
                    db.func.avg(UserSkillProfile.accuracy_score).label('avg_score'),
                    db.func.count(UserSkillProfile.id).label('profile_count')
                ).group_by(UserSkillProfile.category).having(
                    db.func.count(UserSkillProfile.id) >= 5  # At least 5 profiles
                ).order_by('avg_score').limit(5).all()
                
                problem_areas = [{
                    'name': category,
                    'avg_score': float(avg_score)
                } for category, avg_score, _ in problem_performance if avg_score < 0.6]
            except Exception as e:
                print(f"[ML] Error getting problem areas: {e}")
        
        # Mock model performance data
        model_performance = {
            'difficulty_model': {
                'accuracy': 0.82,
                'predictions_count': QuestionDifficultyProfile.query.count() if ml_available else 0,
                'last_updated': datetime.now() - timedelta(hours=2)
            },
            'adaptive_model': {
                'personalization_rate': 0.75,
                'active_users': active_profiles,
                'avg_improvement': 0.15
            },
            'question_model': {
                'questions_analyzed': Question.query.count(),
                'difficulty_profiles': QuestionDifficultyProfile.query.count() if ml_available else 0,
                'avg_discrimination': 0.68
            }
        }
        
        # Mock recent ML activity
        recent_ml_activity = [
            {
                'action': 'Profile Updated',
                'details': f'{active_profiles} user profiles refreshed',
                'timestamp': datetime.now() - timedelta(minutes=15)
            },
            {
                'action': 'Model Retrained',
                'details': 'Difficulty prediction model updated',
                'timestamp': datetime.now() - timedelta(hours=2)
            },
            {
                'action': 'Analytics Generated',
                'details': 'Weekly learning analytics computed',
                'timestamp': datetime.now() - timedelta(hours=6)
            }
        ]
        
        return {
            'ml_status': ml_status,
            'ml_stats': ml_stats,
            'ml_config': ml_config,
            'skill_distribution': skill_distribution,
            'top_categories': top_categories,
            'problem_areas': problem_areas,
            'model_performance': model_performance,
            'recent_ml_activity': recent_ml_activity
        }
        
    except Exception as e:
        print(f"[ML] Error in get_ml_context: {e}")
        # Return safe fallback data
        return {
            'ml_status': {
                'ml_enabled': False,
                'algorithm_version': '1.0',
                'error': str(e)
            },
            'ml_stats': {
                'total_users': User.query.count() if User else 0,
                'active_profiles': 0,
                'adaptive_sessions': 0
            },
            'ml_config': {
                'learning_rate': 0.05,
                'adaptation_strength': 0.5,
                'collect_response_times': True,
                'track_confidence': True,
                'analyze_patterns': True,
                'update_frequency': 'daily'
            },
            'skill_distribution': {},
            'top_categories': [],
            'problem_areas': [],
            'model_performance': {},
            'recent_ml_activity': []
        }

# ========================================
# ML API ENDPOINTS
# ========================================

@admin_bp.route('/api/ml-status', methods=['GET'])
@admin_required
def api_ml_status():
    """Get ML system status"""
    try:
        context = get_ml_context()
        return jsonify({
            'success': True,
            'status': context['ml_status'],
            'stats': context['ml_stats']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/ml-export', methods=['GET'])
@admin_required
def api_ml_export():
    """Export ML analytics data"""
    try:
        # Create CSV export of ML data
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Metric', 'Value', 'Timestamp'])
        
        # Get context data
        context = get_ml_context()
        
        # Write stats
        for key, value in context['ml_stats'].items():
            writer.writerow([key, value, datetime.now().isoformat()])
        
        # Write skill distribution
        for level, count in context['skill_distribution'].items():
            writer.writerow([f'skill_level_{level}', count, datetime.now().isoformat()])
        
        csv_content = output.getvalue()
        output.close()
        
        # Log the export
        AdminSecurityService.log_admin_action(
            admin_user=current_user,
            action='ml_data_export',
            additional_info=json.dumps({
                'export_type': 'analytics',
                'timestamp': datetime.now().isoformat()
            })
        )
        
        return jsonify({
            'success': True,
            'data': csv_content,
            'filename': f'ml_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/ml-reset', methods=['POST'])
@admin_required
def api_ml_reset():
    """Reset ML models and data"""
    try:
        # Try to import ML modules
        try:
            from ..ml.models import UserSkillProfile, QuestionDifficultyProfile, AdaptiveQuizSession, LearningAnalytics, MLModel
            
            # Count before reset
            profiles_count = UserSkillProfile.query.count()
            models_count = MLModel.query.count()
            
            # Clear ML data (be careful!)
            # In a production system, you might want to archive this data instead
            UserSkillProfile.query.delete()
            QuestionDifficultyProfile.query.delete()
            AdaptiveQuizSession.query.delete()
            LearningAnalytics.query.delete()
            MLModel.query.delete()
            
            db.session.commit()
            
            # Log the reset
            AdminSecurityService.log_admin_action(
                admin_user=current_user,
                action='ml_system_reset',
                additional_info=json.dumps({
                    'profiles_deleted': profiles_count,
                    'models_deleted': models_count,
                    'timestamp': datetime.now().isoformat()
                })
            )
            
            return jsonify({
                'success': True,
                'message': f'ML system reset complete. Deleted {profiles_count} profiles and {models_count} models.',
                'deleted': {
                    'profiles': profiles_count,
                    'models': models_count
                }
            })
            
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'ML modules not available'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/ml-diagnostics', methods=['GET'])
@admin_required
def api_ml_diagnostics():
    """Get ML system diagnostics"""
    try:
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'system_health': 'good',
            'modules_available': False,
            'database_tables': [],
            'data_counts': {},
            'potential_issues': []
        }
        
        # Check ML module availability
        try:
            from ..ml.service import ml_service
            from ..ml.models import UserSkillProfile, QuestionDifficultyProfile, AdaptiveQuizSession, LearningAnalytics, MLModel
            diagnostics['modules_available'] = True
            diagnostics['ml_service_initialized'] = hasattr(ml_service, '_initialized') and ml_service._initialized
            
            # Check table existence and counts
            tables = {
                'UserSkillProfile': UserSkillProfile.query.count(),
                'QuestionDifficultyProfile': QuestionDifficultyProfile.query.count(),
                'AdaptiveQuizSession': AdaptiveQuizSession.query.count(),
                'LearningAnalytics': LearningAnalytics.query.count(),
                'MLModel': MLModel.query.count()
            }
            diagnostics['data_counts'] = tables
            
            # Check for potential issues
            total_users = User.query.count()
            users_with_profiles = UserSkillProfile.query.distinct(UserSkillProfile.user_id).count()
            
            if total_users > 10 and users_with_profiles == 0:
                diagnostics['potential_issues'].append('No user skill profiles found despite having users')
            
            if Question.query.count() > 10 and tables['QuestionDifficultyProfile'] == 0:
                diagnostics['potential_issues'].append('No question difficulty profiles found despite having questions')
            
            if not diagnostics['potential_issues']:
                diagnostics['potential_issues'].append('No issues detected')
                
        except ImportError as e:
            diagnostics['import_error'] = str(e)
            diagnostics['potential_issues'].append(f'ML modules not available: {str(e)}')
        except Exception as e:
            diagnostics['ml_error'] = str(e)
            diagnostics['potential_issues'].append(f'ML system error: {str(e)}')
        
        # Basic database checks
        try:
            diagnostics['basic_counts'] = {
                'total_users': User.query.count(),
                'total_questions': Question.query.count(),
                'total_quiz_sessions': QuizSession.query.count()
            }
        except Exception as e:
            diagnostics['basic_counts'] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'diagnostics': diagnostics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/ml-refresh', methods=['POST'])
@admin_required
def api_ml_refresh():
    """Refresh ML data and models"""
    try:
        # Try to refresh ML data
        try:
            from ..ml.service import ml_service
            
            # Force re-initialization
            ml_service.initialize()
            
            # Get updated context
            context = get_ml_context()
            
            # Log the refresh
            AdminSecurityService.log_admin_action(
                admin_user=current_user,
                action='ml_data_refresh',
                additional_info=json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'active_profiles': context['ml_stats']['active_profiles']
                })
            )
            
            return jsonify({
                'success': True,
                'message': 'ML data refreshed successfully',
                'stats': context['ml_stats']
            })
            
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'ML modules not available'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
