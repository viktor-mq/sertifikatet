#!/usr/bin/env python3
"""
Comprehensive Rule Puzzle Scenarios for Norwegian Traffic Laws
Based on current Norwegian traffic regulations (2024-2025)
Covers all major traffic situations with accurate legal requirements
"""

import json
from app import db
from app.models import GameScenario


def create_comprehensive_scenarios():
    """Create comprehensive set of rule puzzle scenarios based on Norwegian traffic laws"""
    scenarios = []
    
    # =============================================================================
    # INTERSECTION SCENARIOS (Kryss) - Norwegian Right-of-Way Rules
    # =============================================================================
    
    # Basic right-of-way scenarios
    intersection_scenarios = [
        {
            "name": "Kryss uten skilt - høyreregel",
            "description": "I et kryss uten trafikkskilt må du vike for trafikk fra høyre",
            "difficulty": "easy",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §3 - Vikeplikt fra høyre",
            "layout": {
                "type": "four_way_intersection",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "right_car", "position": [4, 2], "direction": "west", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Du må vike for bil som kommer fra høyre",
                "Vent til krysset er fritt før du kjører"
            ],
            "correct_actions": ["wait", "yield"],
            "max_score": 100
        },
        {
            "name": "Kryss med vikepliktskilt",
            "description": "Du har vikepliktskilt og må vike for all annen trafikk",
            "difficulty": "easy", 
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §5 - Vikepliktskilt",
            "layout": {
                "type": "four_way_intersection",
                "signs": [{"type": "yield", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "crossing_car", "position": [1, 2], "direction": "east", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Vikepliktskilt betyr at du må vike for all annen trafikk",
                "Stopp og vurder før du kjører inn i krysset"
            ],
            "correct_actions": ["stop", "yield", "proceed_when_clear"],
            "max_score": 100
        },
        {
            "name": "Kryss med stoppskilt",
            "description": "Du har stoppskilt og må stoppe helt før krysset",
            "difficulty": "medium",
            "scenario_type": "intersection", 
            "legal_reference": "Trafikkregler §6 - Stoppskilt",
            "layout": {
                "type": "four_way_intersection",
                "signs": [{"type": "stop", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "crossing_car", "position": [1, 2], "direction": "east", "type": "car"}
                ]
            },
            "rules": [
                "Stoppskilt krever fullstendig stopp",
                "Du må vike for all annen trafikk",
                "Kjør først når krysset er fritt"
            ],
            "correct_actions": ["full_stop", "yield", "proceed_when_clear"],
            "max_score": 120
        },
        {
            "name": "Prioritetsvei - du har forkjørsrett",
            "description": "Du kjører på prioritetsvei og har forkjørsrett",
            "difficulty": "easy",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §4 - Prioritetsvei",
            "layout": {
                "type": "four_way_intersection", 
                "signs": [{"type": "priority_road", "position": [2, 1]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "priority": 1},
                    {"id": "yield_car", "position": [4, 2], "direction": "west", "type": "car"}
                ]
            },
            "rules": [
                "Prioritetsvei gir forkjørsrett",
                "Andre må vike for deg",
                "Kjør forsiktig selv om du har forkjørsrett"
            ],
            "correct_actions": ["proceed", "maintain_speed"],
            "max_score": 80
        }
    ]
    
    # Complex intersection scenarios
    complex_intersections = [
        {
            "name": "T-kryss med kollektivfelt",
            "description": "T-kryss hvor du skal svinge fra kollektivfelt",
            "difficulty": "hard",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §8 - Kollektivfelt",
            "layout": {
                "type": "t_intersection",
                "signs": [{"type": "bus_lane", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "bus", "position": [2, 1], "direction": "south", "type": "bus", "priority": 1}
                ]
            },
            "rules": [
                "Du må ikke hindre buss i kollektivfelt",
                "Vike for buss selv om du har forkjørsrett ellers",
                "Sving forsiktig ut av kollektivfeltet"
            ],
            "correct_actions": ["yield_to_bus", "exit_bus_lane", "turn"],
            "max_score": 150
        },
        {
            "name": "Lysregulert kryss - gult lys",
            "description": "Du nærmer deg lysregulert kryss med gult lys",
            "difficulty": "medium",
            "scenario_type": "intersection",
            "legal_reference": "Trafikkregler §7 - Lyskryss",
            "layout": {
                "type": "four_way_intersection",
                "signs": [{"type": "traffic_light", "position": [2, 2], "state": "yellow"}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": "medium"}
                ]
            },
            "rules": [
                "Gult lys betyr stopp hvis mulig",
                "Hvis du ikke kan stoppe trygt, kjør forsiktig gjennom",
                "Forbered deg på rødt lys"
            ],
            "correct_actions": ["evaluate_stopping", "proceed_if_unsafe_to_stop"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # ROUNDABOUT SCENARIOS (Rundkjøring) - Norwegian Roundabout Rules  
    # =============================================================================
    
    roundabout_scenarios = [
        {
            "name": "Rundkjøring - inn i rundkjøring",
            "description": "Du skal inn i rundkjøring og må vike for trafikk i rundkjøringen",
            "difficulty": "medium",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Rundkjøring",
            "layout": {
                "type": "roundabout",
                "signs": [{"type": "roundabout", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "roundabout_car", "position": [3, 2], "direction": "west", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Vike for all trafikk som allerede er i rundkjøringen",
                "Kjør mot klokka i rundkjøringen",
                "Bruk blinklys riktig"
            ],
            "correct_actions": ["yield_to_traffic_in_roundabout", "enter_when_clear", "signal_properly"],
            "max_score": 120
        },
        {
            "name": "Rundkjøring - høyre av første avkjørsel",
            "description": "Du skal til høyre i første avkjørsel fra rundkjøring",
            "difficulty": "easy",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Blinklys i rundkjøring",
            "layout": {
                "type": "roundabout",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [3, 2], "direction": "west", "type": "car"}
                ]
            },
            "rules": [
                "Blink høyre før du går inn i rundkjøringen",
                "Hold høyre blinklys til du forlater rundkjøringen",
                "Sjekk blindsonen før avkjørsel"
            ],
            "correct_actions": ["signal_right_before_entering", "maintain_signal", "check_blind_spot", "exit"],
            "max_score": 100
        },
        {
            "name": "Rundkjøring - rett frem (andre avkjørsel)",
            "description": "Du skal rett frem (andre avkjørsel) gjennom rundkjøring",
            "difficulty": "medium", 
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Blinklys ved gjennomkjøring",
            "layout": {
                "type": "roundabout",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"}
                ]
            },
            "rules": [
                "Ikke blink når du går inn for å kjøre rett frem",
                "Blink høyre ved siste avkjørsel før din avkjørsel",
                "Hold til høyre i rundkjøringen"
            ],
            "correct_actions": ["no_signal_entering", "signal_before_exit", "stay_right"],
            "max_score": 110
        },
        {
            "name": "Rundkjøring - til venstre (tredje avkjørsel)", 
            "description": "Du skal til venstre i tredje avkjørsel fra rundkjøring",
            "difficulty": "hard",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §9 - Venstresvingning i rundkjøring",
            "layout": {
                "type": "roundabout",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"},
                    {"id": "other_car", "position": [3, 2], "direction": "west", "type": "car"}
                ]
            },
            "rules": [
                "Ikke blink når du går inn",
                "Blink høyre ved siste avkjørsel før din avkjørsel", 
                "Pass på annen trafikk i rundkjøringen"
            ],
            "correct_actions": ["no_signal_entering", "navigate_to_third_exit", "signal_before_exit", "yield_to_inner_traffic"],
            "max_score": 140
        },
        {
            "name": "Rundkjøring med sykklist",
            "description": "Sykklist i rundkjøring - du må vike",
            "difficulty": "hard",
            "scenario_type": "roundabout",
            "legal_reference": "Trafikkregler §10 - Syklist i rundkjøring",
            "layout": {
                "type": "roundabout",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "cyclist", "position": [3, 3], "direction": "southwest", "type": "bicycle", "priority": 1}
                ]
            },
            "rules": [
                "Sykklist har samme rettigheter som bil i rundkjøring",
                "Du må vike for sykklist som allerede er i rundkjøringen",
                "Vær ekstra forsiktig med syklist"
            ],
            "correct_actions": ["yield_to_cyclist", "wait_for_clear_path", "enter_carefully"],
            "max_score": 130
        }
    ]
    
    # =============================================================================
    # PEDESTRIAN CROSSING SCENARIOS (Fotgjengerovergang)
    # =============================================================================
    
    pedestrian_scenarios = [
        {
            "name": "Fotgjengerovergang uten lys",
            "description": "Fotgjenger venter ved fotgjengerovergang uten lyssignal", 
            "difficulty": "easy",
            "scenario_type": "pedestrian_crossing",
            "legal_reference": "Trafikkregler §11 - Fotgjengerovergang",
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "pedestrian_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "ped1", "position": [1, 2], "direction": "east", "state": "waiting"}
                ]
            },
            "rules": [
                "Du må stoppe for fotgjenger som ønsker å krysse",
                "Fotgjenger har alltid forkjørsrett på fotgjengerovergang",
                "Stopp helt og la fotgjenger krysse trygt"
            ],
            "correct_actions": ["stop_for_pedestrian", "wait_until_clear", "proceed_slowly"],
            "max_score": 100
        },
        {
            "name": "Fotgjengerovergang ved skole",
            "description": "Fotgjengerovergang i skolesone med barn som krysser",
            "difficulty": "medium",
            "scenario_type": "pedestrian_crossing", 
            "legal_reference": "Trafikkregler §12 - Skolesone",
            "layout": {
                "type": "straight_road",
                "signs": [
                    {"type": "school_zone", "position": [2, 1]},
                    {"type": "pedestrian_crossing", "position": [2, 2]}
                ],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "child1", "position": [1, 2], "direction": "east", "state": "crossing", "type": "child"},
                    {"id": "child2", "position": [0, 2], "direction": "east", "state": "waiting", "type": "child"}
                ]
            },
            "rules": [
                "Ekstra forsiktighet i skolesone",
                "Barn kan oppføre seg uforutsigbart",
                "Stopp helt og vent til alle barn har krysset"
            ],
            "correct_actions": ["reduce_speed_in_school_zone", "stop_for_children", "wait_for_all_clear", "proceed_very_slowly"],
            "max_score": 120
        },
        {
            "name": "Fotgjengerovergang med lys - rødt for fotgjenger",
            "description": "Fotgjengerovergang med lyssignal som viser rødt for fotgjenger",
            "difficulty": "medium",
            "scenario_type": "pedestrian_crossing",
            "legal_reference": "Trafikkregler §7 - Lysregulert fotgjengerovergang", 
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "pedestrian_light", "position": [2, 2], "state": "red_for_pedestrian"}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "ped1", "position": [1, 2], "direction": "east", "state": "waiting"}
                ]
            },
            "rules": [
                "Rødt lys for fotgjenger betyr at bil kan kjøre",
                "Vær likevel forsiktig for fotgjengere som ikke følger lyset", 
                "Kjør i normal hastighet men vær observant"
            ],
            "correct_actions": ["proceed_cautiously", "watch_for_violating_pedestrians"],
            "max_score": 90
        },
        {
            "name": "Fotgjengerovergang - fotgjenger på vei over",
            "description": "Fotgjenger er allerede på vei over veien",
            "difficulty": "easy",
            "scenario_type": "pedestrian_crossing",
            "legal_reference": "Trafikkregler §11 - Ikke hindre kryssende fotgjenger",
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "pedestrian_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "ped1", "position": [2, 2], "direction": "east", "state": "crossing"}
                ]
            },
            "rules": [
                "Du må aldri hindre fotgjenger som krysser",
                "Stopp helt til fotgjenger er trygt over",
                "Ikke tut eller stress fotgjenger"
            ],
            "correct_actions": ["stop_immediately", "wait_patiently", "do_not_honk"],
            "max_score": 100
        }
    ]
    
    # =============================================================================
    # EMERGENCY VEHICLE SCENARIOS (Utrykningskjøretøy)
    # =============================================================================
    
    emergency_scenarios = [
        {
            "name": "Ambulanse med blålys og sirene",
            "description": "Ambulanse med blålys og sirene nærmer seg bakfra",
            "difficulty": "medium",
            "scenario_type": "emergency_vehicle",
            "legal_reference": "Trafikkregler §13 - Utrykningskjøretøy",
            "layout": {
                "type": "straight_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 2], "direction": "north", "type": "car"},
                    {"id": "ambulance", "position": [2, 4], "direction": "north", "type": "ambulance", "emergency": True, "priority": 1}
                ]
            },
            "rules": [
                "Utrykningskjøretøy med blålys og sirene har forkjørsrett",
                "Du må vike til høyre og stoppe om nødvendig",
                "Ikke sving til venstre foran utrykningskjøretøy"
            ],
            "correct_actions": ["move_right", "stop_if_necessary", "give_way_immediately"],
            "max_score": 130
        },
        {
            "name": "Brannbil i kryss",
            "description": "Brannbil med utrykningssignal kommer fra høyre i kryss",
            "difficulty": "hard",
            "scenario_type": "emergency_vehicle",
            "legal_reference": "Trafikkregler §13 - Utrykningskjøretøy har alltid forkjørsrett",
            "layout": {
                "type": "four_way_intersection",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "fire_truck", "position": [4, 2], "direction": "west", "type": "fire_truck", "emergency": True, "priority": 1}
                ]
            },
            "rules": [
                "Utrykningskjøretøy har forkjørsrett i alle situasjoner",
                "Stopp og vike selv om du har forkjørsrett ellers",
                "Vent til utrykningskjøretøy har passert"
            ],
            "correct_actions": ["stop_immediately", "yield_right_of_way", "wait_for_emergency_vehicle"],
            "max_score": 140
        },
        {
            "name": "Politibil bak deg",
            "description": "Politibil med blålys følger deg tett",
            "difficulty": "medium",
            "scenario_type": "emergency_vehicle", 
            "legal_reference": "Trafikkregler §13 - Vike for politibil",
            "layout": {
                "type": "straight_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 2], "direction": "north", "type": "car"},
                    {"id": "police", "position": [2, 3], "direction": "north", "type": "police_car", "emergency": True, "priority": 1}
                ]
            },
            "rules": [
                "Vike til høyre så snart det er trygt",
                "Ikke bråstopp midt i veien",
                "Finn trygg plass å stoppe"
            ],
            "correct_actions": ["find_safe_place", "move_right_gradually", "stop_safely"],
            "max_score": 120
        }
    ]
    
    # =============================================================================
    # LANE MERGING/WEAVING SCENARIOS (Filterfletning)
    # =============================================================================
    
    merging_scenarios = [
        {
            "name": "Påkjøringsrampe til motorvei", 
            "description": "Du kjører fra påkjøringsrampe inn på motorvei",
            "difficulty": "hard",
            "scenario_type": "merging",
            "legal_reference": "Trafikkregler §14 - Påkjøring motorvei",
            "layout": {
                "type": "highway_onramp",
                "signs": [{"type": "merge", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [1, 4], "direction": "north", "type": "car"},
                    {"id": "highway_car1", "position": [2, 3], "direction": "north", "type": "car", "priority": 1},
                    {"id": "highway_car2", "position": [2, 1], "direction": "north", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Tilpasse hastighet til trafikken på motorveien",
                "Vike for trafikk som allerede er på motorveien", 
                "Bruk akselerasjonsfelt til å oppnå riktig hastighet"
            ],
            "correct_actions": ["accelerate_to_match_traffic", "yield_to_highway_traffic", "merge_when_safe"],
            "max_score": 150
        },
        {
            "name": "Filterfletning - du i høyre felt",
            "description": "Bil fra venstre felt vil flette inn foran deg",
            "difficulty": "medium",
            "scenario_type": "merging",
            "legal_reference": "Trafikkregler §15 - Filterfletning",
            "layout": {
                "type": "multi_lane_road", 
                "signs": [{"type": "lane_merge", "position": [1, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"},
                    {"id": "merging_car", "position": [1, 2], "direction": "northeast", "type": "car"}
                ]
            },
            "rules": [
                "Bil som fletter inn må vike",
                "Du kan lette på gassen for å hjelpe",
                "Hold sikker avstand"
            ],
            "correct_actions": ["maintain_position", "adjust_speed_to_help", "keep_safe_distance"],
            "max_score": 110
        },
        {
            "name": "Kollektivfelt avsluttes",
            "description": "Du kjører i kollektivfelt som avsluttes og må flette ut",
            "difficulty": "hard",
            "scenario_type": "merging",
            "legal_reference": "Trafikkregler §8 - Forlate kollektivfelt",
            "layout": {
                "type": "bus_lane_ending",
                "signs": [{"type": "bus_lane_ends", "position": [1, 2]}],
                "vehicles": [
                    {"id": "player", "position": [1, 3], "direction": "north", "type": "taxi"},
                    {"id": "normal_car", "position": [2, 2], "direction": "north", "type": "car", "priority": 1}
                ]
            },
            "rules": [
                "Du må vike når du forlater kollektivfelt",
                "Ikke blokkere normal trafikk",
                "Blink og flette ut trygt"
            ],
            "correct_actions": ["signal_intention", "yield_to_normal_traffic", "merge_carefully"],
            "max_score": 130
        }
    ]
    
    # =============================================================================
    # SCHOOL ZONE SCENARIOS (Skolesone)
    # =============================================================================
    
    school_scenarios = [
        {
            "name": "Skolesone - fartsgrense 30 km/h",
            "description": "Du kjører gjennom skolesone med redusert fartsgrense",
            "difficulty": "easy", 
            "scenario_type": "school_zone",
            "legal_reference": "Trafikkregler §12 - Fartsgrense i skolesone",
            "layout": {
                "type": "straight_road",
                "signs": [
                    {"type": "school_zone", "position": [2, 1]},
                    {"type": "speed_limit_30", "position": [2, 2]}
                ],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 50}
                ]
            },
            "rules": [
                "Reduser fart til 30 km/h i skolesone",
                "Vær ekstra årvåken for barn",
                "Barn kan komme plutselig ut i veien"
            ],
            "correct_actions": ["reduce_speed_to_30", "increase_alertness", "watch_for_children"],
            "max_score": 100
        },
        {
            "name": "Skolesone - barn leker nær veien",
            "description": "Barn leker nær veikanten i skolesone",
            "difficulty": "medium",
            "scenario_type": "school_zone",
            "legal_reference": "Trafikkregler §12 - Aktsomhetskrav ved barn",
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "school_zone", "position": [2, 1]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "pedestrians": [
                    {"id": "child1", "position": [1, 2], "direction": "random", "state": "playing", "type": "child"},
                    {"id": "child2", "position": [0, 2], "direction": "random", "state": "playing", "type": "child"}
                ]
            },
            "rules": [
                "Kjør ekstra forsiktig når barn er i nærheten",
                "Vær klar til å bremse brått",
                "Barn kan handle uforutsigbart"
            ],
            "correct_actions": ["drive_very_slowly", "be_ready_to_brake", "increase_vigilance"],
            "max_score": 120
        },
        {
            "name": "Skolesone - skolebuss stopper",
            "description": "Skolebuss stopper for å slippe av barn",
            "difficulty": "hard",
            "scenario_type": "school_zone", 
            "legal_reference": "Trafikkregler §13 - Forbikjøring av skolebuss",
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "school_zone", "position": [2, 1]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "school_bus", "position": [2, 2], "direction": "north", "type": "school_bus", "state": "stopping"}
                ]
            },
            "rules": [
                "Ikke kjør forbi skolebuss som stopper",
                "Barn kan komme ut plutselig",
                "Vent til bussen kjører videre"
            ],
            "correct_actions": ["stop_behind_bus", "wait_for_bus_to_proceed", "watch_for_children_exiting"],
            "max_score": 140
        }
    ]
    
    # =============================================================================
    # PARKING SCENARIOS (Parkering)
    # =============================================================================
    
    parking_scenarios = [
        {
            "name": "Parkering forbudt - gul stripe",
            "description": "Du står i område med gul stripe på veikanten", 
            "difficulty": "easy",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §16 - Parkeringsforbud",
            "layout": {
                "type": "curb_parking",
                "signs": [{"type": "yellow_curb", "position": [1, 2]}],
                "vehicles": [
                    {"id": "player", "position": [1, 2], "direction": "north", "type": "car", "state": "parked"}
                ]
            },
            "rules": [
                "Gul stripe betyr parkeringsforbud",
                "Du må flytte bilen umiddelbart",
                "Kan få bot ved kontroll"
            ],
            "correct_actions": ["move_vehicle_immediately", "find_legal_parking"],
            "max_score": 80
        },
        {
            "name": "5-meters regelen ved kryss",
            "description": "Du vil parkere nær et kryss",
            "difficulty": "medium",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §17 - Avstand til kryss",
            "layout": {
                "type": "intersection_parking",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [1, 3], "direction": "north", "type": "car", "state": "parking"}
                ],
                "measurements": [
                    {"type": "distance", "from": [1, 3], "to": [2, 2], "value": "3m"}
                ]
            },
            "rules": [
                "Minimum 5 meter avstand til kryss",
                "Ikke blokkere sikt for andre",
                "Finn annen parkeringsplass"
            ],
            "correct_actions": ["find_parking_5m_from_intersection", "avoid_blocking_sight_lines"],
            "max_score": 100
        },
        {
            "name": "Parkering for bevegelseshemmede",
            "description": "Du uten HC-skilt vurderer å parkere på HC-plass",
            "difficulty": "easy",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §18 - HC-parkering",
            "layout": {
                "type": "parking_space",
                "signs": [{"type": "handicap_parking", "position": [1, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "west", "type": "car", "state": "looking_for_parking"}
                ]
            },
            "rules": [
                "HC-parkering kun for bevegelseshemmede med gyldig skilt",
                "Store bøter ved ulovlig bruk", 
                "Finn annen parkeringsplass"
            ],
            "correct_actions": ["avoid_hc_parking", "find_regular_parking"],
            "max_score": 90
        },
        {
            "name": "Betalt parkering - p-skive",
            "description": "Du parkerer i sone som krever p-skive",
            "difficulty": "medium",
            "scenario_type": "parking",
            "legal_reference": "Trafikkregler §19 - P-skive regulering",
            "layout": {
                "type": "parking_space",
                "signs": [{"type": "parking_disc_required", "position": [1, 1], "time_limit": "2h"}],
                "vehicles": [
                    {"id": "player", "position": [1, 2], "direction": "north", "type": "car", "state": "parked"}
                ]
            },
            "rules": [
                "Sett p-skive med ankomsttid", 
                "Maksimalt 2 timer i dette området",
                "Bot ved manglende p-skive"
            ],
            "correct_actions": ["set_parking_disc", "note_time_limit", "return_within_limit"],
            "max_score": 100
        },
        {
            "name": "Parkering i boområde",
            "description": "Du som ikke bor her vil parkere i boområde",
            "difficulty": "medium",
            "scenario_type": "parking", 
            "legal_reference": "Trafikkregler §20 - Beboerparkering",
            "layout": {
                "type": "residential_parking",
                "signs": [{"type": "resident_parking", "position": [1, 1]}],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "west", "type": "car", "state": "looking_for_parking"}
                ]
            },
            "rules": [
                "Beboerparkering kun for beboere med tillatelse",
                "Besøkende kan få kort til besøk",
                "Finn offentlig parkering i stedet"
            ],
            "correct_actions": ["avoid_resident_parking", "find_public_parking", "check_visitor_permits"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # SPEED LIMIT SCENARIOS (Fartsgrenser)
    # =============================================================================
    
    speed_scenarios = [
        {
            "name": "Fartsgrense 30 km/h i boområde",
            "description": "Du kjører gjennom boområde med fartsgrense 30 km/h",
            "difficulty": "easy",
            "scenario_type": "speed_limit",
            "legal_reference": "Trafikkregler §21 - Fartsgrenser i boområde",
            "layout": {
                "type": "residential_road",
                "signs": [{"type": "speed_limit_30", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 45}
                ]
            },
            "rules": [
                "Tilpass fart til fartsgrenseskilt",
                "30 km/h i mange boområder",
                "Ekstra forsiktighet ved lekeplasser"
            ],
            "correct_actions": ["reduce_speed_to_30", "maintain_appropriate_speed"],
            "max_score": 80
        },
        {
            "name": "Fartsgrense på motorvei - 110 km/h",
            "description": "Du kjører på motorvei med fartsgrense 110 km/h",
            "difficulty": "medium", 
            "scenario_type": "speed_limit",
            "legal_reference": "Trafikkregler §22 - Motorveifartsgrenser",
            "layout": {
                "type": "highway",
                "signs": [{"type": "speed_limit_110", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 90}
                ]
            },
            "rules": [
                "Øk fart til passende hastighet for motorvei",
                "Hold deg til høyre hvis du kjører sakte",
                "Ikke kjør for sakte på motorvei"
            ],
            "correct_actions": ["increase_speed_appropriately", "stay_in_right_lane_if_slower"],
            "max_score": 90
        },
        {
            "name": "Variabel fartsgrense - elektronisk skilt",
            "description": "Elektronisk fartsgrenseskilt viser 60 km/h pga værforhold",
            "difficulty": "medium",
            "scenario_type": "speed_limit",
            "legal_reference": "Trafikkregler §23 - Variable fartsgrenser",
            "layout": {
                "type": "highway",
                "signs": [{"type": "variable_speed_60", "position": [2, 2], "weather": "rain"}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 90}
                ],
                "weather": "rain"
            },
            "rules": [
                "Følg elektroniske fartsgrenseskilt",
                "Tilpass fart til vær og føreforhold",
                "Variable grenser har samme gyldighet som vanlige skilt"
            ],
            "correct_actions": ["reduce_speed_to_variable_limit", "adapt_to_weather_conditions"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # BICYCLE/MOTORCYCLE SCENARIOS (Sykkel/Motorsykkel)
    # =============================================================================
    
    bicycle_scenarios = [
        {
            "name": "Forbikjøring av sykklist",
            "description": "Du skal kjøre forbi sykklist på smal vei",
            "difficulty": "medium",
            "scenario_type": "bicycle",
            "legal_reference": "Trafikkregler §24 - Forbikjøring av sykklist",
            "layout": {
                "type": "narrow_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"},
                    {"id": "cyclist", "position": [2, 2], "direction": "north", "type": "bicycle"}
                ]
            },
            "rules": [
                "Minimum 1,5 meter sideavi til sykklist",
                "Vent til det er trygt å kjøre forbi",
                "Ikke tut for å få sykklist til å flytte seg"
            ],
            "correct_actions": ["maintain_safe_distance", "wait_for_safe_passing_opportunity", "give_wide_berth"],
            "max_score": 120
        },
        {
            "name": "Sykklist svinger til venstre",
            "description": "Sykklist foran deg signaliserer venstresvingning",
            "difficulty": "medium",
            "scenario_type": "bicycle", 
            "legal_reference": "Trafikkregler §25 - Syklistens rettigheter",
            "layout": {
                "type": "four_way_intersection",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 3], "direction": "north", "type": "car"},
                    {"id": "cyclist", "position": [2, 2], "direction": "north", "type": "bicycle", "signal": "left"}
                ]
            },
            "rules": [
                "Sykklist har rett til å svinge til venstre",
                "Du må vike og la sykklist svinge først",
                "Ikke kjør forbi sykklist som skal svinge"
            ],
            "correct_actions": ["yield_to_turning_cyclist", "wait_behind_cyclist", "do_not_overtake"],
            "max_score": 110
        },
        {
            "name": "Sykkelsti krysser veien",
            "description": "Sykkelsti krysser veien du kjører på",
            "difficulty": "hard",
            "scenario_type": "bicycle",
            "legal_reference": "Trafikkregler §26 - Kryssende sykkelsti",
            "layout": {
                "type": "bike_path_crossing",
                "signs": [{"type": "bike_crossing", "position": [2, 2]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"},
                    {"id": "cyclist", "position": [1, 2], "direction": "east", "type": "bicycle", "priority": 1}
                ]
            },
            "rules": [
                "Sykklist på sykkelsti har forkjørsrett",
                "Du må vike for syklistene",
                "Vær ekstra oppmerksom på sykkeltrafikkskilt"
            ],
            "correct_actions": ["yield_to_cyclists_on_path", "stop_if_necessary", "proceed_when_clear"],
            "max_score": 130
        }
    ]
    
    # =============================================================================
    # WEATHER/SPECIAL CONDITIONS (Værforhold/Spesielle forhold)
    # =============================================================================
    
    weather_scenarios = [
        {
            "name": "Kjøring i tåke",
            "description": "Tett tåke reduserer sikten betydelig",
            "difficulty": "hard",
            "scenario_type": "weather",
            "legal_reference": "Trafikkregler §27 - Kjøring ved dårlig sikt",
            "layout": {
                "type": "straight_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "weather": "fog",
                "visibility": "low"
            },
            "rules": [
                "Reduser fart ved dårlig sikt", 
                "Bruk nærlys og tåkelys",
                "Øk følgeavstand"
            ],
            "correct_actions": ["reduce_speed", "turn_on_fog_lights", "increase_following_distance"],
            "max_score": 130
        },
        {
            "name": "Glatt vei - is og snø",
            "description": "Vinterføre med is og snø på veien",
            "difficulty": "hard",
            "scenario_type": "weather",
            "legal_reference": "Trafikkregler §28 - Kjøring på glatt vei",
            "layout": {
                "type": "straight_road",
                "signs": [{"type": "slippery_road", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "weather": "snow",
                "road_condition": "icy"
            },
            "rules": [
                "Tilpass fart til føreforhold",
                "Brems forsiktig og tidlig", 
                "Unngå brå manøvrer"
            ],
            "correct_actions": ["reduce_speed_for_conditions", "brake_gently", "avoid_sudden_movements"],
            "max_score": 140
        },
        {
            "name": "Mørke - kveldsbygging",
            "description": "Mørke kveldsforhold uten gatelys",
            "difficulty": "medium",
            "scenario_type": "weather",
            "legal_reference": "Trafikkregler §29 - Lys i mørke",
            "layout": {
                "type": "rural_road",
                "signs": [],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "lighting": "dark",
                "time": "night"
            },
            "rules": [
                "Bruk fjernlys når mulig",
                "Bytt til nærlys ved møtende trafikk",
                "Reduser fart i mørke"
            ],
            "correct_actions": ["use_high_beams", "dim_for_oncoming_traffic", "reduce_speed_in_dark"],
            "max_score": 110
        }
    ]
    
    # =============================================================================
    # ROAD WORK SCENARIOS (Veiarbeid)
    # =============================================================================
    
    roadwork_scenarios = [
        {
            "name": "Veiarbeid med flaggmann",
            "description": "Veiarbeid kontrolleres av flaggmann",
            "difficulty": "medium",
            "scenario_type": "roadwork",
            "legal_reference": "Trafikkregler §30 - Veiarbeid",
            "layout": {
                "type": "construction_zone",
                "signs": [{"type": "road_work", "position": [2, 3]}],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car"}
                ],
                "workers": [
                    {"id": "flagman", "position": [1, 2], "state": "stop_sign", "type": "flagman"}
                ]
            },
            "rules": [
                "Følg flaggmannens instruksjoner",
                "Reduser fart i veiarbeidsone",
                "Vær tålmodig"
            ],
            "correct_actions": ["follow_flagman_instructions", "reduce_speed", "wait_patiently"],
            "max_score": 100
        },
        {
            "name": "Veiarbeidsone - redusert fartsgrense",
            "description": "Midlertidig fartsgrense 40 km/h pga veiarbeid",
            "difficulty": "easy",
            "scenario_type": "roadwork",
            "legal_reference": "Trafikkregler §31 - Midlertidig fartsgrense", 
            "layout": {
                "type": "construction_zone",
                "signs": [
                    {"type": "temporary_speed_40", "position": [2, 3]},
                    {"type": "road_work", "position": [2, 2]}
                ],
                "vehicles": [
                    {"id": "player", "position": [2, 4], "direction": "north", "type": "car", "speed": 60}
                ]
            },
            "rules": [
                "Følg midlertidige fartsgrenser",
                "Oransje skilt har forrang over vanlige skilt",
                "Beskytt veiarbeidere"
            ],
            "correct_actions": ["reduce_to_temporary_limit", "maintain_reduced_speed_through_zone"],
            "max_score": 90
        }
    ]
    
    # =============================================================================
    # COMBINE ALL SCENARIOS
    # =============================================================================
    
    all_scenarios = (
        intersection_scenarios + complex_intersections + 
        roundabout_scenarios + pedestrian_scenarios + 
        emergency_scenarios + merging_scenarios + 
        school_scenarios + parking_scenarios + 
        speed_scenarios + bicycle_scenarios + 
        weather_scenarios + roadwork_scenarios
    )
    
    return all_scenarios


def seed_comprehensive_rule_puzzle_scenarios():
    """Seed database with comprehensive rule puzzle scenarios"""
    
    print("🌱 Starting comprehensive seeding of rule puzzle scenarios...")
    
    # Check if we already have scenarios to avoid duplicates
    existing_count = GameScenario.query.filter_by(scenario_type='rule_puzzle').count()
    
    if existing_count > 50:  # If we already have many scenarios
        print(f"⚠️  Found {existing_count} existing scenarios. Skipping seeding to avoid duplicates.")
        print("   Delete existing scenarios first if you want to reseed.")
        return
    
    scenarios_data = create_comprehensive_scenarios()
    
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
                order_index=success_count + 1,
                is_active=True,
                config_json=json.dumps(config, ensure_ascii=False, indent=2),
                template_name='rule_puzzle_game.html'
            )
            
            db.session.add(scenario)
            success_count += 1
            
            if success_count % 20 == 0:  # Progress indicator
                print(f"  ✅ Added {success_count} scenarios...")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error adding scenario '{scenario_data['name']}': {e}")
    
    try:
        db.session.commit()
        print(f"🎉 Successfully seeded {success_count} comprehensive rule puzzle scenarios!")
        
        if error_count > 0:
            print(f"⚠️  {error_count} scenarios failed to seed")
        
        # Print summary by category
        categories = {}
        for scenario_data in scenarios_data[:success_count]:
            cat = scenario_data.get("scenario_type", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📊 Scenarios by category:")
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
        seed_comprehensive_rule_puzzle_scenarios()