#!/usr/bin/env python3
"""
Database Status Checker for Gamification Migration
Run this script to check which tables exist and what columns are missing
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database_status():
    """Check the current database status for gamification tables"""
    
    # Import the database URL from your config
    try:
        from app import create_app
        app = create_app()
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
    except Exception as e:
        print(f"❌ Error getting database URL: {e}")
        print("Make sure your .env file is configured correctly")
        return
    
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        
        print("🔍 Gamification Database Status Check")
        print("=" * 50)
        
        # Tables to check
        required_tables = {
            'weekly_tournaments': ['id', 'name', 'start_date', 'end_date', 'created_at'],
            'tournament_participants': ['id', 'user_id', 'tournament_id', 'score'],
            'daily_challenges': ['id', 'title', 'challenge_type', 'date'],
            'user_daily_challenges': ['id', 'user_id', 'challenge_id', 'completed'],
            'achievements': ['id', 'name', 'description', 'points'],
            'user_achievements': ['id', 'user_id', 'achievement_id', 'earned_at'],
            'user_levels': ['id', 'user_id', 'current_level', 'total_xp'],
            'xp_transactions': ['id', 'user_id', 'amount', 'transaction_type'],
            'xp_rewards': ['id', 'reward_type', 'base_value', 'scaling_factor']
        }
        
        # Check each table
        existing_tables = inspector.get_table_names()
        missing_tables = []
        tables_missing_columns = []
        
        for table_name, required_columns in required_tables.items():
            if table_name not in existing_tables:
                missing_tables.append(table_name)
                print(f"❌ Table '{table_name}' does not exist")
            else:
                print(f"✅ Table '{table_name}' exists")
                
                # Check columns
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                missing_columns = [col for col in required_columns if col not in existing_columns]
                
                if missing_columns:
                    tables_missing_columns.append((table_name, missing_columns))
                    print(f"   ⚠️  Missing columns: {', '.join(missing_columns)}")
                else:
                    print(f"   ✅ All required columns present")
        
        print("\n📋 Summary")
        print("=" * 20)
        
        if not missing_tables and not tables_missing_columns:
            print("🎉 All tables and columns exist! Your database is ready for gamification admin.")
        else:
            print("🔧 Migration needed:")
            
            if missing_tables:
                print(f"   • Tables to create: {', '.join(missing_tables)}")
            
            if tables_missing_columns:
                print("   • Columns to add:")
                for table_name, columns in tables_missing_columns:
                    print(f"     - {table_name}: {', '.join(columns)}")
            
            print("\n🚀 Run the migration script to fix these issues!")
            print("   See: gamification_migration.sql")
        
        print(f"\n📊 Total tables found: {len(existing_tables)}")
        print(f"📊 Gamification tables ready: {len(required_tables) - len(missing_tables)}/{len(required_tables)}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        print("Make sure your database server is running and accessible")

if __name__ == "__main__":
    check_database_status()
