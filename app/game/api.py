from flask import jsonify, request
from flask_login import login_required, current_user
from . import game_bp
from ..models import db, GameScenario, GameSession, TrafficSign, Question
import random
import json

@game_bp.route('/api/traffic-signs/random', methods=['GET'])
@login_required
def get_random_traffic_signs():
    """Get random traffic signs for the recognition game."""
    count = request.args.get('count', 10, type=int)
    
    # Get random traffic signs
    signs = TrafficSign.query.filter(TrafficSign.filename.isnot(None)).all()
    
    if len(signs) < count:
        count = len(signs)
    
    selected_signs = random.sample(signs, count)
    
    return jsonify({
        'signs': [{
            'id': sign.id,
            'sign_code': sign.sign_code,
            'category': sign.category,
            'filename': sign.filename,
            'description': sign.description
        } for sign in selected_signs]
    })

@game_bp.route('/api/traffic-signs/check', methods=['POST'])
@login_required
def check_traffic_sign():
    """Check if the user correctly identified a traffic sign."""
    data = request.get_json()
    sign_id = data.get('sign_id')
    user_answer = data.get('answer', '').lower()
    
    sign = TrafficSign.query.get_or_404(sign_id)
    
    # Check if answer is correct (flexible matching)
    correct = False
    if sign.description:
        description_lower = sign.description.lower()
        # Check for partial match
        if user_answer in description_lower or description_lower in user_answer:
            correct = True
    
    return jsonify({
        'correct': correct,
        'correct_answer': sign.description,
        'explanation': sign.explanation
    })

@game_bp.route('/api/memory-game/cards', methods=['GET'])
@login_required
def get_memory_cards():
    """Get pairs of traffic signs for memory game."""
    pairs = request.args.get('pairs', 8, type=int)
    
    # Get random traffic signs with images
    signs = TrafficSign.query.filter(TrafficSign.filename.isnot(None)).limit(pairs).all()
    
    # Create pairs
    cards = []
    for i, sign in enumerate(signs):
        # Add each sign twice for matching
        for _ in range(2):
            cards.append({
                'id': f"{sign.id}_{_}",
                'sign_id': sign.id,
                'filename': sign.filename,
                'description': sign.description,
                'matched': False
            })
    
    # Shuffle cards
    random.shuffle(cards)
    
    return jsonify({'cards': cards})

@game_bp.route('/api/driving-scenario', methods=['GET'])
@login_required
def get_driving_scenario():
    """Get a driving scenario with questions."""
    # Get random driving-related questions
    questions = Question.query.filter(
        Question.category.in_(['Vikeplikt', 'Trafikkregler', 'Kjøreteknikk'])
    ).order_by(db.func.random()).limit(5).all()
    
    scenarios = []
    for q in questions:
        scenario = {
            'id': q.id,
            'situation': q.question,
            'image': q.image_filename,
            'options': [{
                'letter': opt.option_letter,
                'text': opt.option_text
            } for opt in q.options],
            'correct_option': q.correct_option,
            'explanation': q.explanation
        }
        scenarios.append(scenario)
    
    return jsonify({'scenarios': scenarios})

@game_bp.route('/api/rule-puzzle/generate', methods=['GET'])
@login_required
def generate_rule_puzzle():
    """Generate a rule-based puzzle."""
    puzzle_types = ['priority', 'speed_limit', 'distance', 'parking']
    puzzle_type = random.choice(puzzle_types)
    
    puzzle = None
    
    if puzzle_type == 'priority':
        # Generate a priority/right-of-way puzzle
        situations = [
            {
                'description': 'Du kommer til et uregulert kryss samtidig med en bil fra høyre.',
                'question': 'Hvem har vikeplikt?',
                'options': ['Du har vikeplikt', 'Den andre bilen har vikeplikt', 'Begge må vente'],
                'correct': 0,
                'rule': 'Høyreregelen: Kjøretøy fra høyre har forkjørsrett i uregulerte kryss.'
            },
            {
                'description': 'Du skal svinge til venstre i et lyskryss med grønt lys. En bil kommer imot.',
                'question': 'Hvem må vente?',
                'options': ['Du må vente', 'Motgående bil må vente', 'Begge kan kjøre samtidig'],
                'correct': 0,
                'rule': 'Ved venstresving må du vike for motgående trafikk.'
            }
        ]
        puzzle = random.choice(situations)
    
    elif puzzle_type == 'speed_limit':
        # Speed limit puzzle
        zones = [
            {'zone': 'Tettbygd strøk', 'default': 50, 'unless': 'annet er skiltet'},
            {'zone': 'Landevei', 'default': 80, 'unless': 'annet er skiltet'},
            {'zone': 'Motorvei', 'default': 110, 'unless': 'annet er skiltet'},
            {'zone': 'Boliggate', 'default': 30, 'unless': 'annet er skiltet'}
        ]
        zone = random.choice(zones)
        puzzle = {
            'description': f'Du kjører i {zone["zone"]} uten fartsgrenseskilt.',
            'question': 'Hva er fartsgrensen?',
            'options': [f'{zone["default"]} km/t', f'{zone["default"]-20} km/t', f'{zone["default"]+20} km/t'],
            'correct': 0,
            'rule': f'Standard fartsgrense i {zone["zone"]} er {zone["default"]} km/t {zone["unless"]}.'
        }
        random.shuffle(puzzle['options'])
    
    return jsonify({'puzzle': puzzle, 'type': puzzle_type})

@game_bp.route('/api/time-challenge/questions', methods=['GET'])
@login_required
def get_time_challenge_questions():
    """Get rapid-fire questions for time challenge."""
    # Get 20 random questions from different categories
    questions = Question.query.filter(
        Question.is_active == True
    ).order_by(db.func.random()).limit(20).all()
    
    challenge_questions = []
    for q in questions:
        challenge_questions.append({
            'id': q.id,
            'question': q.question,
            'image': q.image_filename,
            'options': [{
                'letter': opt.option_letter,
                'text': opt.option_text
            } for opt in q.options],
            'correct': q.correct_option,
            'category': q.category
        })
    
    return jsonify({
        'questions': challenge_questions,
        'time_limit': 120,  # 2 minutes for 20 questions
        'points_per_correct': 10,
        'time_bonus_per_second': 1
    })

@game_bp.route('/api/multiplayer/find-match', methods=['POST'])
@login_required
def find_multiplayer_match():
    """Find a multiplayer match (placeholder for now)."""
    if current_user.subscription_tier == 'free':
        return jsonify({'error': 'Premium subscription required'}), 403
    
    # This is a placeholder - real implementation would use WebSockets
    return jsonify({
        'status': 'searching',
        'message': 'Søker etter motspillere...',
        'estimated_time': 30
    })

@game_bp.route('/api/game-stats', methods=['GET'])
@login_required
def get_game_stats():
    """Get user's game statistics."""
    stats = db.session.query(
        GameScenario.name,
        GameScenario.scenario_type,
        db.func.count(GameSession.id).label('games_played'),
        db.func.max(GameSession.score).label('high_score'),
        db.func.avg(GameSession.score).label('avg_score')
    ).join(GameSession).filter(
        GameSession.user_id == current_user.id,
        GameSession.completed == True
    ).group_by(GameScenario.id).all()
    
    return jsonify({
        'stats': [{
            'game_name': stat.name,
            'game_type': stat.scenario_type,
            'games_played': stat.games_played,
            'high_score': stat.high_score,
            'avg_score': round(stat.avg_score) if stat.avg_score else 0
        } for stat in stats]
    })
