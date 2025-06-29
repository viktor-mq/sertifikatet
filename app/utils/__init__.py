# app/utils/__init__.py
"""Utility functions and helpers for the application."""

from .email import (
    send_email,
    send_verification_email,
    send_password_reset_email,
    send_learning_reminder_email,
    send_badge_notification,
    send_admin_alert,
    send_batch_reminders,
    verify_email_token,
    verify_reset_token,
    send_welcome_email,
    send_streak_lost_email,
    send_weekly_summary_email,
    send_study_tip_email,
    send_user_report_alert,
    send_manual_review_alert
)

__all__ = [
    'send_email',
    'send_verification_email',
    'send_password_reset_email',
    'send_learning_reminder_email',
    'send_badge_notification',
    'send_admin_alert',
    'send_batch_reminders',
    'verify_email_token',
    'verify_reset_token',
    'send_welcome_email',
    'send_streak_lost_email',
    'send_weekly_summary_email',
    'send_study_tip_email',
    'send_user_report_alert',
    'send_manual_review_alert'
]
