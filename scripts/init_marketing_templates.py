#!/usr/bin/env python3
"""
Marketing Templates Initialization Script
Adds default marketing email templates to the database for the Sertifikatet platform.

Usage: python init_marketing_templates.py
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.marketing_models import MarketingTemplate
from app.models import User

def init_marketing_templates():
    """Initialize default marketing email templates"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get the first admin user to assign as creator
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                print("❌ Error: No admin user found. Please create an admin user first.")
                return False
            
            print(f"📧 Initializing marketing templates with admin user: {admin_user.username}")
            
            # Check if templates already exist
            existing_count = MarketingTemplate.query.count()
            if existing_count > 0:
                print(f"📋 Found {existing_count} existing templates. Skipping initialization.")
                return True
            
            # Define default templates based on the Quick Start templates
            templates = [
                {
                    "name": "Newsletter Template",
                    "description": "Monthly newsletter with updates and tips for driving theory preparation",
                    "category": "newsletter",
                    "html_content": """<!DOCTYPE html>
<html>
<head>
    <title>Sertifikatet Newsletter</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sertifikatet Newsletter</h1>
        </div>
        <div class="content">
            <h2>Hei {{user.full_name}}!</h2>
            <p>Velkommen til vår månedlige newsletter med de siste oppdateringene fra Sertifikatet.</p>
            
            <h3>Hva er nytt?</h3>
            <ul>
                <li>Nye spørsmål lagt til</li>
                <li>Forbedret mobilapp</li>
                <li>Nye prestasjoner</li>
            </ul>
            
            <p><a href="https://sertifikatet.no" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Logg inn og øv nå</a></p>
        </div>
    </div>
</body>
</html>"""
                },
                {
                    "name": "Promotion Template",  
                    "description": "Special offers and promotional campaigns for premium subscriptions",
                    "category": "promotion",
                    "html_content": """<!DOCTYPE html>
<html>
<head>
    <title>Spesialtilbud - Sertifikatet</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .promo { background: #fff3cd; border: 2px solid #ffc107; padding: 20px; margin: 20px 0; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Spesialtilbud!</h1>
        </div>
        <div class="content">
            <h2>Hei {{user.full_name}}!</h2>
            
            <div class="promo">
                <h3>50% rabatt på Premium!</h3>
                <p>Kun denne uken - oppgrader til Premium og få tilgang til alle funksjoner.</p>
            </div>
            
            <p><a href="https://sertifikatet.no/subscription" style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Oppgrader nå</a></p>
        </div>
    </div>
</body>
</html>"""
                },
                {
                    "name": "Announcement Template",
                    "description": "Important announcements and platform updates",
                    "category": "announcement", 
                    "html_content": """<!DOCTYPE html>
<html>
<head>
    <title>Viktig kunngjøring - Sertifikatet</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #6c757d; color: white; padding: 20px; text-align: center; }
        .announcement { background: #d1ecf1; border-left: 4px solid #bee5eb; padding: 20px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📢 Viktig kunngjøring</h1>
        </div>
        <div class="content">
            <h2>Hei {{user.full_name}}!</h2>
            
            <div class="announcement">
                <h3>Viktig informasjon</h3>
                <p>Vi har en viktig oppdatering å dele med deg...</p>
            </div>
            
            <p>Med vennlig hilsen,<br>
            <strong>Sertifikatet-teamet</strong></p>
        </div>
    </div>
</body>
</html>"""
                },
                {
                    "name": "Welcome Template",
                    "description": "Welcome email for new users joining the platform",
                    "category": "welcome",
                    "html_content": """<!DOCTYPE html>
<html>
<head>
    <title>Velkommen til Sertifikatet!</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .welcome { background: #e7f3ff; border: 1px solid #007bff; padding: 20px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Velkommen!</h1>
        </div>
        <div class="content">
            <div class="welcome">
                <h2>Hei {{user.full_name}}!</h2>
                <p>Velkommen til Sertifikatet! Vi er glade for å ha deg med oss på veien mot førerkortet.</p>
            </div>
            
            <h3>Kom i gang:</h3>
            <ol>
                <li>Ta din første quiz</li>
                <li>Se introduksjonsvideoene</li>
                <li>Sett opp ditt daglige mål</li>
            </ol>
            
            <p><a href="https://sertifikatet.no" style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Start å øve nå</a></p>
        </div>
    </div>
</body>
</html>"""
                }
            ]
            
            # Create templates
            created_count = 0
            for template_data in templates:
                template = MarketingTemplate(
                    name=template_data["name"],
                    description=template_data["description"],
                    html_content=template_data["html_content"],
                    category=template_data["category"],
                    is_active=True,
                    created_by_user_id=admin_user.id
                )
                
                db.session.add(template)
                created_count += 1
                print(f"✅ Created template: {template_data['name']}")
            
            # Commit all templates
            db.session.commit()
            
            print(f"\n🎉 Successfully initialized {created_count} marketing templates!")
            print("\nTemplates created:")
            for i, template_data in enumerate(templates, 1):
                print(f"  {i}. {template_data['name']} ({template_data['category']})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing marketing templates: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Marketing Templates Initialization")
    print("=====================================")
    
    if init_marketing_templates():
        print("\n✅ Marketing templates initialization completed successfully!")
        print("\n💡 You can now:")
        print("   1. Click the 'Templates' button in the admin marketing section")
        print("   2. See the available templates with preview functionality")
        print("   3. Create new campaigns using these templates")
    else:
        print("\n❌ Marketing templates initialization failed!")
        sys.exit(1)
