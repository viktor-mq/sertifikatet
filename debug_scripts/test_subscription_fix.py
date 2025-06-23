#!/usr/bin/env python3
"""
Test script to verify foreign key subscription service is working correctly
Run this from the project root: python test_subscription_fix.py
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from app.payment_models import SubscriptionPlan
from app.services.payment_service import SubscriptionService, UsageLimitService

def test_subscription_service():
    app = create_app()
    
    with app.app_context():
        # Find Viktor user
        viktor = User.query.filter_by(username='Viktor').first()
        
        if not viktor:
            print("❌ Viktor user not found!")
            return
        
        print(f"✅ Found user: {viktor.username} (ID: {viktor.id})")
        print(f"   Email: {viktor.email}")
        print(f"   OLD subscription_tier field: {viktor.subscription_tier}")
        
        # Check FK relationship
        if hasattr(viktor, 'current_plan_id') and viktor.current_plan_id:
            print(f"   NEW current_plan_id: {viktor.current_plan_id}")
            if viktor.current_plan:
                print(f"   NEW current_plan.name: {viktor.current_plan.name}")
                print(f"   NEW current_plan.display_name: {viktor.current_plan.display_name}")
            print(f"   NEW subscription_status: {getattr(viktor, 'subscription_status', 'Not set')}")
        else:
            print("   ❌ No current_plan_id found - migration not applied yet")
        
        print(f"   is_admin: {viktor.is_admin}")
        
        # Test SubscriptionService
        try:
            plan_name = SubscriptionService.get_user_plan(viktor.id)
            print(f"   SubscriptionService.get_user_plan(): {plan_name}")
            
            subscription_stats = SubscriptionService.get_subscription_stats(viktor.id)
            print(f"   Plan display name: {subscription_stats['plan_display_name']}")
            print(f"   Is premium: {subscription_stats['is_premium']}")
            print(f"   Status: {subscription_stats['status']}")
            
            # Test features
            features = SubscriptionService.get_plan_features(plan_name)
            print(f"   Features available:")
            for feature, enabled in features.items():
                if enabled:
                    print(f"     ✅ {feature}")
                else:
                    print(f"     ❌ {feature}")
            
            print("✅ Subscription service is working correctly!")
            
        except Exception as e:
            print(f"❌ Error testing subscription service: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # List all subscription plans
        print("\n📋 Available subscription plans:")
        plans = SubscriptionPlan.query.all()
        for plan in plans:
            print(f"   {plan.id}: {plan.name} - {plan.display_name} ({plan.price_nok} NOK)")

if __name__ == "__main__":
    test_subscription_service()
