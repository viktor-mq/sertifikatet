# app/learning/routes.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from . import learning_bp
from .. import db
from ..models import (
    LearningPath, LearningPathItem, UserLearningPath, 
    Question, Video, GameScenario, QuizSession, VideoProgress,
    UserProgress, QuizResponse
)
from ..services.progress_service import ProgressService
from ..services.achievement_service import AchievementService


@learning_bp.route('/learning')
@login_required
def index():
    """Display all learning paths with user progress."""
    # Get all learning paths
    learning_paths = LearningPath.query.order_by(
        LearningPath.is_recommended.desc(),
        LearningPath.difficulty_level
    ).all()
    
    # Get user's enrolled paths
    user_paths = {up.path_id: up for up in current_user.learning_paths}
    
    # Add user progress info to each path
    paths_with_progress = []
    for path in learning_paths:
        path_info = {
            'path': path,
            'user_path': user_paths.get(path.id),
            'is_enrolled': path.id in user_paths,
            'progress': user_paths.get(path.id).progress_percentage if path.id in user_paths else 0,
            'total_items': len(path.items)
        }
        paths_with_progress.append(path_info)
    
    return render_template('learning/index.html',
                         paths=paths_with_progress,
                         title='Læringsveier')


@learning_bp.route('/learning/<int:path_id>')
@login_required
def view_path(path_id):
    """View detailed learning path with all items."""
    path = LearningPath.query.get_or_404(path_id)
    
    # Check if user is enrolled
    user_path = UserLearningPath.query.filter_by(
        user_id=current_user.id,
        path_id=path_id
    ).first()
    
    # Get all items with their content
    path_items = []
    for item in path.items:
        item_info = {
            'item': item,
            'content': None,
            'completed': False,
            'locked': False
        }
        
        # Get the actual content based on item type
        if item.item_type == 'quiz':
            item_info['content'] = Question.query.filter_by(
                category=item.item_id  # Using category as identifier for quiz topics
            ).first()
            # Check if user has completed quiz in this category
            if user_path:
                completed_quiz = QuizSession.query.filter_by(
                    user_id=current_user.id,
                    category=item.item_id,
                    quiz_type='learning_path'
                ).filter(QuizSession.score >= 80).first()
                item_info['completed'] = completed_quiz is not None
                
        elif item.item_type == 'video':
            item_info['content'] = Video.query.get(item.item_id)
            # Check if user has watched the video
            if user_path and item_info['content']:
                video_progress = VideoProgress.query.filter_by(
                    user_id=current_user.id,
                    video_id=item.item_id
                ).first()
                item_info['completed'] = video_progress and video_progress.completed
                
        elif item.item_type == 'game':
            item_info['content'] = GameScenario.query.get(item.item_id)
            # Games will be implemented later
            
        # Check if item is locked (previous mandatory items not completed)
        if item.order_index > 0:
            prev_items = [i for i in path_items if i['item'].order_index < item.order_index]
            mandatory_incomplete = any(
                i['item'].is_mandatory and not i['completed'] 
                for i in prev_items
            )
            item_info['locked'] = mandatory_incomplete
            
        path_items.append(item_info)
    
    # Calculate overall progress
    completed_items = sum(1 for item in path_items if item['completed'])
    progress = int((completed_items / len(path_items) * 100)) if path_items else 0
    
    return render_template('learning/path_detail.html',
                         path=path,
                         user_path=user_path,
                         path_items=path_items,
                         progress=progress,
                         title=path.name)


@learning_bp.route('/learning/<int:path_id>/enroll', methods=['POST'])
@login_required
def enroll_path(path_id):
    """Enroll user in a learning path."""
    path = LearningPath.query.get_or_404(path_id)
    
    # Check if already enrolled
    existing = UserLearningPath.query.filter_by(
        user_id=current_user.id,
        path_id=path_id
    ).first()
    
    if existing:
        flash('Du er allerede påmeldt denne læringsveien!', 'info')
    else:
        # Create enrollment
        user_path = UserLearningPath(
            user_id=current_user.id,
            path_id=path_id,
            progress_percentage=0
        )
        db.session.add(user_path)
        db.session.commit()
        
        flash(f'Du er nå påmeldt "{path.name}"!', 'success')
        
        # Check for achievement
        AchievementService.check_and_award_achievement(
            current_user.id, 'learning_path_enrolled'
        )
    
    return redirect(url_for('learning.view_path', path_id=path_id))


@learning_bp.route('/learning/<int:path_id>/item/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_item(path_id, item_id):
    """Mark a learning path item as complete."""
    user_path = UserLearningPath.query.filter_by(
        user_id=current_user.id,
        path_id=path_id
    ).first_or_404()
    
    path_item = LearningPathItem.query.get_or_404(item_id)
    
    # Update progress
    total_items = len(user_path.path.items)
    completed_items = request.json.get('completed_items', 1)
    
    user_path.progress_percentage = int((completed_items / total_items) * 100)
    
    # Check if path is completed
    if user_path.progress_percentage >= 100:
        user_path.completed_at = datetime.utcnow()
        
        # Award XP and check achievements
        ProgressService.update_user_progress(current_user.id, xp_earned=100)
        AchievementService.check_and_award_achievement(
            current_user.id, 'learning_path_completed'
        )
        
        flash(f'Gratulerer! Du har fullført "{user_path.path.name}"!', 'success')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'progress': user_path.progress_percentage,
        'completed': user_path.completed_at is not None
    })


@learning_bp.route('/learning/recommendations')
@login_required
def get_recommendations():
    """Get personalized learning path recommendations."""
    # Get user's quiz performance by category
    category_performance = db.session.query(
        Question.category,
        func.avg(QuizResponse.is_correct).label('accuracy')
    ).join(
        QuizResponse, Question.id == QuizResponse.question_id
    ).join(
        QuizSession, QuizResponse.session_id == QuizSession.id
    ).filter(
        QuizSession.user_id == current_user.id
    ).group_by(Question.category).all()
    
    # Find categories where user needs improvement (< 70% accuracy)
    weak_categories = [cat for cat, acc in category_performance if acc < 0.7]
    
    # Get recommended paths based on weak categories
    recommended_paths = []
    if weak_categories:
        # Find paths that cover weak categories
        paths = LearningPath.query.all()
        for path in paths:
            # Check if path covers any weak categories
            path_categories = set()
            for item in path.items:
                if item.item_type == 'quiz':
                    path_categories.add(item.item_id)  # item_id stores category
            
            if path_categories.intersection(weak_categories):
                recommended_paths.append(path)
    
    # If no specific recommendations, return beginner paths
    if not recommended_paths:
        recommended_paths = LearningPath.query.filter_by(
            difficulty_level=1,
            is_recommended=True
        ).limit(3).all()
    
    return jsonify({
        'recommendations': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'difficulty': p.difficulty_level,
            'estimated_hours': p.estimated_hours
        } for p in recommended_paths[:3]]
    })


@learning_bp.route('/learning/my-paths')
@login_required
def my_paths():
    """Show user's enrolled learning paths."""
    user_paths = UserLearningPath.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UserLearningPath.completed_at.asc(),
        UserLearningPath.progress_percentage.desc()
    ).all()
    
    return render_template('learning/my_paths.html',
                         user_paths=user_paths,
                         title='Mine Læringsveier')
