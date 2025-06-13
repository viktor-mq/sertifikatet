# scripts/send_reminders.py
"""
Script to send daily learning reminders to users.
This can be run as a cron job or integrated with Celery for scheduled tasks.

Usage:
    python scripts/send_reminders.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.utils.email import send_batch_reminders
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to send daily reminders."""
    app = create_app()
    
    with app.app_context():
        logger.info(f"Starting reminder batch at {datetime.now()}")
        
        try:
            send_batch_reminders()
            logger.info("Reminder batch completed successfully")
        except Exception as e:
            logger.error(f"Error during reminder batch: {str(e)}")
            # Send admin alert
            from app.utils.email import send_admin_alert
            send_admin_alert(
                subject="Daily Reminder Batch Failed",
                message=f"The daily reminder batch failed with error: {str(e)}"
            )


if __name__ == "__main__":
    main()
