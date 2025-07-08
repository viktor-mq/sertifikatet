# app/learning/__init__.py
from flask import Blueprint

learning_bp = Blueprint('learning', __name__)

from app.learning import routes