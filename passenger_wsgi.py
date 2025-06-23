#!/usr/bin/env python3
"""
Passenger WSGI file for cPanel hosting
This file is required for cPanel's Python app hosting
"""
import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables for production
os.environ['FLASK_ENV'] = 'production'

try:
    # Import your Flask application
    from app import create_app
    
    # Create the application instance
    application = create_app()
    
    # For development/testing
    if __name__ == "__main__":
        application.run(debug=False)
        
except Exception as e:
    # Create a simple error application for debugging
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>Application Error</h1>
        <p>Error: {str(e)}</p>
        <p>Check the error logs in cPanel for more details.</p>
        """
