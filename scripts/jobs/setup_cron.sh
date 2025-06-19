#!/bin/bash
"""
Setup Daily Subscription Check
Installs the cron job for daily subscription maintenance
"""

echo "🚀 Setting up daily subscription check..."

# Create log directory
sudo mkdir -p /var/log/sertifikatet
sudo chown $(whoami):$(whoami) /var/log/sertifikatet

# Make the script executable
chmod +x /Users/viktorigesund/Documents/teoritest/scripts/jobs/daily_subscription_check.py

# Install the cron job
echo "📅 Installing cron job..."
crontab -l > /tmp/current_crontab 2>/dev/null || touch /tmp/current_crontab

# Check if cron job already exists
if ! grep -q "daily_subscription_check.py" /tmp/current_crontab; then
    cat /Users/viktorigesund/Documents/teoritest/scripts/jobs/crontab_config >> /tmp/current_crontab
    crontab /tmp/current_crontab
    echo "✅ Cron job installed successfully!"
else
    echo "ℹ️  Cron job already exists, skipping installation."
fi

# Clean up
rm /tmp/current_crontab

echo "🎉 Setup completed!"
echo ""
echo "The daily subscription check will run every day at 00:05 (5 minutes after midnight)."
echo "Logs will be written to: /var/log/sertifikatet/"
echo ""
echo "To manually run the check now:"
echo "  cd /Users/viktorigesund/Documents/teoritest && python3 scripts/jobs/daily_subscription_check.py"
echo ""
echo "To view the cron job:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e  # then delete the line with 'daily_subscription_check.py'"
