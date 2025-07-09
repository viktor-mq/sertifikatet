    @staticmethod
    def get_submodules_progress(module_id, user):
        """Get all submodules for a module with user progress"""
        try:
            # Return mock submodule data for all modules
            submodules_data = {
                1: [  # Grunnleggende Trafikklære
                    {
                        'submodule_number': 1.1,
                        'title': 'Trafikkregler',
                        'description': 'Grunnleggende trafikkregler og forskrifter',
                        'estimated_minutes': 25,
                        'difficulty_level': 1,
                        'completion_percentage': 100,
                        'status': 'completed',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.2,
                        'title': 'Vikeplikt',
                        'description': 'Forstå vikeplikt i ulike trafikksituasjoner',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 65,
                        'status': 'in_progress',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.3,
                        'title': 'Politi og trafikklys',
                        'description': 'Signaler fra politi og trafikklys',
                        'estimated_minutes': 20,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.4,
                        'title': 'Plassering og feltskifte',
                        'description': 'Riktig plassering på veien og feltskifte',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 1.5,
                        'title': 'Kjøring i rundkjøring',
                        'description': 'Mestre rundkjøring og navigering',
                        'estimated_minutes': 25,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    }
                ],
                2: [  # Skilt og Oppmerking
                    {
                        'submodule_number': 2.1,
                        'title': 'Fareskilt – lær mønstrene',
                        'description': 'Forstå fareskiltene som varsler om spesielle farer',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.2,
                        'title': 'Forbudsskilt – hva du IKKE kan gjøre',
                        'description': 'Lær deg forbudsskiltene som setter begrensninger',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.3,
                        'title': 'Påbudsskilt – følg instruksjonen',
                        'description': 'Forstå påbudsskiltene som gir obligatoriske instrukser',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.4,
                        'title': 'Opplysningsskilt og serviceskilt',
                        'description': 'Lær deg skiltene som gir nyttig informasjon og viser vei til tjenester',
                        'estimated_minutes': 30,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 2.5,
                        'title': 'Vegoppmerking – linjer og symboler',
                        'description': 'Forstå de ulike linjene og symbolene på veien',
                        'estimated_minutes': 45,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                3: [  # Kjøretøy og Teknologi
                    {
                        'submodule_number': 3.1,
                        'title': 'Bremselengde og reaksjonstid',
                        'description': 'Lær om de kritiske faktorene som bestemmer hvor lang tid og distanse du trenger for å stoppe',
                        'estimated_minutes': 45,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.2,
                        'title': 'Sikt, lysbruk og vær',
                        'description': 'Mestre kunsten å se og bli sett under alle forhold',
                        'estimated_minutes': 40,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.3,
                        'title': 'Dekk, mønsterdybde og grep',
                        'description': 'Forstå hvorfor dekkene er din viktigste forbindelse til veien',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.4,
                        'title': 'Kontrollrutiner før kjøring',
                        'description': 'Lær deg de enkle sjekkene du må gjøre før hver kjøretur',
                        'estimated_minutes': 30,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 3.5,
                        'title': 'Elbil, hybrid og moderne hjelpemidler',
                        'description': 'Utforsk teknologien som former fremtidens kjøring',
                        'estimated_minutes': 40,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                4: [  # Mennesket i Trafikken
                    {
                        'submodule_number': 4.1,
                        'title': 'Alkohol, rus og reaksjonsevne',
                        'description': 'Forstå hvordan alkohol og andre rusmidler påvirker kjøreevnen',
                        'estimated_minutes': 35,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.2,
                        'title': 'Trøtthet og distraksjoner',
                        'description': 'Lær å gjenkjenne og håndtere trøtthet og distraksjoner under kjøring',
                        'estimated_minutes': 30,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.3,
                        'title': 'Risikoforståelse og kjørestrategi',
                        'description': 'Utvikle god risikoforståelse og defensive kjøreteknikker',
                        'estimated_minutes': 40,
                        'difficulty_level': 3,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 4.4,
                        'title': 'Førstehjelp og ulykkesberedskap',
                        'description': 'Lær grunnleggende førstehjelp og hvordan du reagerer ved ulykker',
                        'estimated_minutes': 45,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 4,
                        'has_quiz': True
                    }
                ],
                5: [  # Øvingskjøring og Avsluttende Test
                    {
                        'submodule_number': 5.1,
                        'title': 'Ansvar og regler under øvingskjøring',
                        'description': 'Forstå ditt ansvar og hvilke regler som gjelder under øvingskjøring',
                        'estimated_minutes': 35,
                        'difficulty_level': 2,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 3,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.2,
                        'title': 'Oppsummeringsquiz',
                        'description': 'Test din kunnskap med en omfattende quiz som dekker alle moduler',
                        'estimated_minutes': 40,
                        'difficulty_level': 4,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': False,
                        'shorts_count': 0,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.3,
                        'title': 'Eksamenstrening med tidspress',
                        'description': 'Øv på teoriprøven under realistiske tidsforhold',
                        'estimated_minutes': 50,
                        'difficulty_level': 4,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': True
                    },
                    {
                        'submodule_number': 5.4,
                        'title': 'Hva skjer på teoriprøven?',
                        'description': 'Forbered deg til selve teoriprøven og lær hva du kan forvente',
                        'estimated_minutes': 25,
                        'difficulty_level': 1,
                        'completion_percentage': 0,
                        'status': 'not_started',
                        'has_video_shorts': True,
                        'shorts_count': 2,
                        'has_quiz': False
                    }
                ]
            }
            
            return submodules_data.get(module_id, [])
        except Exception as e:
            logger.error(f"Error getting submodules progress for module {module_id}: {str(e)}")
            return []
