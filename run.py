#!/usr/bin/env python
"""
Main entry point for the Flask application
"""
import os
from flask import jsonify
from datetime import datetime
from app import create_app

# Create the Flask application
app = create_app()

# Add health check endpoint for deployment verification
@app.route('/health')
def health_check():
    """Health check endpoint for deployment verification"""
    try:
        # Check database connection
        from app import db
        db.session.execute('SELECT 1')
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Get basic system info
    health_data = {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("FLASK_ENV", "development"),
        "database": db_status,
        "uptime": "running"
    }
    
    status_code = 200 if health_data["status"] == "healthy" else 503
    return jsonify(health_data), status_code

if __name__ == '__main__':
    # Create static directories if they don't exist
    static_dir = app.static_folder
    os.makedirs(os.path.join(static_dir, 'images', 'signs'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'images', 'quiz'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'images', 'custom'), exist_ok=True)
    
    # Run the application
    # Note: When using Cloudflare Tunnel, this will be accessible via sertifikatet.no
    # The tunnel will proxy requests from the domain to localhost:8000
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),  # Use localhost for security with tunnel
        port=int(os.getenv('PORT', 8000)),  # Updated to match deployment scripts
        debug=app.config['DEBUG']
    )
