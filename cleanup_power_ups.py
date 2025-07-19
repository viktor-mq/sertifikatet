#!/usr/bin/env python3
"""
Clean up power-up related data from database

This script removes power-up related data that may exist in the database
after removing power-up functionality from the application.
"""

from app import create_app, db
from sqlalchemy import text

def cleanup_power_up_data():
    """Remove power-up related data from database"""
    
    print("🧹 Cleaning up power-up related data...")
    print("=" * 50)
    
    # Check if power-up tables exist and get row counts
    try:
        # Check power_ups table
        power_ups_count = db.session.execute(text("SELECT COUNT(*) FROM power_ups")).scalar()
        print(f"📊 Found {power_ups_count} power-ups in database")
        
        # Check user_power_ups table  
        user_power_ups_count = db.session.execute(text("SELECT COUNT(*) FROM user_power_ups")).scalar()
        print(f"📊 Found {user_power_ups_count} user power-up records")
        
        # Check for power-up related XP transactions
        power_up_transactions = db.session.execute(
            text("SELECT COUNT(*) FROM xp_transactions WHERE transaction_type = 'power_up_purchase'")
        ).scalar()
        print(f"📊 Found {power_up_transactions} power-up purchase transactions")
        
    except Exception as e:
        print(f"ℹ️  Power-up tables may not exist: {e}")
        return
    
    # Ask for confirmation before deleting
    if power_ups_count > 0 or user_power_ups_count > 0 or power_up_transactions > 0:
        response = input("\n⚠️  Delete all power-up data? (y/N): ").strip().lower()
        
        if response == 'y':
            print("\n🗑️  Deleting power-up data...")
            
            # Delete user power-ups first (foreign key constraint)
            if user_power_ups_count > 0:
                db.session.execute(text("DELETE FROM user_power_ups"))
                print(f"   ✅ Deleted {user_power_ups_count} user power-up records")
            
            # Delete power-ups
            if power_ups_count > 0:
                db.session.execute(text("DELETE FROM power_ups"))
                print(f"   ✅ Deleted {power_ups_count} power-ups")
            
            # Update power-up purchase transactions to be generic
            if power_up_transactions > 0:
                db.session.execute(text(
                    "UPDATE xp_transactions SET transaction_type = 'purchase', "
                    "description = CONCAT('Legacy: ', description) "
                    "WHERE transaction_type = 'power_up_purchase'"
                ))
                print(f"   ✅ Updated {power_up_transactions} power-up transactions")
            
            # Commit all changes
            db.session.commit()
            print("\n✅ Power-up cleanup completed successfully!")
            
        else:
            print("❌ Cleanup cancelled")
    else:
        print("\n✅ No power-up data found - nothing to clean up")

def drop_power_up_tables():
    """Drop power-up tables entirely (optional)"""
    
    print("\n🗑️  Dropping power-up tables...")
    
    try:
        # Drop tables in correct order (foreign key constraints)
        db.session.execute(text("DROP TABLE IF EXISTS user_power_ups"))
        print("   ✅ Dropped user_power_ups table")
        
        db.session.execute(text("DROP TABLE IF EXISTS power_ups"))
        print("   ✅ Dropped power_ups table")
        
        db.session.commit()
        print("✅ Power-up tables dropped successfully!")
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        db.session.rollback()

def main():
    """Main cleanup function"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Power-Up Cleanup Tool")
        print("========================\n")
        
        # Clean up data first
        cleanup_power_up_data()
        
        # Option to drop tables entirely
        if input("\n🗑️  Also drop power-up tables entirely? (y/N): ").strip().lower() == 'y':
            drop_power_up_tables()
        
        print("\n💡 Note: Power-up functionality has been removed from the application.")
        print("   The database cleanup is now complete!")

if __name__ == '__main__':
    main()
