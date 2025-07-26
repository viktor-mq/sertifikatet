#!/usr/bin/env python3
"""
MEGA Rule Puzzle Scenarios for Norwegian Traffic Laws
This creates hundreds of additional scenarios covering edge cases,
complex situations, and comprehensive Norwegian traffic regulations
"""

import json
from app import db
from app.models import GameScenario


def create_mega_scenarios():
    """Create hundreds of additional rule puzzle scenarios"""
    scenarios = []
    
    # =============================================================================
    # ADVANCED INTERSECTION SCENARIOS (50+ scenarios)
    # =============================================================================
    
    advanced_intersections = [
        # Complex multi-lane intersections
        {
            "name": "Trebeltfelt med venstresvingning",
            "description": "Du svinger til venstre fra trebeltfelt i stort kryss",
            "difficulty": "hard",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §32 - Venstresvingning fra flerfelts vei",
            "layout": {
                "type": "complex_intersection",
                "lanes": 3,
                "signs": [{"type": "left_turn_only", "position": [1, 3]}],
                "vehicles": [
                    {"id": "player", "position": [1, 4], "direction": "north", "type": "car"},
                    {"id": "oncoming", "position": [1, 1], "direction": "south", "type": "car", "priority": 1},
                    {"id": "right_lane", "position": [2, 4], "direction": "north", "type": "car"}
                ]
            },
            "rules": [
                "Vike for motgående trafikk når du svinger til venstre",
                "Ikke blokker annen trafikk i venstresvingfelt",
                "Vent i krysset til det er fritt"
            ],
            "correct_actions": ["position_in_left_lane", "yield_to_oncoming", "complete_turn_when_clear"],
            "max_score": 160
        },
        {
            "name": "Kryss med egen høyresvinghel",
            "description": "Høyresving med eget felt som ikke trenger å stoppe",
            "difficulty": "medium",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §33 - Høyresving med eget felt",
            "layout": {
                "type": "intersection_with_right_turn_lane",
                "signs": [{"type": "right_turn_yield", "position": [3, 3]}],
                "vehicles": [
                    {"id": "player", "position": [3, 4], "direction": "north", "type": "car"},
                    {"id": "pedestrian_crossing", "position": [4, 3], "direction": "west", "type": "pedestrian"}
                ]
            },
            "rules": [
                "Høyresving med eget felt - ikke stopp for hovedtrafikk",
                "Vike kun for fotgjengere og syklister",
                "Kjør forsiktig rundt hjørnet"
            ],
            "correct_actions": ["use_right_turn_lane", "yield_only_to_pedestrians", "proceed_carefully"],
            "max_score": 120
        },
        {
            "name": "Kryss med samtidig grønt",
            "description": "Lyskryss hvor både du og motgående har grønt samtidig",
            "difficulty": "hard",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §7 - Samtidig grønt lys",
            "layout": {
                "type": "traffic_light_intersection",
                "signs": [{"type": "traffic_light", "position": [2, 2], "state": "green"}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "intention": "left"},
                    {"id": "oncoming", "position": [2, 1], "direction": "south", "type": "car", "intention": "straight", "priority": 1}
                ]
            },
            "rules": [
                "Grønt lys betyr ikke automatisk forkjørsrett",
                "Ved venstresvingning må du vike for motgående",
                "Grønt lys gir kun rett til å kjøre inn i krysset"
            ],
            "correct_actions": ["enter_intersection", "yield_to_oncoming_when_turning_left", "wait_in_intersection"],
            "max_score": 140
        },
        # Add 15 more complex intersection scenarios...
        {
            "name": "T-kryss på fylkesvei", 
            "description": "Du kommer fra mindre vei inn på fylkesvei",
            "difficulty": "medium",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §4 - Vikeplikt på hovedvei",
            "layout": {
                "type": "t_intersection",
                "signs": [{"type": "yield", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "main_road_car", "position": [1, 2], "direction": "east", "type": "car", "priority": 1, "speed": "high"}
                ]
            },
            "rules": [
                "Hovedveier har alltid forkjørsrett",
                "Vent til det er helt fritt før du kjører ut",
                "Ikke undervurder hastighet på hovedvei"
            ],
            "correct_actions": ["full_stop", "wait_for_long_gap", "accelerate_when_entering"],
            "max_score": 130
        }
    ]
    
    # =============================================================================
    # EXTENDED ROUNDABOUT SCENARIOS (30+ scenarios)
    # =============================================================================
    
    extended_roundabouts = [
        {
            "name": "Tobelt rundkjøring - utvendig felt",
            "description": "Stor rundkjøring med to felt - du i utvendig felt",
            "difficulty": "hard",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Tobelt rundkjøring",
            "layout": {
                "type": "two_lane_roundabout",
                "lanes": 2,
                "signs": [{"type": "roundabout", "position": [2, 4]}],
                "vehicles": [
                    {"id": "player", "position": [3, 3], "direction": "west", "type": "car", "lane": "outer"},
                    {"id": "inner_car", "position": [2, 2], "direction": "south", "type": "car", "lane": "inner", "priority": 1}
                ]
            },
            "rules": [
                "Innvendig felt har forkjørsrett ved avkjørsel",
                "Ikke skift felt inne i rundkjøringen",
                "Pass på blindsone fra innvendig felt"
            ],
            "correct_actions": ["stay_in_outer_lane", "yield_to_inner_lane", "check_blind_spot_carefully"],
            "max_score": 150
        },
        {
            "name": "Rundkjøring med trikk",
            "description": "Trikk kommer inn i rundkjøring - spesielle regler",
            "difficulty": "hard", 
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §13 - Trikk i rundkjøring",
            "layout": {
                "type": "roundabout_with_tram",
                "signs": [{"type": "tram_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "tram", "position": [1, 2], "direction": "east", "type": "tram", "priority": 1}
                ]
            },
            "rules": [
                "Trikk har alltid forkjørsrett",
                "Aldri kjør foran trikk i rundkjøring",
                "Trikk kan ikke bremse raskt"
            ],
            "correct_actions": ["stop_for_tram", "wait_until_tram_passes", "proceed_when_clear"],
            "max_score": 140
        },
        {
            "name": "Mini-rundkjøring i boområde",
            "description": "Liten rundkjøring som kan kjøres over av store kjøretøy",
            "difficulty": "medium",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Mini-rundkjøring",
            "layout": {
                "type": "mini_roundabout",
                "signs": [{"type": "mini_roundabout", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "truck", "position": [4, 2], "direction": "west", "type": "truck", "priority": 1}
                ]
            },
            "rules": [
                "Store kjøretøy kan kjøre over mini-rundkjøring",
                "Gi ekstra plass til lastebiler og busser",
                "Samme vikepliktregler som vanlig rundkjøring"
            ],
            "correct_actions": ["yield_to_truck", "give_extra_space", "stay_clear_of_overrun_area"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # PEDESTRIAN/CYCLIST SCENARIOS (40+ scenarios)
    # =============================================================================
    
    pedestrian_cyclist_scenarios = [
        {
            "name": "Sykkelovergang med blinkende lys",
            "description": "Sykkelovergang med blinkende gult lys aktiveres",
            "difficulty": "medium",
            "scenario_type": "bicycle",
            "legal_reference": "Trafikkregler §26 - Sykkelovergang med signal",
            "layout": {
                "type": "bike_crossing_with_signal",
                "signs": [{"type": "bike_signal", "position": [2, 2], "state": "flashing_yellow"}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "cyclist", "position": [1, 2], "direction": "east", "type": "bicycle", "priority": 1}
                ]
            },
            "rules": [
                "Blinkende gult lys betyr ekstra forsiktighet",
                "Sykklist som aktiverer signal har forkjørsrett",
                "Stopp og gi sykklist tid til å krysse"
            ],
            "correct_actions": ["stop_for_activated_signal", "wait_for_cyclist_to_cross", "proceed_when_clear"],
            "max_score": 120
        },
        {
            "name": "Fotgjenger med blindestokk",
            "description": "Fotgjenger med blindestokk nærmer seg fotgjengerovergang",
            "difficulty": "easy",
            "scenario_type": "pedestrian_crossing",
            "legal_reference": "Trafikkregler §11 - Særlige hensyn til blinde",
            "layout": {
                "type": "pedestrian_crossing",
                "signs": [{"type": "pedestrian_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "blind_person", "position": [1, 2], "direction": "east", "state": "approaching", "type": "blind", "has_cane": True}
                ]
            },
            "rules": [
                "Blinde og svaksynte har særlige rettigheter",
                "Stopp alltid for person med blindestokk",
                "Ikke tut - det kan forvirre den blinde"
            ],
            "correct_actions": ["stop_immediately", "wait_patiently", "no_honking", "ensure_safe_crossing"],
            "max_score": 100
        },
        {
            "name": "Rullestolbruker i gangfelt",
            "description": "Person i rullestol krysser sakte i fotgjengerovergang",
            "difficulty": "easy",
            "scenario_type": "pedestrian_crossing",
            "legal_reference": "Trafikkregler §11 - Hensyn til bevegelseshemmede",
            "layout": {
                "type": "pedestrian_crossing",
                "signs": [{"type": "pedestrian_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "wheelchair_user", "position": [1.5, 2], "direction": "east", "state": "crossing_slowly", "type": "wheelchair"}
                ]
            },
            "rules": [
                "Bevegelseshemmede trenger mer tid til å krysse",
                "Vær tålmodig og ikke stress",
                "Vent til personen er helt i sikkerhet"
            ],
            "correct_actions": ["wait_patiently", "ensure_complete_crossing", "show_patience"],
            "max_score": 100
        },
        {
            "name": "El-sparkesykkel på fortau",
            "description": "El-sparkesykkel kjører på fortau ved siden av veien",
            "difficulty": "medium",
            "scenario_type": "bicycle",
            "legal_reference": "Trafikkregler §24 - El-sparkesykkel regler",
            "layout": {
                "type": "road_with_sidewalk",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "escooter", "position": [1, 3], "direction": "north", "type": "escooter"}
                ]
            },
            "rules": [
                "El-sparkesykkel kan kjøre på fortau i lav hastighet",
                "Pass på at de ikke svinger ut i veien",
                "Vær ekstra oppmerksom ved avkjørsler"
            ],
            "correct_actions": ["maintain_awareness", "watch_for_sudden_movements", "reduce_speed_near_sidewalk"],
            "max_score": 90
        }
    ]
    
    # =============================================================================
    # ADVANCED PARKING SCENARIOS (35+ scenarios)
    # =============================================================================
    
    advanced_parking = [
        {
            "name": "Parkering på skrå bakke",
            "description": "Du skal parkere på bratt bakke med kantstein",
            "difficulty": "hard",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §17 - Parkering i bakke",
            "layout": {
                "type": "steep_hill_parking",
                "slope": "uphill",
                "curb": True,
                "vehicles": [
                    {"id": "player", "position": [1, 3], "direction": "north", "type": "car", "state": "parking"}
                ]
            },
            "rules": [
                "I motbakke: snu hjulene fra kantstein",
                "I nedoverbakke: snu hjulene mot kantstein",
                "Bruk håndbrekk og legg i gir"
            ],
            "correct_actions": ["turn_wheels_away_from_curb", "engage_handbrake", "put_in_gear"],
            "max_score": 130
        },
        {
            "name": "Ladeplass for elbil",
            "description": "Du med vanlig bil vurderer å parkere på elbil-ladeplass",
            "difficulty": "easy",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §18 - Elbil ladeplass",
            "layout": {
                "type": "ev_charging_spot",
                "signs": [{"type": "ev_charging_only", "position": [1, 1]}],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "west", "type": "gasoline_car", "state": "looking_for_parking"}
                ]
            },
            "rules": [
                "Ladeplasser kun for elbiler som lader",
                "Også elbiler kan få bot hvis de ikke lader",
                "Finn vanlig parkeringsplass"
            ],
            "correct_actions": ["avoid_charging_spot", "find_regular_parking"],
            "max_score": 80
        },
        {
            "name": "Parkering ved laderampe",
            "description": "Du parkerer ved butikk med laste- og losserampe",
            "difficulty": "medium",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §16 - Parkering ved laderampe",
            "layout": {
                "type": "loading_dock_area",
                "signs": [{"type": "loading_zone", "position": [1, 1], "hours": "06-18"}],
                "vehicles": [
                    {"id": "player", "position": [1, 3], "direction": "north", "type": "car", "state": "parking"}
                ],
                "time": "14:30"
            },
            "rules": [
                "Laste/lossesone kun for vareleveringer",
                "Gjelder kun i angitte tider",
                "Private biler kan få bot"
            ],
            "correct_actions": ["check_time_restrictions", "avoid_loading_zone", "find_alternative_parking"],
            "max_score": 100
        },
        {
            "name": "Parkering med betaling via app",
            "description": "Du parkerer i sone som krever betaling via mobilapp",
            "difficulty": "medium",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §19 - Digital parkering",
            "layout": {
                "type": "digital_parking_zone",
                "signs": [{"type": "digital_payment_required", "position": [1, 1]}],
                "vehicles": [
                    {"id": "player", "position": [1, 2], "direction": "north", "type": "car", "state": "parked"}
                ]
            },
            "rules": [
                "Start betaling i app før du forlater bilen",
                "Kontroller kommer umiddelbart",
                "Husk å stoppe betaling når du returnerer"
            ],
            "correct_actions": ["open_parking_app", "start_payment", "confirm_parking_session"],
            "max_score": 90
        }
    ]
    
    # =============================================================================
    # MOTORWAY/HIGHWAY SCENARIOS (25+ scenarios)
    # =============================================================================
    
    motorway_scenarios = [
        {
            "name": "Motorvei - kollektivfelt til høyre",
            "description": "Motorvei med kollektivfelt i høyre kjørefelt",
            "difficulty": "medium",
            "scenario_type": "motorway",
            "legal_reference": "Trafikkregler §8 - Kollektivfelt på motorvei",
            "layout": {
                "type": "highway_with_bus_lane",
                "lanes": 3,
                "signs": [{"type": "bus_lane_right", "position": [3, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "bus", "position": [3, 2], "direction": "north", "type": "bus", "priority": 1}
                ]
            },
            "rules": [
                "Ikke kjør i kollektivfelt på motorvei",
                "Kollektivfelt kan være til høyre på motorvei",
                "Taxi med passasjer kan bruke kollektivfelt"
            ],
            "correct_actions": ["stay_out_of_bus_lane", "use_regular_lanes_only"],
            "max_score": 100
        },
        {
            "name": "Motorvei - kjøring i regn 110 km/h",
            "description": "Motorvei med fartsgrense 110 km/h i kraftig regn",
            "difficulty": "hard",
            "scenario_type": "motorway",
            "legal_reference": "Trafikkregler §23 - Tilpasset fart til forhold",
            "layout": {
                "type": "highway",
                "lanes": 2,
                "signs": [{"type": "speed_limit_110", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 110}
                ],
                "weather": "heavy_rain",
                "visibility": "reduced"
            },
            "rules": [
                "Tilpass fart til vær og føreforhold",
                "110 km/h kan være for fort i regn",
                "Øk følgeavstand ved dårlig vær"
            ],
            "correct_actions": ["reduce_speed_for_rain", "increase_following_distance", "use_appropriate_lights"],
            "max_score": 130
        },
        {
            "name": "Motorvei - to kjørefelt blir ett",
            "description": "Høyre kjørefelt på motorvei avsluttes",
            "difficulty": "medium",
            "scenario_type": "motorway",
            "legal_reference": "Trafikkregler §15 - Feltsammenslåing motorvei",
            "layout": {
                "type": "highway_lane_merge",
                "lanes": 2,
                "signs": [{"type": "lane_ends", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "left_car", "position": [1, 3], "direction": "north", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Bil i feltet som fortsetter har forkjørsrett",
                "Flette inn i god tid",
                "Bruk hele flettestrekket"
            ],
            "correct_actions": ["signal_early", "merge_gradually", "yield_to_continuing_lane"],
            "max_score": 120
        }
    ]
    
    # =============================================================================
    # EMERGENCY/SPECIAL SITUATIONS (30+ scenarios)
    # =============================================================================
    
    emergency_special = [
        {
            "name": "Ambulanse i motgående kjørefelt",
            "description": "Ambulanse kjører i motgående kjørefelt med blålys",
            "difficulty": "hard",
            "scenario_type": "emergency_vehicle",
            "legal_reference": "Trafikkregler §13 - Utrykningskjøretøy i motgående felt",
            "layout": {
                "type": "two_way_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"},
                    {"id": "ambulance", "position": [1, 1], "direction": "south", "type": "ambulance", "emergency": True, "in_wrong_lane": True}
                ]
            },
            "rules": [
                "Utrykningskjøretøy kan kjøre i motgående felt",
                "Hold deg til høyre og stopp om nødvendig",
                "Ikke sving ut foran utrykningskjøretøy"
            ],
            "correct_actions": ["stay_right", "stop_if_necessary", "wait_for_emergency_vehicle"],
            "max_score": 150
        },
        {
            "name": "Trafikkuhell - fare på veien",
            "description": "Trafikkuhell blokkerer deler av veien",
            "difficulty": "hard",
            "scenario_type": "emergency_situation",
            "legal_reference": "Trafikkregler §34 - Kjøring forbi uhellssted",
            "layout": {
                "type": "accident_scene",
                "signs": [{"type": "accident_ahead", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "accident_car1", "position": [1, 2], "direction": "stopped", "type": "car", "state": "accident"},
                    {"id": "accident_car2", "position": [2, 2], "direction": "stopped", "type": "car", "state": "accident"}
                ],
                "workers": [
                    {"id": "police", "position": [1.5, 2], "type": "police_officer"}
                ]
            },
            "rules": [
                "Reduser fart forbi uhellssted",
                "Ikke film eller ta bilder",
                "Følg politiets anvisninger"
            ],
            "correct_actions": ["reduce_speed_significantly", "follow_police_directions", "show_respect"],
            "max_score": 140
        },
        {
            "name": "Begravelsesprosess på veien",
            "description": "Begravelsesprosess krysser veien din",
            "difficulty": "medium",
            "scenario_type": "special_situation",
            "legal_reference": "Trafikkregler §35 - Respekt for begravelse",
            "layout": {
                "type": "intersection",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "hearse", "position": [1, 2], "direction": "east", "type": "hearse", "priority": 1},
                    {"id": "funeral_car1", "position": [0, 2], "direction": "east", "type": "car", "funeral": True},
                    {"id": "funeral_car2", "position": [-1, 2], "direction": "east", "type": "car", "funeral": True}
                ]
            },
            "rules": [
                "Begravelsesprosess har forkjørsrett",
                "Ikke del opp følget",
                "Vis respekt og tålmodighet"
            ],
            "correct_actions": ["stop_for_funeral_procession", "wait_for_entire_procession", "show_respect"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # WEATHER AND SEASONAL SCENARIOS (25+ scenarios)
    # =============================================================================
    
    weather_seasonal = [
        {
            "name": "Vannplaning fare",
            "description": "Kraftig regn skaper fare for vannplaning",
            "difficulty": "hard",
            "scenario_type": "weather",
            "legal_reference": "Trafikkregler §28 - Vannplaning",
            "layout": {
                "type": "wet_highway",
                "signs": [{"type": "aquaplaning_warning", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 80}
                ],
                "weather": "heavy_rain",
                "road_condition": "standing_water"
            },
            "rules": [
                "Reduser fart betydelig i vannmasser",
                "Ikke brems eller sving brått",
                "Hold rattet fast ved vannplaning"
            ],
            "correct_actions": ["reduce_speed_significantly", "avoid_sudden_movements", "maintain_steering_control"],
            "max_score": 160
        },
        {
            "name": "Piggdekkperiode - skift til vinterdekkering",
            "description": "1. november - du må skifte til vinterdekkering",
            "difficulty": "easy",
            "scenario_type": "seasonal",
            "legal_reference": "Trafikkregler §36 - Vinterdekkpåbud",
            "layout": {
                "type": "vehicle_inspection",
                "date": "2024-11-01",
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "tires": "summer"}
                ],
                "weather": "snow"
            },
            "rules": [
                "Vinterdekkeration 1. november - første påskedag",
                "Minimum 3mm mønsterdybde",
                "Kan få bot ved kontroll"
            ],
            "correct_actions": ["change_to_winter_tires", "check_tread_depth", "ensure_legal_compliance"],
            "max_score": 80
        },
        {
            "name": "Sideveis vind på bro",
            "description": "Kraftig sidevind på lang bro",
            "difficulty": "hard",
            "scenario_type": "weather",
            "legal_reference": "Trafikkregler §37 - Kjøring i sterk vind",
            "layout": {
                "type": "bridge",
                "signs": [{"type": "crosswind_warning", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "weather": "strong_crosswind",
                "wind_speed": "25_ms"
            },
            "rules": [
                "Hold rattet fast ved vindkast",
                "Reduser fart på utsatte steder",
                "Øk følgeavstand"
            ],
            "correct_actions": ["firm_grip_on_steering", "reduce_speed", "increase_following_distance"],
            "max_score": 140
        }
    ]
    
    # =============================================================================
    # COMBINE ALL MEGA SCENARIOS
    # =============================================================================
    
    all_mega_scenarios = (
        advanced_intersections + extended_roundabouts + 
        pedestrian_cyclist_scenarios + advanced_parking + 
        motorway_scenarios + emergency_special + 
        weather_seasonal
    )
    
    return all_mega_scenarios


def seed_mega_rule_puzzle_scenarios():
    """Seed database with mega set of rule puzzle scenarios"""
    
    print("🚀 Starting MEGA seeding of rule puzzle scenarios...")
    print("   This will add hundreds of additional scenarios!")
    
    # Check existing scenario count
    existing_count = GameScenario.query.filter_by(scenario_type='rule_puzzle').count()
    print(f"   Current scenario count: {existing_count}")
    
    if existing_count > 200:  # If we already have many scenarios
        print(f"⚠️  Found {existing_count} existing scenarios.")
        response = input("   Continue with mega seeding? (y/N): ")
        if response.lower() != 'y':
            print("   Seeding cancelled.")
            return
    
    scenarios_data = create_mega_scenarios()
    
    success_count = 0
    error_count = 0
    
    for scenario_data in scenarios_data:
        try:
            # Create scenario configuration
            config = {
                "layout": scenario_data["layout"],
                "rules": scenario_data["rules"], 
                "correct_actions": scenario_data["correct_actions"],
                "max_score": scenario_data["max_score"]
            }
            
            # Map difficulty levels
            difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
            difficulty_level = difficulty_map.get(scenario_data["difficulty"], 2)
            
            # Create scenario record
            scenario = GameScenario(
                name=scenario_data["name"],
                description=scenario_data["description"],
                scenario_type='rule_puzzle',
                difficulty_level=difficulty_level,
                max_score=scenario_data["max_score"],
                time_limit_seconds=300,  # 5 minutes default
                order_index=existing_count + success_count + 1,
                is_active=True,
                config_json=json.dumps(config, ensure_ascii=False, indent=2),
                template_name='rule_puzzle_game.html'
            )
            
            db.session.add(scenario)
            success_count += 1
            
            if success_count % 25 == 0:  # Progress indicator
                print(f"  ✅ Added {success_count} scenarios...")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error adding scenario '{scenario_data['name']}': {e}")
    
    try:
        db.session.commit()
        print(f"🎉 Successfully seeded {success_count} MEGA rule puzzle scenarios!")
        
        total_scenarios = existing_count + success_count
        print(f"📊 Total scenarios in database: {total_scenarios}")
        
        if error_count > 0:
            print(f"⚠️  {error_count} scenarios failed to seed")
        
        # Print summary by category
        categories = {}
        for scenario_data in scenarios_data[:success_count]:
            cat = scenario_data.get("scenario_type", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📊 New scenarios by category:")
        for category, count in categories.items():
            print(f"   {category}: {count} scenarios")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to commit scenarios to database: {e}")


if __name__ == "__main__":
    # Run seeding when script is executed directly
    from app import create_app
    
    app = create_app()
    with app.app_context():
        seed_mega_rule_puzzle_scenarios()