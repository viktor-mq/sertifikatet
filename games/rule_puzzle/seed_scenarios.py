#!/usr/bin/env python3
"""
Database seeding script for Rule Puzzle game scenarios
Run this script to populate the database with predefined scenarios
"""

import json
from app import create_app, db
from app.models import GameScenario

# Scenario data that was previously hardcoded
SCENARIOS_DATA = [
    {
        "name": "Kryss Vikeplikt",
        "description": "Organiser kjøretøy i riktig rekkefølge gjennom krysset",
        "scenario_type": "rule_puzzle",
        "difficulty_level": 2,
        "max_score": 1000,
        "time_limit_seconds": 300,
        "template_name": "intersection",
        "order_index": 1,
        "config": {
            "points": 100,
            "vehicles": ["bil", "sykkel", "fotgjenger", "buss"],
            "rules": [
                "Høyre før venstre regel",
                "Hovedvei har vikeplikt", 
                "Fotgjengere har alltid vikeplikt på fotgjengerovergang"
            ],
            "layout": {
                "type": "intersection",
                "roads": ["north", "south", "east", "west"],
                "traffic_signs": ["yield", "stop"],
                "lanes": 2,
                "drop_zones": [
                    {"id": "north", "x": 350, "y": 100, "label": "Nord", "priority": 1},
                    {"id": "east", "x": 500, "y": 220, "label": "Øst", "priority": 2},
                    {"id": "south", "x": 350, "y": 350, "label": "Sør", "priority": 3},
                    {"id": "west", "x": 200, "y": 220, "label": "Vest", "priority": 4},
                    {"id": "center", "x": 350, "y": 220, "label": "Sentrum", "priority": 5}
                ]
            }
        }
    },
    {
        "name": "Rundkjøring",
        "description": "Lei kjøretøy gjennom rundkjøringen i riktig rekkefølge",
        "scenario_type": "rule_puzzle",
        "difficulty_level": 3,
        "max_score": 1200,
        "time_limit_seconds": 360,
        "template_name": "roundabout",
        "order_index": 2,
        "config": {
            "points": 120,
            "vehicles": ["bil", "lastebil", "motorsykkel"],
            "rules": [
                "Kjøretøy i rundkjøringen har vikeplikt",
                "Signal til høyre når du forlater rundkjøringen",
                "Bruk innerste felt ved høyresvign"
            ],
            "layout": {
                "type": "roundabout",
                "entrances": ["north", "south", "east", "west"],
                "exits": ["north", "south", "east", "west"],
                "lanes": 1,
                "drop_zones": [
                    {"id": "entrance_north", "x": 350, "y": 50, "label": "Inngang Nord"},
                    {"id": "entrance_east", "x": 550, "y": 220, "label": "Inngang Øst"},
                    {"id": "entrance_south", "x": 350, "y": 390, "label": "Inngang Sør"},
                    {"id": "entrance_west", "x": 150, "y": 220, "label": "Inngang Vest"},
                    {"id": "in_roundabout_1", "x": 300, "y": 170, "label": "I rundkjøring"},
                    {"id": "in_roundabout_2", "x": 400, "y": 270, "label": "I rundkjøring"}
                ]
            }
        }
    },
    {
        "name": "Fotgjengerovergang",
        "description": "Sikre at fotgjengere krysser trygt",
        "scenario_type": "rule_puzzle", 
        "difficulty_level": 1,
        "max_score": 800,
        "time_limit_seconds": 240,
        "template_name": "crossing",
        "order_index": 3,
        "config": {
            "points": 90,
            "vehicles": ["bil", "fotgjenger", "barnevogn"],
            "rules": [
                "Stopp for fotgjengere på overgangen",
                "Gi signal før du stopper",
                "Vent til fotgjengeren er helt over"
            ],
            "layout": {
                "type": "crossing",
                "road_direction": "horizontal",
                "crossing_points": ["center"],
                "traffic_lights": True,
                "drop_zones": [
                    {"id": "before_crossing", "x": 200, "y": 220, "label": "Før overgang"},
                    {"id": "crossing_wait", "x": 320, "y": 220, "label": "Venter"},
                    {"id": "crossing_north", "x": 350, "y": 150, "label": "Krysser nord"},
                    {"id": "crossing_south", "x": 350, "y": 290, "label": "Krysser sør"},
                    {"id": "after_crossing", "x": 500, "y": 220, "label": "Etter overgang"}
                ]
            }
        }
    },
    {
        "name": "Utrykningskjøretøy",
        "description": "Rydd vei for utrykningskjøretøy",
        "scenario_type": "rule_puzzle",
        "difficulty_level": 3,
        "max_score": 1500,
        "time_limit_seconds": 300,
        "template_name": "emergency",
        "order_index": 4,
        "config": {
            "points": 150,
            "vehicles": ["bil", "ambulanse", "brannbil", "politibil"],
            "rules": [
                "Alle må vike for utrykningskjøretøy",
                "Flytt til høyre side av veien",
                "Stopp hvis nødvendig"
            ],
            "layout": {
                "type": "highway",
                "lanes": 3,
                "direction": "horizontal",
                "shoulder": True,
                "drop_zones": [
                    {"id": "emergency_lane", "x": 350, "y": 120, "label": "Utrykningsfelt"},
                    {"id": "lane_1", "x": 350, "y": 180, "label": "Felt 1"},
                    {"id": "lane_2", "x": 350, "y": 240, "label": "Felt 2"},
                    {"id": "lane_3", "x": 350, "y": 300, "label": "Felt 3"},
                    {"id": "shoulder", "x": 350, "y": 360, "label": "Skulder"}
                ]
            }
        }
    },
    {
        "name": "Filterfletning",
        "description": "Flett inn i trafikken på en trygg måte",
        "scenario_type": "rule_puzzle",
        "difficulty_level": 2,
        "max_score": 1100,
        "time_limit_seconds": 300,
        "template_name": "merge",
        "order_index": 5,
        "config": {
            "points": 110,
            "vehicles": ["bil", "motorsykkel", "lastebil"],
            "rules": [
                "Gi signal i god tid",
                "Tilpass hastighet til trafikken",
                "Bruk sammenfletningsregelen"
            ],
            "layout": {
                "type": "merge",
                "main_lanes": 2,
                "merge_lane": 1,
                "merge_point": "right",
                "drop_zones": [
                    {"id": "main_lane_1", "x": 250, "y": 180, "label": "Hovedfelt 1"},
                    {"id": "main_lane_2", "x": 250, "y": 240, "label": "Hovedfelt 2"},
                    {"id": "merge_lane", "x": 450, "y": 280, "label": "Flettefelt"},
                    {"id": "merged_1", "x": 500, "y": 180, "label": "Etter fletning 1"},
                    {"id": "merged_2", "x": 500, "y": 240, "label": "Etter fletning 2"}
                ]
            }
        }
    },
    {
        "name": "Skolesone",
        "description": "Naviger trygt gjennom skolesonen",
        "scenario_type": "rule_puzzle",
        "difficulty_level": 2,
        "max_score": 1000,
        "time_limit_seconds": 300,
        "template_name": "school_zone",
        "order_index": 6,
        "config": {
            "points": 100,
            "vehicles": ["bil", "barn", "syklist", "skolepatrulje"],
            "rules": [
                "Redusert hastighet i skolesoner",
                "Ekstra oppmerksomhet på barn",
                "Stopp for skolepatrulje"
            ],
            "layout": {
                "type": "school_zone",
                "speed_limit": 30,
                "crossing_guard": True,
                "sidewalks": True,
                "drop_zones": [
                    {"id": "approaching", "x": 150, "y": 220, "label": "Nærmer seg"},
                    {"id": "school_zone", "x": 300, "y": 220, "label": "I skolesone"},
                    {"id": "crossing", "x": 400, "y": 220, "label": "Ved overgang"},
                    {"id": "sidewalk_north", "x": 350, "y": 150, "label": "Fortau nord"},
                    {"id": "sidewalk_south", "x": 350, "y": 290, "label": "Fortau sør"}
                ]
            }
        }
    }
]

def seed_scenarios():
    """Seed the database with rule puzzle scenarios"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Seeding rule puzzle scenarios...")
        
        # Remove existing rule_puzzle scenarios
        existing_scenarios = GameScenario.query.filter_by(scenario_type='rule_puzzle').all()
        for scenario in existing_scenarios:
            db.session.delete(scenario)
        
        # Add new scenarios
        for scenario_data in SCENARIOS_DATA:
            config = scenario_data.pop('config')
            scenario = GameScenario(
                **scenario_data,
                config_json=json.dumps(config, ensure_ascii=False),
                is_active=True,
                min_level_required=1,
                is_premium=False
            )
            db.session.add(scenario)
            print(f"  ✅ Added scenario: {scenario.name}")
        
        db.session.commit()
        print(f"🎉 Successfully seeded {len(SCENARIOS_DATA)} rule puzzle scenarios!")

if __name__ == "__main__":
    seed_scenarios()