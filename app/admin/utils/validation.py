# app/admin/utils.py

def validate_question(data, question_id=None):
    """Validate question data"""
    errors = []
    
    # Check required fields
    required_fields = {
        'question': 'Spørsmålsteksten',
        'option_a': 'Alternativ A',
        'option_b': 'Alternativ B', 
        'option_c': 'Alternativ C',
        'option_d': 'Alternativ D',
        'correct_option': 'Riktig svar'
    }
    
    for field, name in required_fields.items():
        field_value = data.get(field, '')
        # Handle None values by converting to empty string
        if field_value is None:
            field_value = ''
        if not str(field_value).strip():
            errors.append(f"{name} kan ikke være tom.")
    
    # Validate correct answer
    correct_option = data.get('correct_option', '')
    # Handle None values
    if correct_option is None:
        correct_option = ''
    if str(correct_option).lower() not in ['a', 'b', 'c', 'd']:
        errors.append('Riktig svar må være a, b, c eller d.')
    
    return errors
