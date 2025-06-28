"""
Advertising Module for Sertifikatet
Handles ad management, revenue tracking, and smart upgrade prompts
"""

from flask import Blueprint

advertising = Blueprint('advertising', __name__, url_prefix='/api/advertising')

from . import routes, services, analytics
