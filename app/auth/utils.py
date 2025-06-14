# app/auth/utils.py
"""
Utility functions for authentication
"""

def validate_password(password):
    """
    Validate password against requirements.
    
    Args:
        password (str): Password to validate
        
    Returns:
        list: List of error messages (empty if valid)
    """
    errors = []
    
    if not password or len(password) < 8:
        errors.append('Passordet må være minst 8 tegn langt')
    
    if password and not any(c.isupper() for c in password):
        errors.append('Passordet må inneholde minst én stor bokstav')
    
    if password and not any(c.islower() for c in password):
        errors.append('Passordet må inneholde minst én liten bokstav')
    
    if password and not any(c.isdigit() for c in password):
        errors.append('Passordet må inneholde minst ett tall')
    
    return errors
