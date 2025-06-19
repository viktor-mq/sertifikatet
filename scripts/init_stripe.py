#!/usr/bin/env python3
"""
Initialize Stripe Payment Integration
Creates subscription plans and sets up basic payment configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.payment_models import SubscriptionPlan
from datetime import datetime
import json

def create_subscription_plans():
    """Create the subscription plans in database"""
    
    plans = [
        {
            'name': 'free',
            'display_name': 'Gratis Plan',
            'price_nok': 0.00,
            'billing_cycle': 'monthly',
            'description': 'Grunnleggende tilgang til quiz og læring',
            'features_json': json.dumps([
                'Inntil 10 quiz per dag',
                'Inntil 2 prøveeksamener per uke',
                'Grunnleggende statistikk',
                'Annonser inkludert'
            ]),
            'max_daily_quizzes': 10,
            'max_weekly_exams': 2,
            'has_ads': True,
            'has_detailed_stats': False,
            'has_ai_adaptive': False,
            'has_offline_mode': False,
            'has_personal_tutor': False,
            'has_video_access': False,
            'priority_support': False
        },
        {
            'name': 'premium',
            'display_name': 'Premium Plan',
            'price_nok': 149.00,
            'billing_cycle': 'monthly',
            'description': 'Komplett tilgang til alle funksjoner utenom offline modus',
            'features_json': json.dumps([
                'Ubegrenset quiz og prøveeksamener',
                'Alle videoer og læringsmateriell',
                'Detaljert statistikk og fremgang',
                'AI-tilpasset læring',
                'Ingen annonser',
                'Prioritert kundesupport'
            ]),
            'max_daily_quizzes': None,
            'max_weekly_exams': None,
            'has_ads': False,
            'has_detailed_stats': True,
            'has_ai_adaptive': True,
            'has_offline_mode': False,
            'has_personal_tutor': False,
            'has_video_access': True,
            'priority_support': True
        },
        {
            'name': 'pro',
            'display_name': 'Pro Plan',
            'price_nok': 249.00,
            'billing_cycle': 'monthly',
            'description': 'Alle Premium-funksjoner pluss offline modus og personlig veileder',
            'features_json': json.dumps([
                'Alt fra Premium Plan',
                'Offline modus for læring uten internett',
                'Personlig AI-veileder',
                'Avansert læringsanalyse',
                'Raskere kundesupport',
                'Tidlig tilgang til nye funksjoner'
            ]),
            'max_daily_quizzes': None,
            'max_weekly_exams': None,
            'has_ads': False,
            'has_detailed_stats': True,
            'has_ai_adaptive': True,
            'has_offline_mode': True,
            'has_personal_tutor': True,
            'has_video_access': True,
            'priority_support': True
        }
    ]
    
    for plan_data in plans:
        # Check if plan already exists
        existing_plan = SubscriptionPlan.query.filter_by(name=plan_data['name']).first()
        
        if existing_plan:
            print(f"Plan '{plan_data['name']}' already exists, updating...")
            for key, value in plan_data.items():
                setattr(existing_plan, key, value)
        else:
            print(f"Creating plan '{plan_data['name']}'...")
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
    
    db.session.commit()
    print("✅ Subscription plans created/updated successfully!")

def verify_stripe_config():
    """Verify Stripe configuration"""
    from flask import current_app
    
    publishable_key = current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    secret_key = current_app.config.get('STRIPE_SECRET_KEY')
    
    if not publishable_key or not secret_key:
        print("❌ Error: Stripe keys not found in configuration!")
        print("Make sure STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY are set in your .env file")
        return False
    
    if publishable_key.startswith('pk_live'):
        print("✅ Stripe LIVE keys detected")
        print("⚠️  WARNING: You are using LIVE Stripe keys! Real payments will be processed!")
    elif publishable_key.startswith('pk_test'):
        print("✅ Stripe TEST keys detected")
        print("💡 You can test payments safely")
    else:
        print("❌ Error: Invalid Stripe publishable key format")
        return False
    
    return True

def test_stripe_connection():
    """Test connection to Stripe API"""
    try:
        import stripe
        from flask import current_app
        
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        
        # Try to retrieve account information
        account = stripe.Account.retrieve()
        print(f"✅ Successfully connected to Stripe account: {account.get('business_profile', {}).get('name', 'Unknown')}")
        print(f"   Country: {account.get('country', 'Unknown')}")
        print(f"   Account ID: {account.get('id', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Stripe: {str(e)}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing Stripe Payment Integration for Sertifikatet...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        print("1. Verifying Stripe configuration...")
        if not verify_stripe_config():
            return
        
        print("\n2. Testing Stripe connection...")
        if not test_stripe_connection():
            print("⚠️  Stripe connection failed, but continuing with database setup...")
        
        print("\n3. Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        print("\n4. Setting up subscription plans...")
        create_subscription_plans()
        
        print("\n" + "=" * 60)
        print("🎉 Stripe integration initialized successfully!")
        print("\nNext steps:")
        print("1. Test payments using Stripe's test card numbers")
        print("2. Set up webhook endpoints in Stripe Dashboard:")
        print("   Webhook URL: https://your-domain.com/subscription/webhook/stripe")
        print("3. Configure webhook events: payment_intent.succeeded, checkout.session.completed")
        print("4. Add the webhook signing secret to your .env file as STRIPE_WEBHOOK_SECRET")
        print("\nTest cards for Norway:")
        print("- Visa: 4000 0056 4000 0008")
        print("- Mastercard: 5555 5556 4000 0008")
        print("- Use any future expiry date and any 3-digit CVC")

if __name__ == '__main__':
    main()
