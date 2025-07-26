# Rule Puzzle Game Configuration
"""
Configuration settings for the traffic scenario puzzle game
"""

GAME_CONFIG = {
    "name": "Trafikk Scenario Puslespill",
    "description": "Løs trafikksituasjoner ved å plassere kjøretøy riktig",
    "base_xp": 50,
    "max_score": 1000,
    "time_limit": 300,  # 5 minutes
    "difficulty_levels": {
        "easy": {
            "name": "Lett",
            "max_vehicles": 3,
            "time_bonus_multiplier": 1.2,
            "score_multiplier": 1.0,
            "hint_penalty": 5
        },
        "medium": {
            "name": "Middels", 
            "max_vehicles": 5,
            "time_bonus_multiplier": 1.5,
            "score_multiplier": 1.3,
            "hint_penalty": 10
        },
        "hard": {
            "name": "Vanskelig",
            "max_vehicles": 8,
            "time_bonus_multiplier": 2.0,
            "score_multiplier": 1.6,
            "hint_penalty": 15
        }
    }
}

# Scenario types and their configurations
SCENARIO_TYPES = {
    "intersection_priority": {
        "name": "Kryss Vikeplikt",
        "description": "Organiser kjøretøy i riktig rekkefølge gjennom krysset",
        "points": 100,
        "vehicles": ["bil", "sykkel", "fotgjenger", "buss"],
        "rules": [
            "Høyre før venstre regel",
            "Hovedvei har vikeplikt",
            "Fotgjengere har alltid vikeplikt på fotgjengerovergang"
        ]
    },
    "roundabout_navigation": {
        "name": "Rundkjøring",
        "description": "Lei kjøretøy gjennom rundkjøringen i riktig rekkefølge",
        "points": 120,
        "vehicles": ["bil", "lastebil", "motorsykkel"],
        "rules": [
            "Kjøretøy i rundkjøringen har vikeplikt",
            "Signal til høyre når du forlater rundkjøringen",
            "Bruk innerste felt ved høyresvign"
        ]
    },
    "pedestrian_crossing": {
        "name": "Fotgjengerovergang",
        "description": "Sikre at fotgjengere krysser trygt",
        "points": 90,
        "vehicles": ["bil", "fotgjenger", "barnevogn"],
        "rules": [
            "Stopp for fotgjengere på overgangen",
            "Gi signal før du stopper",
            "Vent til fotgjengeren er helt over"
        ]
    },
    "emergency_vehicle": {
        "name": "Utrykning",
        "description": "Rydd vei for utrykningskjøretøy",
        "points": 150,
        "vehicles": ["bil", "ambulanse", "brannbil", "politibil"],
        "rules": [
            "Alle må vike for utrykningskjøretøy",
            "Flytt til høyre side av veien",
            "Stopp hvis nødvendig"
        ]
    },
    "lane_merging": {
        "name": "Filterfletning",
        "description": "Flett inn i trafikken på en trygg måte",
        "points": 110,
        "vehicles": ["bil", "motorcykel", "lastebil"],
        "rules": [
            "Gi signal i god tid",
            "Tilpass hastighet til trafikken",
            "Bruk sammenfletningsregelen"
        ]
    },
    "school_zone": {
        "name": "Skolesone",
        "description": "Naviger trygt gjennom skolesonen",
        "points": 100,
        "vehicles": ["bil", "barn", "syklist", "skolepatrulje"],
        "rules": [
            "Redusert hastighet i skolesoner",
            "Ekstra oppmerksomhet på barn",
            "Stopp for skolepatrulje"
        ]
    }
}

# Vehicle types and their properties
VEHICLE_TYPES = {
    "bil": {
        "name": "Bil",
        "icon": "🚗",
        "color": "#3B82F6",
        "size": "medium",
        "priority": 1
    },
    "lastebil": {
        "name": "Lastebil", 
        "icon": "🚚",
        "color": "#EF4444",
        "size": "large",
        "priority": 1
    },
    "motorsykkel": {
        "name": "Motorsykkel",
        "icon": "🏍️",
        "color": "#10B981",
        "size": "small", 
        "priority": 1
    },
    "sykkel": {
        "name": "Sykkel",
        "icon": "🚲",
        "color": "#F59E0B",
        "size": "small",
        "priority": 2
    },
    "fotgjenger": {
        "name": "Fotgjenger",
        "icon": "🚶",
        "color": "#8B5CF6",
        "size": "small",
        "priority": 3
    },
    "barn": {
        "name": "Barn",
        "icon": "🧒",
        "color": "#EC4899",
        "size": "small",
        "priority": 4
    },
    "ambulanse": {
        "name": "Ambulanse",
        "icon": "🚑",
        "color": "#DC2626",
        "size": "large",
        "priority": 10  # Highest priority
    },
    "brannbil": {
        "name": "Brannbil",
        "icon": "🚒",
        "color": "#DC2626",
        "size": "large",
        "priority": 10
    },
    "politibil": {
        "name": "Politibil", 
        "icon": "🚓",
        "color": "#1E40AF",
        "size": "medium",
        "priority": 10
    },
    "buss": {
        "name": "Buss",
        "icon": "🚌",
        "color": "#059669",
        "size": "large",
        "priority": 2
    },
    "barnevogn": {
        "name": "Barnevogn",
        "icon": "🍼",
        "color": "#F472B6",
        "size": "small",
        "priority": 4
    },
    "skolepatrulje": {
        "name": "Skolepatrulje",
        "icon": "🛑",
        "color": "#F59E0B",
        "size": "small",
        "priority": 5
    }
}

# Scoring configuration
SCORING = {
    "perfect_solution": 100,
    "correct_placement": 20,
    "wrong_placement": -10,
    "hint_used": -5,
    "time_bonus_threshold": 120,  # seconds
    "speed_bonus_max": 50
}

# Achievement thresholds
ACHIEVEMENTS = {
    "first_puzzle_solved": {
        "name": "Første Puslespill",
        "description": "Løste ditt første trafikk scenario",
        "xp_bonus": 25
    },
    "perfect_score": {
        "name": "Perfekt Løsning",
        "description": "Løste et scenario uten feil",
        "xp_bonus": 50
    },
    "speed_demon": {
        "name": "Hastighetsdemon",
        "description": "Løste et scenario på under 60 sekunder",
        "xp_bonus": 40
    },
    "no_hints": {
        "name": "Selvstendig",
        "description": "Løste et scenario uten hints",
        "xp_bonus": 30
    },
    "streak_master": {
        "name": "Serie Mester",
        "description": "Løste 5 scenarioer på rad",
        "xp_bonus": 75
    }
}