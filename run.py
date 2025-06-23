#!/usr/bin/env python
"""
Main entry point for the Flask application
"""
import os
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Create static directories if they don't exist
    static_dir = app.static_folder
    os.makedirs(os.path.join(static_dir, 'images', 'signs'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'images', 'quiz'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'images', 'custom'), exist_ok=True)
    
    # Run the application
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 8000)),
        debug=app.config['DEBUG']
    )
