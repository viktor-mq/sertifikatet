# Rule Puzzle Game Logic
"""
Core game logic for the traffic scenario puzzle game
"""

import random
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from games.base.interfaces import BaseGame, GameResult
from games.base.models import GameQuestion, GameAnswer, GameScore
from .config import GAME_CONFIG, SCORING, ACHIEVEMENTS
import json


class RulePuzzleGame(BaseGame):
    """Traffic scenario puzzle game implementation"""
    
    def __init__(self, user_id: int, game_id: str = "rule_puzzle"):
        super().__init__(user_id, game_id)
        self.difficulty = "medium"
        self.scenario_type = None
        self.current_scenario = None
        self.vehicle_positions = {}
        self.correct_positions = {}
        self.hints_used = 0
        self.moves_made = 0
        self.perfect_score = True
        
    def start_session(self) -> Dict[str, Any]:
        """Initialize a new puzzle session"""
        from games.base.utils import generate_session_id
        from app.models import GameScenario
        
        self.session_id = generate_session_id()
        self.start_time = datetime.utcnow()
        
        # Get available scenarios from database
        scenarios = GameScenario.query.filter_by(
            scenario_type='rule_puzzle',
            is_active=True
        ).all()
        
        if not scenarios:
            raise Exception("No active rule puzzle scenarios found in database")
        
        # Select random scenario
        selected_scenario = random.choice(scenarios)
        self.scenario_type = selected_scenario.name.lower().replace(' ', '_')
        
        # Parse scenario configuration from database
        try:
            scenario_config = json.loads(selected_scenario.config_json) if selected_scenario.config_json else {}
        except json.JSONDecodeError:
            scenario_config = {}
        
        self.current_scenario = {
            'id': selected_scenario.id,
            'name': selected_scenario.name,
            'description': selected_scenario.description,
            'points': scenario_config.get('points', 100),
            'vehicles': scenario_config.get('vehicles', ['bil', 'fotgjenger']),
            'rules': scenario_config.get('rules', ['Følg trafikkregler']),
            'layout': scenario_config.get('layout', {}),
            'difficulty': selected_scenario.difficulty_level,
            'max_score': selected_scenario.max_score or GAME_CONFIG['max_score'],
            'time_limit': selected_scenario.time_limit_seconds or GAME_CONFIG['time_limit']
        }
        
        # Generate puzzle configuration
        scenario_config = self._generate_scenario_config()
        
        # Store session data
        self.session_data = {
            'scenario_type': self.scenario_type,
            'difficulty': self.difficulty,
            'scenario_config': scenario_config,
            'hints_used': 0,
            'moves_made': 0,
            'start_time': self.start_time.isoformat()
        }
        
        return {
            'session_id': self.session_id,
            'scenario': self.current_scenario,
            'scenario_config': scenario_config,
            'game_config': GAME_CONFIG,
            'vehicle_types': VEHICLE_TYPES,
            'difficulty': self.difficulty,
            'max_score': GAME_CONFIG['max_score'],
            'time_limit': GAME_CONFIG['time_limit']
        }
    
    def _generate_scenario_config(self) -> Dict[str, Any]:
        """Generate specific configuration for the current scenario"""
        scenario = self.current_scenario
        difficulty_config = GAME_CONFIG['difficulty_levels'][self.difficulty]
        max_vehicles = difficulty_config['max_vehicles']
        
        # Select vehicles for this scenario
        available_vehicles = scenario['vehicles']
        selected_vehicles = random.sample(
            available_vehicles, 
            min(len(available_vehicles), max_vehicles)
        )
        
        # Generate road layout based on scenario type
        road_layout = self._generate_road_layout()
        
        # Generate correct solution
        self.correct_positions = self._generate_correct_solution(selected_vehicles, road_layout)
        
        # Shuffle vehicle starting positions
        starting_positions = self._generate_starting_positions(selected_vehicles, road_layout)
        
        return {
            'vehicles': selected_vehicles,
            'road_layout': road_layout,
            'starting_positions': starting_positions,
            'rules': scenario['rules'],
            'points': scenario['points']
        }
    
    def _generate_road_layout(self) -> Dict[str, Any]:
        """Generate road layout based on scenario type"""
        if self.scenario_type == "intersection_priority":
            return {
                'type': 'intersection',
                'roads': ['north', 'south', 'east', 'west'],
                'traffic_signs': ['yield', 'stop'],
                'lanes': 2
            }
        elif self.scenario_type == "roundabout_navigation":
            return {
                'type': 'roundabout',
                'entrances': ['north', 'south', 'east', 'west'],
                'exits': ['north', 'south', 'east', 'west'],
                'lanes': 1
            }
        elif self.scenario_type == "pedestrian_crossing":
            return {
                'type': 'crossing',
                'road_direction': 'horizontal',
                'crossing_points': ['center'],
                'traffic_lights': True
            }
        elif self.scenario_type == "emergency_vehicle":
            return {
                'type': 'highway',
                'lanes': 3,
                'direction': 'horizontal',
                'shoulder': True
            }
        elif self.scenario_type == "lane_merging":
            return {
                'type': 'merge',
                'main_lanes': 2,
                'merge_lane': 1,
                'merge_point': 'right'
            }
        elif self.scenario_type == "school_zone":
            return {
                'type': 'school_zone',
                'speed_limit': 30,
                'crossing_guard': True,
                'sidewalks': True
            }
        else:
            # Default layout
            return {
                'type': 'street',
                'lanes': 2,
                'direction': 'horizontal'
            }
    
    def _generate_correct_solution(self, vehicles: List[str], layout: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate the correct solution for vehicle positioning"""
        solution = {}
        
        if self.scenario_type == "intersection_priority":
            # Sort by priority rules: emergency > right-before-left > vehicles > pedestrians
            priority_order = []
            for vehicle in vehicles:
                vehicle_info = VEHICLE_TYPES[vehicle]
                priority_order.append((vehicle, vehicle_info['priority']))
            
            priority_order.sort(key=lambda x: x[1], reverse=True)
            
            # Assign positions based on priority
            positions = ['position_1', 'position_2', 'position_3', 'position_4']
            for i, (vehicle, _) in enumerate(priority_order[:len(positions)]):
                solution[vehicle] = {
                    'position': positions[i],
                    'order': i + 1,
                    'reason': self._get_priority_reason(vehicle)
                }
                
        elif self.scenario_type == "roundabout_navigation":
            # Vehicles already in roundabout have priority
            in_roundabout = []
            entering = []
            
            for vehicle in vehicles:
                if random.choice([True, False]):  # Randomly assign some vehicles as already in roundabout
                    in_roundabout.append(vehicle)
                else:
                    entering.append(vehicle)
            
            order = 1
            for vehicle in in_roundabout:
                solution[vehicle] = {
                    'position': f'in_roundabout_{order}',
                    'order': order,
                    'reason': 'Har vikeplikt - allerede i rundkjøringen'
                }
                order += 1
                
            for vehicle in entering:
                solution[vehicle] = {
                    'position': f'entering_{order}',
                    'order': order,
                    'reason': 'Venter på ledig plass i rundkjøringen'
                }
                order += 1
                
        elif self.scenario_type == "emergency_vehicle":
            # Emergency vehicles go first, others move to side
            emergency_vehicles = [v for v in vehicles if VEHICLE_TYPES[v]['priority'] == 10]
            regular_vehicles = [v for v in vehicles if VEHICLE_TYPES[v]['priority'] < 10]
            
            order = 1
            for vehicle in emergency_vehicles:
                solution[vehicle] = {
                    'position': f'emergency_lane_{order}',
                    'order': order,
                    'reason': 'Utrykningskjøretøy har alltid vikeplikt'
                }
                order += 1
                
            for vehicle in regular_vehicles:
                solution[vehicle] = {
                    'position': f'side_lane_{order}',
                    'order': order,
                    'reason': 'Viker for utrykningskjøretøy'
                }
                order += 1
        
        else:
            # Default solution based on vehicle priority
            vehicles_with_priority = [(v, VEHICLE_TYPES[v]['priority']) for v in vehicles]
            vehicles_with_priority.sort(key=lambda x: x[1], reverse=True)
            
            for i, (vehicle, _) in enumerate(vehicles_with_priority):
                solution[vehicle] = {
                    'position': f'position_{i + 1}',
                    'order': i + 1,
                    'reason': self._get_priority_reason(vehicle)
                }
        
        return solution
    
    def _get_priority_reason(self, vehicle: str) -> str:
        """Get explanation for why a vehicle has priority"""
        vehicle_info = VEHICLE_TYPES[vehicle]
        priority = vehicle_info['priority']
        
        if priority == 10:
            return "Utrykningskjøretøy har alltid vikeplikt"
        elif priority >= 4:
            return "Fotgjengere og barn har særlig beskyttelse"
        elif priority >= 3:
            return "Myke trafikanter har vikeplikt"
        elif priority >= 2:
            return "Kollektivtrafikk har ofte vikeplikt"
        else:
            return "Følger vanlige vikepliktsregler"
    
    def _generate_starting_positions(self, vehicles: List[str], layout: Dict[str, Any]) -> Dict[str, Dict]:
        """Generate randomized starting positions for vehicles"""
        positions = {}
        available_spots = ['start_1', 'start_2', 'start_3', 'start_4', 'start_5', 'start_6', 'start_7', 'start_8']
        
        for i, vehicle in enumerate(vehicles):
            positions[vehicle] = {
                'x': random.randint(50, 750),
                'y': random.randint(50, 450),
                'spot': available_spots[i % len(available_spots)],
                'rotation': random.choice([0, 90, 180, 270])
            }
        
        return positions
    
    def process_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process game actions"""
        if action_type == "move_vehicle":
            return self._handle_vehicle_move(action_data)
        elif action_type == "request_hint":
            return self._handle_hint_request(action_data)
        elif action_type == "submit_solution":
            return self._handle_solution_submission(action_data)
        elif action_type == "reset_scenario":
            return self._handle_scenario_reset()
        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}
    
    def _handle_vehicle_move(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vehicle movement"""
        vehicle_id = action_data.get('vehicle_id')
        new_position = action_data.get('position')
        
        if not vehicle_id or not new_position:
            return {'success': False, 'error': 'Missing vehicle_id or position'}
        
        # Update vehicle position
        self.vehicle_positions[vehicle_id] = new_position
        self.moves_made += 1
        
        # Check if this placement is correct
        is_correct = self._check_placement_correctness(vehicle_id, new_position)
        
        if not is_correct:
            self.perfect_score = False
        
        return {
            'success': True,
            'vehicle_id': vehicle_id,
            'position': new_position,
            'is_correct': is_correct,
            'moves_made': self.moves_made,
            'feedback': self._get_placement_feedback(vehicle_id, new_position, is_correct)
        }
    
    def _check_placement_correctness(self, vehicle_id: str, position: Dict[str, Any]) -> bool:
        """Check if a vehicle placement is correct"""
        if vehicle_id not in self.correct_positions:
            return False
        
        correct_pos = self.correct_positions[vehicle_id]
        # Simple position matching - in a real implementation, this would be more sophisticated
        return position.get('target_zone') == correct_pos.get('position')
    
    def _get_placement_feedback(self, vehicle_id: str, position: Dict[str, Any], is_correct: bool) -> str:
        """Get feedback for vehicle placement"""
        if is_correct:
            return f"✅ {VEHICLE_TYPES[vehicle_id]['name']} er riktig plassert!"
        else:
            return f"❌ {VEHICLE_TYPES[vehicle_id]['name']} er ikke på riktig plass."
    
    def _handle_hint_request(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle hint requests"""
        self.hints_used += 1
        
        # Get hint for the scenario
        hint_text = self._generate_hint()
        
        return {
            'success': True,
            'hint': hint_text,
            'hints_used': self.hints_used,
            'penalty_points': SCORING['hint_used']
        }
    
    def _generate_hint(self) -> str:
        """Generate contextual hint for current scenario"""
        hints = {
            "intersection_priority": [
                "Husk høyre-før-venstre regelen",
                "Utrykningskjøretøy har alltid vikeplikt",
                "Fotgjengere har vikeplikt på overganger",
                "Sjekk trafikkskiltene for vikeplikt"
            ],
            "roundabout_navigation": [
                "Kjøretøy som allerede er i rundkjøringen har vikeplikt",
                "Signal til høyre når du forlater rundkjøringen",
                "Bruk innerste felt for høyresvign"
            ],
            "emergency_vehicle": [
                "Alle må vike for utrykningskjøretøy",
                "Flytt til høyre side hvis mulig",
                "Ambulanse, brannbil og politibil har høyest prioritet"
            ]
        }
        
        scenario_hints = hints.get(self.scenario_type, ["Følg vanlige trafikkregler"])
        return random.choice(scenario_hints)
    
    def _handle_solution_submission(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle solution submission and scoring"""
        submitted_positions = action_data.get('positions', {})
        
        # Calculate score
        score_result = self._calculate_score(submitted_positions)
        
        # Check if solution is completely correct
        is_complete = self._check_complete_solution(submitted_positions)
        
        return {
            'success': True,
            'is_complete': is_complete,
            'score': score_result,
            'correct_positions': self.correct_positions,
            'explanation': self._generate_solution_explanation()
        }
    
    def _check_complete_solution(self, positions: Dict[str, Any]) -> bool:
        """Check if the submitted solution is completely correct"""
        for vehicle_id, correct_pos in self.correct_positions.items():
            submitted_pos = positions.get(vehicle_id)
            if not submitted_pos or not self._check_placement_correctness(vehicle_id, submitted_pos):
                return False
        return True
    
    def _generate_solution_explanation(self) -> str:
        """Generate explanation of the correct solution"""
        explanations = []
        
        for vehicle_id, pos_info in self.correct_positions.items():
            vehicle_name = VEHICLE_TYPES[vehicle_id]['name']
            reason = pos_info['reason']
            explanations.append(f"{vehicle_name}: {reason}")
        
        return "\n".join(explanations)
    
    def _handle_scenario_reset(self) -> Dict[str, Any]:
        """Reset the current scenario"""
        self.vehicle_positions = {}
        self.moves_made = 0
        self.perfect_score = True
        
        return {
            'success': True,
            'message': 'Scenario tilbakestilt',
            'starting_positions': self.session_data.get('scenario_config', {}).get('starting_positions', {})
        }
    
    def calculate_final_score(self) -> int:
        """Calculate final score for the session"""
        base_score = SCORING['perfect_solution'] if self.perfect_score else 50
        
        # Apply penalties
        hint_penalty = self.hints_used * SCORING['hint_used']
        
        # Apply time bonus
        elapsed_time = self._get_elapsed_time()
        time_bonus = 0
        if elapsed_time < SCORING['time_bonus_threshold']:
            time_bonus = min(SCORING['speed_bonus_max'], 
                           int((SCORING['time_bonus_threshold'] - elapsed_time) / 10))
        
        # Apply difficulty multiplier
        difficulty_multiplier = GAME_CONFIG['difficulty_levels'][self.difficulty]['score_multiplier']
        
        final_score = int((base_score - hint_penalty + time_bonus) * difficulty_multiplier)
        return max(0, final_score)
    
    def _calculate_score(self, positions: Dict[str, Any]) -> GameScore:
        """Calculate detailed score breakdown"""
        correct_placements = 0
        wrong_placements = 0
        
        for vehicle_id, pos in positions.items():
            if self._check_placement_correctness(vehicle_id, pos):
                correct_placements += 1
            else:
                wrong_placements += 1
        
        base_score = correct_placements * SCORING['correct_placement']
        penalty = wrong_placements * abs(SCORING['wrong_placement']) + self.hints_used * abs(SCORING['hint_used'])
        
        # Time bonus
        elapsed_time = self._get_elapsed_time()
        time_bonus = 0
        if elapsed_time < SCORING['time_bonus_threshold']:
            time_bonus = min(SCORING['speed_bonus_max'], 
                           int((SCORING['time_bonus_threshold'] - elapsed_time) / 10))
        
        return GameScore(
            base_score=base_score,
            time_bonus=time_bonus,
            penalty=penalty,
            accuracy_bonus=SCORING['perfect_solution'] if self.perfect_score else 0
        )
    
    def complete_session(self) -> GameResult:
        """Complete the session and return results"""
        final_score = self.calculate_final_score()
        completion_time = self._get_elapsed_time()
        
        # Calculate XP
        performance_multiplier = final_score / GAME_CONFIG['max_score']
        xp_earned = self._award_xp(GAME_CONFIG['base_xp'], performance_multiplier)
        
        # Check achievements
        achievements = self._check_achievements(final_score, completion_time)
        
        result = GameResult(
            score=final_score,
            max_score=GAME_CONFIG['max_score'],
            completion_time=completion_time,
            correct_answers=len([pos for pos in self.vehicle_positions.values() 
                               if self._check_placement_correctness('temp', pos)]),
            total_questions=len(self.correct_positions),
            xp_earned=xp_earned,
            achievements_unlocked=achievements,
            performance_data={
                'scenario_type': self.scenario_type,
                'difficulty': self.difficulty,
                'hints_used': self.hints_used,
                'moves_made': self.moves_made,
                'perfect_score': self.perfect_score
            }
        )
        
        return result
    
    def _check_achievements(self, score: int, completion_time: float) -> List[str]:
        """Check and return unlocked achievements"""
        achievements = []
        
        # First puzzle solved
        achievements.append('first_puzzle_solved')
        
        # Perfect score
        if self.perfect_score and self.hints_used == 0:
            achievements.append('perfect_score')
        
        # Speed demon
        if completion_time < 60:
            achievements.append('speed_demon')
        
        # No hints used
        if self.hints_used == 0:
            achievements.append('no_hints')
        
        return achievements
    
    def get_game_config(self) -> Dict[str, Any]:
        """Get game configuration"""
        return {
            'game_id': self.game_id,
            'config': GAME_CONFIG,
            'scenarios': SCENARIO_TYPES,
            'vehicles': VEHICLE_TYPES,
            'scoring': SCORING,
            'achievements': ACHIEVEMENTS
        }
    
    def get_hint(self) -> Optional[str]:
        """Get a hint for the current situation"""
        return self._generate_hint()
    
    def validate_action(self, action_type: str, action_data: Dict[str, Any]) -> bool:
        """Validate if an action is allowed"""
        if action_type == "move_vehicle":
            return 'vehicle_id' in action_data and 'position' in action_data
        elif action_type in ["request_hint", "submit_solution", "reset_scenario"]:
            return True
        return False