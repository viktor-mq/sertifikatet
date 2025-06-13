# app/utils/celery_tasks.py
"""
Celery tasks for asynchronous operations and scheduled jobs.
Note: This is an optional implementation. You need to install and configure Celery separately.

To use:
1. Install: pip install celery redis
2. Run Redis server
3. Run Celery worker: celery -A app.utils.celery_tasks worker --loglevel=info
4. Run Celery beat: celery -A app.utils.celery_tasks beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime
import os

# Initialize Celery (example configuration)
celery = Celery(
    'sertifikatet',
    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery.conf.update(
    timezone='Europe/Oslo',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,
    beat_schedule={
        'send-daily-reminders': {
            'task': 'app.utils.celery_tasks.send_daily_reminders',
            'schedule': crontab(hour=18, minute=0),  # Send at 18:00 every day
        },
        'check-streaks': {
            'task': 'app.utils.celery_tasks.check_and_update_streaks',
            'schedule': crontab(hour=0, minute=5),  # Check streaks at 00:05 every day
        },
        'weekly-leaderboard': {
            'task': 'app.utils.celery_tasks.update_weekly_leaderboard',
            'schedule': crontab(hour=0, minute=0, day_of_week=1),  # Monday at midnight
        },
    }
)


@celery.task
def send_daily_reminders():
    """Send daily learning reminders to eligible users."""
    from app import create_app
    from app.utils.email import send_batch_reminders
    
    app = create_app()
    with app.app_context():
        send_batch_reminders()
        return {'status': 'completed', 'timestamp': datetime.now().isoformat()}


@celery.task
def send_async_email_task(subject, recipients, html_body):
    """Send email asynchronously using Celery."""
    from app import create_app
    from app.utils.email import send_email
    
    app = create_app()
    with app.app_context():
        send_email(subject, recipients, html_body)
        return {'status': 'sent', 'recipients': recipients}


@celery.task
def check_and_update_streaks():
    """Check and update user streaks at midnight."""
    from app import create_app, db
    from app.models import User, UserProgress
    from datetime import date, timedelta
    
    app = create_app()
    with app.app_context():
        yesterday = date.today() - timedelta(days=1)
        
        # Find users who didn't practice yesterday and had a streak
        broken_streaks = db.session.query(UserProgress).filter(
            UserProgress.last_activity_date < yesterday,
            UserProgress.current_streak_days > 0
        ).all()
        
        for progress in broken_streaks:
            progress.current_streak_days = 0
        
        db.session.commit()
        
        return {
            'status': 'completed',
            'broken_streaks': len(broken_streaks),
            'timestamp': datetime.now().isoformat()
        }


@celery.task
def update_weekly_leaderboard():
    """Update weekly leaderboard entries."""
    from app import create_app, db
    from app.models import User, LeaderboardEntry, UserProgress
    from datetime import date, timedelta
    
    app = create_app()
    with app.app_context():
        # Calculate weekly scores and create leaderboard entries
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)
        
        # Get top users by XP gained this week
        # (This is a simplified example - you'd want more sophisticated scoring)
        
        return {
            'status': 'completed',
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'timestamp': datetime.now().isoformat()
        }


@celery.task
def send_achievement_notification_task(user_id, achievement_name):
    """Send achievement notification asynchronously."""
    from app import create_app, db
    from app.models import User
    from app.utils.email import send_badge_notification
    
    app = create_app()
    with app.app_context():
        user = User.query.get(user_id)
        if user:
            send_badge_notification(user, achievement_name)
            return {'status': 'sent', 'user_id': user_id, 'achievement': achievement_name}
        return {'status': 'user_not_found', 'user_id': user_id}
