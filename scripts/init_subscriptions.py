#!/usr/bin/env python3
"""
Initialize Subscription Plans
Phase 11: Payment & Subscriptions
"""

import sys
import os
from decimal import Decimal
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.payment_models import SubscriptionPlan


def init_subscription_plans():
    """Initialize the subscription plans"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Initializing subscription plans...")
        
        # Free Plan
        free_plan = SubscriptionPlan.query.filter_by(name='free').first()
        if not free_plan:
            free_features = [
                "10 quiz per dag",
                "2 prøveeksamener per uke", 
                "Grunnleggende statistikk",
                "Tilgang til spill",
                "Gamification system"
            ]
            
            free_plan = SubscriptionPlan(
                name='free',
                display_name='Gratis Plan',
                price_nok=Decimal('0.00'),
                billing_cycle='monthly',
                description='Gratis tilgang til grunnleggende funksjoner',
                features_json=json.dumps(free_features),
                max_daily_quizzes=10,
                max_weekly_exams=2,
                has_ads=True,
                has_detailed_stats=False,
                has_ai_adaptive=False,
                has_offline_mode=False,
                has_personal_tutor=False,
                has_video_access=False,
                priority_support=False
            )
            db.session.add(free_plan)
            print("✅ Created Free plan")
        
        # Premium Plan
        premium_plan = SubscriptionPlan.query.filter_by(name='premium').first()
        if not premium_plan:
            premium_features = [
                "Ubegrensede quiz",
                "Ubegrensede prøveeksamener",
                "Tilgang til alle videoer",
                "Detaljert statistikk og analyse",
                "AI-tilpasset læring",
                "Ingen annonser",
                "Prioritert kundesupport",
                "Avanserte gamification funksjoner"
            ]
            
            premium_plan = SubscriptionPlan(
                name='premium',
                display_name='Premium Plan',
                price_nok=Decimal('149.00'),
                billing_cycle='monthly',
                description='Ubegrenset tilgang til alle premium funksjoner',
                features_json=json.dumps(premium_features),
                max_daily_quizzes=None,  # Unlimited
                max_weekly_exams=None,   # Unlimited
                has_ads=False,
                has_detailed_stats=True,
                has_ai_adaptive=True,
                has_offline_mode=False,
                has_personal_tutor=False,
                has_video_access=True,
                priority_support=True
            )
            db.session.add(premium_plan)
            print("✅ Created Premium plan")
        
        # Pro Plan
        pro_plan = SubscriptionPlan.query.filter_by(name='pro').first()
        if not pro_plan:
            pro_features = [
                "Alt fra Premium plan",
                "Offline modus for quiz og videoer",
                "Personlig AI-veileder",
                "Avansert analyse og innsikt",
                "Eksklusiv innhold og funksjoner",
                "24/7 premium support",
                "Eksport av data og resultater",
                "API tilgang for integrasjoner"
            ]
            
            pro_plan = SubscriptionPlan(
                name='pro',
                display_name='Pro Plan',
                price_nok=Decimal('249.00'),
                billing_cycle='monthly',
                description='Alt du trenger for profesjonell teoritest forberedelse',
                features_json=json.dumps(pro_features),
                max_daily_quizzes=None,  # Unlimited
                max_weekly_exams=None,   # Unlimited
                has_ads=False,
                has_detailed_stats=True,
                has_ai_adaptive=True,
                has_offline_mode=True,
                has_personal_tutor=True,
                has_video_access=True,
                priority_support=True
            )
            db.session.add(pro_plan)
            print("✅ Created Pro plan")
        
        # Create yearly variants
        premium_yearly = SubscriptionPlan.query.filter_by(name='premium_yearly').first()
        if not premium_yearly:
            premium_yearly = SubscriptionPlan(
                name='premium_yearly',
                display_name='Premium Plan (Årlig)',
                price_nok=Decimal('1490.00'),  # 2 months free
                billing_cycle='yearly',
                description='Premium plan med årlig fakturering - spar 2 måneder!',
                features_json=premium_plan.features_json,
                max_daily_quizzes=None,
                max_weekly_exams=None,
                has_ads=False,
                has_detailed_stats=True,
                has_ai_adaptive=True,
                has_offline_mode=False,
                has_personal_tutor=False,
                has_video_access=True,
                priority_support=True
            )
            db.session.add(premium_yearly)
            print("✅ Created Premium Yearly plan")
        
        pro_yearly = SubscriptionPlan.query.filter_by(name='pro_yearly').first()
        if not pro_yearly:
            pro_yearly = SubscriptionPlan(
                name='pro_yearly',
                display_name='Pro Plan (Årlig)',
                price_nok=Decimal('2490.00'),  # 2 months free
                billing_cycle='yearly',
                description='Pro plan med årlig fakturering - spar 2 måneder!',
                features_json=pro_plan.features_json,
                max_daily_quizzes=None,
                max_weekly_exams=None,
                has_ads=False,
                has_detailed_stats=True,
                has_ai_adaptive=True,
                has_offline_mode=True,
                has_personal_tutor=True,
                has_video_access=True,
                priority_support=True
            )
            db.session.add(pro_yearly)
            print("✅ Created Pro Yearly plan")
        
        # Commit all changes
        db.session.commit()
        print("💾 All subscription plans saved!")
        
        # Display summary
        plans = SubscriptionPlan.query.all()
        print(f"\n📊 Summary: {len(plans)} subscription plans created")
        for plan in plans:
            print(f"   • {plan.display_name}: {plan.price_nok} NOK ({plan.billing_cycle})")
        
        print("\n🎉 Subscription system ready!")


if __name__ == '__main__':
    init_subscription_plans()
