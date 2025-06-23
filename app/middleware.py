"""
Developer Authentication Middleware
Protects the entire site during development with basic auth
"""
from functools import wraps
from flask import request, Response, session, redirect, url_for, render_template_string
import os

# Developer credentials
DEV_USERNAME = os.getenv('DEV_USERNAME', 'admin')
DEV_PASSWORD = os.getenv('DEV_PASSWORD', 'test123')
DEV_MODE = os.getenv('DEV_MODE', 'True').lower() in ('true', '1', 'yes')

def check_dev_auth(username, password):
    """Check if developer credentials are valid"""
    return username == DEV_USERNAME and password == DEV_PASSWORD

def dev_auth_required(f):
    """Decorator to require developer authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip dev auth if disabled
        if not DEV_MODE:
            return f(*args, **kwargs)
        
        # Check if already authenticated
        if session.get('dev_authenticated'):
            return f(*args, **kwargs)
        
        # Check for basic auth header
        auth = request.authorization
        if auth and check_dev_auth(auth.username, auth.password):
            session['dev_authenticated'] = True
            return f(*args, **kwargs)
        
        # Return 401 with basic auth prompt
        return Response(
            'Developer Access Required\n'
            'Please enter your developer credentials.',
            401,
            {'WWW-Authenticate': 'Basic realm="Developer Area"'}
        )
    return decorated

def apply_dev_auth_to_app(app):
    """Apply developer authentication to all routes"""
    if not DEV_MODE:
        return
    
    @app.before_request
    def require_dev_auth():
        # Skip auth for static files
        if request.endpoint == 'static':
            return
        
        # Skip auth if already authenticated
        if session.get('dev_authenticated'):
            return
        
        # Check for basic auth header
        auth = request.authorization
        if auth and check_dev_auth(auth.username, auth.password):
            session['dev_authenticated'] = True
            return
        
        # Show custom login page for better UX
        if request.path == '/dev-login':
            return render_dev_login()
        
        # Redirect to custom login page
        return redirect('/dev-login')
    
    @app.route('/dev-login', methods=['GET', 'POST'])
    def render_dev_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if check_dev_auth(username, password):
                session['dev_authenticated'] = True
                return redirect(request.args.get('next', '/'))
            else:
                error = 'Invalid credentials'
        else:
            error = None
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Access - Sertifikatet.no</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #333;
            margin: 0;
            font-size: 2rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #5a6fd8;
        }
        .error {
            color: #e74c3c;
            margin-top: 1rem;
            text-align: center;
        }
        .dev-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin-top: 1rem;
            font-size: 0.9rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🚗 Sertifikatet.no</h1>
            <p>Developer Access</p>
        </div>
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="btn">Access Developer Site</button>
            
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
        </form>
        
        <div class="dev-info">
            <strong>Development Mode Active</strong><br>
            This site is currently in development and requires authentication.<br>
            Contact the development team for access credentials.
        </div>
    </div>
</body>
</html>
        ''', error=error)
    
    @app.route('/dev-logout')
    def dev_logout():
        session.pop('dev_authenticated', None)
        return redirect('/dev-login')
