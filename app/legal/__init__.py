# app/legal/__init__.py
from flask import Blueprint

legal_bp = Blueprint('legal', __name__, url_prefix='/legal')

from . import routes
