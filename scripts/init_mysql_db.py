#!/usr/bin/env python
"""
Initialize the MySQL database with Flask-Migrate
"""
import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_migrate import init, migrate, upgrade
from app import create_app, db

def init_db():
    """Initialize the database with Flask-Migrate"""
    
    app = create_app()
    
    with app.app_context():
        # Initialize migrations if not already done
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
        
        if not os.path.exists(migrations_dir):
            print("Initializing Flask-Migrate...")
            init()
        
        # Create a new migration
        print("Creating migration...")
        migrate(message='Initial migration')
        
        # Apply the migration
        print("Applying migration...")
        upgrade()
        
        print("Database initialized successfully!")


if __name__ == '__main__':
    init_db()
