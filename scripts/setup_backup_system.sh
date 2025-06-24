#!/bin/bash
# Database Backup System Setup Script

echo "🔧 Setting up Sertifikatet Database Backup System"
echo "=================================================="

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_SCRIPT="$PROJECT_DIR/scripts/database_backup.py"

echo "Project directory: $PROJECT_DIR"
echo "Backup script: $BACKUP_SCRIPT"

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"

# Create backup directory
mkdir -p "../Backups/sertifikatet"

# Install required Python packages if needed
echo "📦 Checking Python dependencies..."
cd "$PROJECT_DIR"
source venv/bin/activate
pip install mysql-connector-python python-dotenv

echo "⏰ Setting up cron jobs..."

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing cron jobs (excluding our backup jobs)
crontab -l 2>/dev/null | grep -v "sertifikatet_backup" > "$TEMP_CRON"

# Add new backup jobs
echo "# Sertifikatet Database Backups" >> "$TEMP_CRON"
echo "# Daily backup at 2:30 AM" >> "$TEMP_CRON"
echo "30 2 * * * cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python $BACKUP_SCRIPT >> ../Backups/sertifikatet/cron.log 2>&1" >> "$TEMP_CRON"
echo "" >> "$TEMP_CRON"

# Install new cron jobs
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron jobs installed:"
echo "   - Daily backup: 2:30 AM"

# Test backup system
echo "🧪 Testing backup system..."
cd "$PROJECT_DIR"
source venv/bin/activate
python "$BACKUP_SCRIPT"

if [ $? -eq 0 ]; then
    echo "✅ Backup test successful!"
else
    echo "❌ Backup test failed. Check configuration."
    exit 1
fi

# Show current backups
echo "📁 Current backups:"
ls -la "../Backups/sertifikatet/"

echo ""
echo "🎉 Backup system setup complete!"
echo ""
echo "📋 Manual commands:"
echo "   Run backup:     cd $PROJECT_DIR && python scripts/database_backup.py"
echo "   Restore backup: cd $PROJECT_DIR && python scripts/database_restore.py"
echo "   View backups:   ls -la ../Backups/sertifikatet/"
echo ""
echo "📧 Email alerts configured for: $(grep SUPER_ADMIN_EMAIL $PROJECT_DIR/.env | cut -d'=' -f2)"
echo "📅 Next automatic backup: Tomorrow at 2:30 AM"
