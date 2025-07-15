# app/gamification/challenge_templates.py
"""
Template system for generating challenge titles and descriptions.
Provides localized Norwegian text for different challenge types.
"""
import random
from typing import Dict, List, Optional
from .challenge_types import ChallengeType, CategoryRegistry


class ChallengeTemplateEngine:
    """Engine for generating challenge titles and descriptions"""
    
    def __init__(self):
        self.templates = {
            ChallengeType.QUIZ: QuizChallengeTemplates(),
            ChallengeType.PERFECT_SCORE: PerfectScoreChallengeTemplates(),
            ChallengeType.CATEGORY_FOCUS: CategoryFocusChallengeTemplates(),
            ChallengeType.STREAK: StreakChallengeTemplates(),
            ChallengeType.SPEED_CHALLENGE: SpeedChallengeTemplates(),
            ChallengeType.ACCURACY_CHALLENGE: AccuracyChallengeTemplates()
        }
    
    def generate_challenge_text(self, challenge_type: ChallengeType, 
                               requirement_value: int, category: str = None,
                               difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        """
        Generate title and description for a challenge.
        
        Returns:
            Dict with 'title' and 'description' keys
        """
        template = self.templates.get(challenge_type)
        if not template:
            return self._generate_fallback_text(challenge_type, requirement_value)
        
        return template.generate(
            requirement_value=requirement_value,
            category=category,
            difficulty=difficulty,
            is_ml_generated=is_ml_generated
        )
    
    def _generate_fallback_text(self, challenge_type: ChallengeType, requirement_value: int) -> Dict[str, str]:
        """Fallback text generation if template not found"""
        return {
            'title': f"Daglig utfordring",
            'description': f"Fullfør {requirement_value} oppgaver for å tjene XP."
        }


class BaseChallengeTemplate:
    """Base class for challenge templates"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        """Generate title and description"""
        raise NotImplementedError
    
    def _get_difficulty_adjective(self, difficulty: float) -> str:
        """Get Norwegian adjective based on difficulty"""
        if difficulty < 0.3:
            return random.choice(['enkle', 'grunnleggende', 'introduksjon'])
        elif difficulty < 0.7:
            return random.choice(['moderate', 'utfordrende', 'viktige'])
        else:
            return random.choice(['avanserte', 'krevende', 'ekspert'])
    
    def _get_encouragement(self, difficulty: float) -> str:
        """Get encouraging phrase based on difficulty"""
        if difficulty < 0.3:
            return random.choice([
                'Du klarer dette!',
                'En fin start på dagen!',
                'Perfekt for å bygge selvtillit!'
            ])
        elif difficulty < 0.7:
            return random.choice([
                'En god utfordring for deg!',
                'Test ferdighetene dine!',
                'Tid for å utvikle seg!'
            ])
        else:
            return random.choice([
                'Vis hva du kan!',
                'En ekte utfordring!',
                'Bare for ekspertene!'
            ])
    
    def _get_ml_prefix(self, is_ml_generated: bool) -> str:
        """Get prefix for ML-generated challenges"""
        return "[ML] " if is_ml_generated else ""


class QuizChallengeTemplates(BaseChallengeTemplate):
    """Templates for quiz challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        difficulty_adj = self._get_difficulty_adjective(difficulty)
        encouragement = self._get_encouragement(difficulty)
        
        if category:
            category_name = CategoryRegistry.get_category_name(category)
            
            titles = [
                f"{prefix}Øv på {category_name}",
                f"{prefix}Test deg i {category_name}",
                f"{prefix}{category_name} utfordring",
                f"{prefix}Mestre {category_name}"
            ]
            
            descriptions = [
                f"Fullfør {requirement_value} {difficulty_adj} spørsmål om {category_name}. {encouragement}",
                f"Test kunnskapen din med {requirement_value} spørsmål innen {category_name}.",
                f"Øv deg på {requirement_value} spørsmål om {category_name} for å forbedre ferdighetene.",
                f"Utforsk {requirement_value} {difficulty_adj} spørsmål om {category_name} og lær noe nytt!"
            ]
        else:
            titles = [
                f"{prefix}Dagens quiz",
                f"{prefix}Quiz utfordring",
                f"{prefix}Test ferdighetene",
                f"{prefix}Øvingsrunde"
            ]
            
            descriptions = [
                f"Fullfør {requirement_value} {difficulty_adj} quiz for å øve på teoriprøven. {encouragement}",
                f"Test deg selv med {requirement_value} spørsmål tilpasset ditt nivå.",
                f"Øv deg med {requirement_value} varierte spørsmål fra teoriprøven.",
                f"Fullfør {requirement_value} spørsmål og forbedre kunnskapen din!"
            ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


class PerfectScoreChallengeTemplates(BaseChallengeTemplate):
    """Templates for perfect score challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        encouragement = self._get_encouragement(difficulty)
        
        titles = [
            f"{prefix}Perfekt resultat",
            f"{prefix}Feilfri prestasjon", 
            f"{prefix}100% nøyaktighet",
            f"{prefix}Mestring på høyt nivå"
        ]
        
        if category:
            category_name = CategoryRegistry.get_category_name(category)
            descriptions = [
                f"Oppnå {requirement_value} perfekte resultater (100%) i {category_name}. {encouragement}",
                f"Vis at du mestrer {category_name} ved å score perfekt {requirement_value} ganger.",
                f"Få full pott på {requirement_value} quiz innen {category_name}.",
                f"Demonstrer din ekspertise i {category_name} med {requirement_value} perfekte runder."
            ]
        else:
            descriptions = [
                f"Oppnå {requirement_value} perfekte quiz-resultater (100% riktig). {encouragement}",
                f"Vis din mestring ved å få full pott på {requirement_value} quiz.",
                f"Fullfør {requirement_value} quiz uten en eneste feil.",
                f"Demonstrer din kunnskap med {requirement_value} feilfrie prestasjoner!"
            ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


class CategoryFocusChallengeTemplates(BaseChallengeTemplate):
    """Templates for category-focused challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        difficulty_adj = self._get_difficulty_adjective(difficulty)
        
        if not category:
            category = 'traffic_signs'  # Default fallback
        
        category_name = CategoryRegistry.get_category_name(category)
        
        titles = [
            f"{prefix}Mestre {category_name}",
            f"{prefix}Fokus på {category_name}",
            f"{prefix}{category_name} spesialist",
            f"{prefix}Dyp kunnskap om {category_name}"
        ]
        
        descriptions = [
            f"Fordyp deg i {category_name} med {requirement_value} {difficulty_adj} spørsmål.",
            f"Bli ekspert på {category_name} ved å løse {requirement_value} spørsmål.",
            f"Fokuser på dine svake områder: øv {requirement_value} spørsmål om {category_name}.",
            f"Styrk kunnskapen din innen {category_name} med målrettet øving på {requirement_value} spørsmål.",
            f"Spesialiser deg på {category_name} - fullfør {requirement_value} fokuserte oppgaver."
        ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


class StreakChallengeTemplates(BaseChallengeTemplate):
    """Templates for streak challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        
        titles = [
            f"{prefix}Holdt rekken gående",
            f"{prefix}Daglig rutine",
            f"{prefix}Konsistent læring",
            f"{prefix}Øvingsdisiplin"
        ]
        
        descriptions = [
            f"Øv deg {requirement_value} dager på rad for å bygge gode vaner.",
            f"Oppretthold læringsrekken din i {requirement_value} sammenhengende dager.",
            f"Vis disiplin ved å øve hver dag i {requirement_value} dager.",
            f"Bygg en sterk læringsrutine med {requirement_value} dagers sammenhengende aktivitet.",
            f"Konsistens er nøkkelen: øv deg daglig i {requirement_value} dager på rad!"
        ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


class SpeedChallengeTemplates(BaseChallengeTemplate):
    """Templates for speed challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        
        titles = [
            f"{prefix}Hastighetstesting",
            f"{prefix}Rask besvarelse",
            f"{prefix}Ekspress quiz",
            f"{prefix}Tempoøving"
        ]
        
        time_limit = max(10, 30 - (requirement_value * 2))  # Rough time calculation
        
        if category:
            category_name = CategoryRegistry.get_category_name(category)
            descriptions = [
                f"Fullfør {requirement_value} spørsmål om {category_name} på under {time_limit} sekunder per spørsmål.",
                f"Test hastigheten din: svar på {requirement_value} {category_name}-spørsmål raskt og nøyaktig.",
                f"Ekspress-runde: {requirement_value} raske spørsmål om {category_name}."
            ]
        else:
            descriptions = [
                f"Fullfør {requirement_value} spørsmål på rekordtid - under {time_limit} sekunder per spørsmål.",
                f"Test både hastighet og nøyaktighet: svar raskt på {requirement_value} spørsmål.",
                f"Hastighetstesting: løs {requirement_value} spørsmål så raskt som mulig.",
                f"Kombiner fart og presisjon i denne {requirement_value}-spørsmåls utfordringen!"
            ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


class AccuracyChallengeTemplates(BaseChallengeTemplate):
    """Templates for accuracy challenges"""
    
    def generate(self, requirement_value: int, category: str = None,
                difficulty: float = 0.5, is_ml_generated: bool = True) -> Dict[str, str]:
        
        prefix = self._get_ml_prefix(is_ml_generated)
        target_accuracy = max(70, 85 + (difficulty * 10))  # 70-95% accuracy target
        
        titles = [
            f"{prefix}Presisjonstrening",
            f"{prefix}Nøyaktighetstest",
            f"{prefix}Treffsikkerhet",
            f"{prefix}Kvalitet over kvantitet"
        ]
        
        if category:
            category_name = CategoryRegistry.get_category_name(category)
            descriptions = [
                f"Oppnå {target_accuracy:.0f}% nøyaktighet på {requirement_value} spørsmål om {category_name}.",
                f"Fokuser på kvalitet: svar presist på {requirement_value} {category_name}-spørsmål.",
                f"Vis din ekspertise innen {category_name} med høy nøyaktighet på {requirement_value} spørsmål."
            ]
        else:
            descriptions = [
                f"Oppnå minimum {target_accuracy:.0f}% riktige svar på {requirement_value} spørsmål.",
                f"Kvalitet over kvantitet: svar nøyaktig på {requirement_value} spørsmål.",
                f"Test presisjonen din med {requirement_value} spørsmål og høy treffsikkerhet.",
                f"Vis at du mestrer teorien med {target_accuracy:.0f}% nøyaktighet på {requirement_value} spørsmål."
            ]
        
        return {
            'title': random.choice(titles),
            'description': random.choice(descriptions)
        }


# Global template engine instance
challenge_template_engine = ChallengeTemplateEngine()
