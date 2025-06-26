# app/legal/routes.py
from flask import render_template
from . import legal_bp


@legal_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('legal/terms.html')


@legal_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('legal/privacy.html')
