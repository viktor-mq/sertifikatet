# app/gamification/__init__.py
from flask import Blueprint

gamification_bp = Blueprint('gamification', __name__)

from . import routes, services
