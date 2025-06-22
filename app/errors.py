# app/errors.py - Centralized Error Handling
from flask import render_template, request, jsonify, current_app
from werkzeug.exceptions import HTTPException
import logging
import traceback
from datetime import datetime
from . import db
from .models import AdminReport


class ErrorHandler:
    """Centralized error handling and reporting"""
    
    @staticmethod
    def log_error(error, error_type="system_error", user_id=None, ip_address=None, url=None):
        """Log error to database and file"""
        try:
            # Log to file
            current_app.logger.error(f"Error: {str(error)}")
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Create admin report for tracking
            report = AdminReport(
                report_type=error_type,
                priority='high' if error_type in ['database_error', 'payment_error'] else 'medium',
                title=f"Application Error: {error.__class__.__name__}",
                description=str(error),
                affected_user_id=user_id,
                ip_address=ip_address or (request.remote_addr if request else None),
                url=url or (request.url if request else None),
                error_message=str(error),
                stack_trace=traceback.format_exc(),
                user_agent=request.headers.get('User-Agent') if request else None
            )
            
            db.session.add(report)
            db.session.commit()
            
        except Exception as db_error:
            # Fallback logging if database fails
            current_app.logger.critical(f"Failed to log error to database: {db_error}")
            current_app.logger.critical(f"Original error: {error}")


def register_error_handlers(app):
    """Register all error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors"""
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.',
                'status_code': 404
            }), 404
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        ErrorHandler.log_error(error, "access_denied")
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource.',
                'status_code': 403
            }), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server errors"""
        ErrorHandler.log_error(error, "server_error")
        db.session.rollback()
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'status_code': 500
            }), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle all unexpected errors"""
        if isinstance(error, HTTPException):
            return error
        
        ErrorHandler.log_error(error, "unexpected_error")
        db.session.rollback()
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unexpected Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'status_code': 500
            }), 500
        
        return render_template('errors/500.html'), 500


# Custom Exceptions for Business Logic
class SertifikatetException(Exception):
    """Base exception for Sertifikatet application"""
    def __init__(self, message, status_code=500, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class SubscriptionException(SertifikatetException):
    """Subscription-related errors"""
    def __init__(self, message, status_code=400):
        super().__init__(message, status_code, "SUBSCRIPTION_ERROR")


class QuotaExceededException(SertifikatetException):
    """User has exceeded their usage quota"""
    def __init__(self, message="Daily quiz limit exceeded", status_code=429):
        super().__init__(message, status_code, "QUOTA_EXCEEDED")
