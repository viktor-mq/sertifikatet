# Advertising Revenue System Database Migration

This directory contains database migration scripts to safely add the advertising revenue system to your Sertifikatet project.

## 🚀 Quick Start

### Option 1: Using Flask-Migrate (Recommended)
```bash
# Navigate to project root
cd /Users/viktorigesund/Documents/teoritest

# Run the migration
flask db upgrade

# Verify migration
python migrate_ads_system.py --verify
```

### Option 2: Using the Migration Script
```bash
# Navigate to project root
cd /Users/viktorigesund/Documents/teoritest

# Dry run first (see what will happen)
python migrate_ads_system.py --dry-run

# Run the actual migration
python migrate_ads_system.py

# Seed initial data (optional)
python migrate_ads_system.py --seed
```

### Option 3: Manual SQL Verification
```bash
# Run the verification script in your MySQL client
mysql -u your_username -p your_database < verify_ads_migration.sql
```

## 📋 What This Migration Does

### ✅ Safe Operations (No Data Loss)
- **Creates 4 new tables:**
  - `ad_interactions` - Track ad impressions, clicks, dismissals
  - `upgrade_prompts` - Track smart upgrade prompts and conversions  
  - `ad_revenue_analytics` - Daily revenue summaries and projections
  - `ad_placement_performance` - Performance by ad location

- **Adds 1 new column:**
  - `subscription_plans.has_ads` - Boolean flag for ad-supported plans

- **Creates performance indexes:**
  - Optimized queries for ad tracking and analytics
  - Foreign key constraints for data integrity

### 🛡️ Safety Features
- **No existing data modified** - Only adds new structures
- **Rollback capability** - Can safely undo the migration
- **Verification included** - Confirms migration success
- **Backup creation** - Schema backup before migration

## 📊 Expected Results

After successful migration, you'll have:

- **Revenue tracking system** ready for Google AdSense integration
- **Smart upgrade prompts** with behavioral targeting
- **Analytics dashboard** for revenue optimization
- **GDPR-compliant** ad consent management

### Revenue Projections
- **Conservative:** 2,985-3,485 NOK/month (1,000 free users)
- **Optimistic:** 18,650-21,150 NOK/month (5,000 free users)

## 🔧 Troubleshooting

### If Migration Fails
```bash
# Check current migration status
flask db current

# Rollback if needed
python migrate_ads_system.py --rollback

# Or rollback with Flask-Migrate
flask db downgrade ml_adaptive_learning
```

### Common Issues

1. **Permission Errors**
   - Ensure database user has CREATE TABLE permissions
   - Check if user can create indexes

2. **Foreign Key Constraints**
   - Verify `users` table exists
   - Check if `subscription_plans` table exists

3. **Column Already Exists**
   - Migration checks for existing columns
   - Safe to re-run if partially completed

### Verification Failures
```bash
# Re-run verification
python migrate_ads_system.py --verify

# Check specific tables manually
mysql -e "SHOW TABLES LIKE 'ad_%'" your_database

# Check column exists
mysql -e "SHOW COLUMNS FROM subscription_plans LIKE 'has_ads'" your_database
```

## 📁 Files Included

- `migrations/versions/add_advertising_system.py` - Main migration file
- `migrate_ads_system.py` - Safe migration runner with verification
- `verify_ads_migration.sql` - Manual SQL verification script
- `README_MIGRATION.md` - This documentation

## 🎯 Next Steps After Migration

1. **Apply for Google AdSense** (longest approval time)
2. **Set up Google Tag Manager** for better ad management
3. **Deploy frontend ad integration** scripts
4. **Test ad tracking** in development environment
5. **Configure ad placements** and frequency limits

## 🔒 Security Notes

- All user data remains untouched
- GDPR-compliant design with proper consent management
- No sensitive data stored in plain text
- Foreign key constraints maintain data integrity

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run verification script to identify specific problems
3. Check Flask application logs for detailed error messages
4. Ensure database permissions are correct

---

**⚠️ Important:** Always backup your database before running migrations in production!
