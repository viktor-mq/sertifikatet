#!/usr/bin/env python3
"""
Automatic MySQL Database Backup Script
Creates automated backups with rotation and verification
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKUP_DIR = Path("backups/database")
MAX_BACKUPS = 30  # Keep 30 days of backups
COMPRESS_BACKUPS = True
VERIFY_BACKUPS = True
SEND_EMAIL_ALERTS = True

# Create backup directory
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BACKUP_DIR / 'backup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Handle MySQL database backups with rotation and verification"""
    
    def __init__(self):
        self.db_config = self._get_db_config()
        self.backup_dir = BACKUP_DIR
        
    def _get_db_config(self):
        """Extract database configuration from DATABASE_URL"""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        # Parse mysql+pymysql://username:password@host:port/database_name
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        return {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path[1:]  # Remove leading slash
        }
    
    def create_backup(self):
        """Create a new database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"sertifikatet_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        logger.info(f"Creating backup: {backup_filename}")
        
        try:
            # Build mysqldump command
            cmd = [
                'mysqldump',
                f'--host={self.db_config["host"]}',
                f'--port={self.db_config["port"]}',
                f'--user={self.db_config["user"]}',
                f'--password={self.db_config["password"]}',
                '--single-transaction',  # Consistent backup
                '--routines',            # Include stored procedures
                '--triggers',            # Include triggers
                '--events',              # Include events
                '--add-drop-table',      # Add DROP TABLE statements
                '--create-options',      # Include all MySQL-specific create options
                '--disable-keys',        # Faster restoration
                '--extended-insert',     # More efficient inserts
                '--quick',               # Retrieve rows one at a time
                '--lock-tables=false',   # Don't lock tables (use single-transaction instead)
                self.db_config['database']
            ]
            
            # Execute mysqldump
            with open(backup_path, 'w') as backup_file:
                result = subprocess.run(
                    cmd, 
                    stdout=backup_file, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
            
            if result.returncode != 0:
                error_msg = result.stderr
                logger.error(f"mysqldump failed: {error_msg}")
                self._send_alert(f"Backup failed: {error_msg}")
                return None
            
            # Get backup file size
            backup_size = backup_path.stat().st_size
            logger.info(f"Backup created: {backup_size:,} bytes")
            
            # Compress backup if enabled
            if COMPRESS_BACKUPS:
                compressed_path = self._compress_backup(backup_path)
                if compressed_path:
                    backup_path.unlink()  # Remove uncompressed file
                    backup_path = compressed_path
                    logger.info(f"Backup compressed: {backup_path}")
            
            # Verify backup if enabled
            if VERIFY_BACKUPS:
                if self._verify_backup(backup_path):
                    logger.info("Backup verification successful")
                else:
                    logger.error("Backup verification failed")
                    self._send_alert("Backup verification failed")
                    return None
            
            logger.info(f"Backup completed successfully: {backup_path}")
            return backup_path
            
        except subprocess.TimeoutExpired:
            logger.error("Backup timeout - database might be too large or busy")
            self._send_alert("Backup timeout")
            return None
        except Exception as e:
            logger.error(f"Backup failed with exception: {e}")
            self._send_alert(f"Backup failed: {e}")
            return None
    
    def _compress_backup(self, backup_path):
        """Compress backup file with gzip"""
        compressed_path = backup_path.with_suffix(backup_path.suffix + '.gz')
        
        try:
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Check compression ratio
            original_size = backup_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Compression ratio: {ratio:.1f}% ({original_size:,} → {compressed_size:,} bytes)")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None
    
    def _verify_backup(self, backup_path):
        """Verify backup integrity"""
        try:
            # For compressed files, decompress and check
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rt') as f:
                    first_line = f.readline()
                    # Check for MySQL dump header
                    if not first_line.startswith('-- MySQL dump'):
                        return False
                    
                    # Read a few more lines to ensure it's valid
                    for _ in range(10):
                        line = f.readline()
                        if not line:
                            break
            else:
                with open(backup_path, 'r') as f:
                    first_line = f.readline()
                    if not first_line.startswith('-- MySQL dump'):
                        return False
            
            # Additional check: try to count tables
            table_count = self._count_tables_in_backup(backup_path)
            if table_count < 50:  # We expect at least 50 tables
                logger.warning(f"Backup contains only {table_count} tables - might be incomplete")
                return False
            
            logger.info(f"Backup verification passed: {table_count} tables found")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification error: {e}")
            return False
    
    def _count_tables_in_backup(self, backup_path):
        """Count CREATE TABLE statements in backup"""
        table_count = 0
        
        try:
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rt') as f:
                    for line in f:
                        if line.startswith('CREATE TABLE'):
                            table_count += 1
            else:
                with open(backup_path, 'r') as f:
                    for line in f:
                        if line.startswith('CREATE TABLE'):
                            table_count += 1
        except Exception as e:
            logger.error(f"Error counting tables: {e}")
            
        return table_count
    
    def cleanup_old_backups(self):
        """Remove old backup files"""
        logger.info("Cleaning up old backups...")
        
        # Get all backup files
        backup_files = []
        for pattern in ['*.sql', '*.sql.gz']:
            backup_files.extend(self.backup_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Keep MAX_BACKUPS newest files
        files_to_delete = backup_files[MAX_BACKUPS:]
        
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"Deleted old backup: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {deleted_count} old backups deleted, {len(backup_files) - deleted_count} kept")
    
    def _send_alert(self, message):
        """Send email alert about backup issues"""
        if not SEND_EMAIL_ALERTS:
            return
        
        try:
            # Email configuration
            smtp_server = os.getenv('MAIL_SERVER', 'mail.sertifikatet.no')
            smtp_port = int(os.getenv('MAIL_PORT', 587))
            smtp_username = os.getenv('ADMIN_MAIL_USERNAME', 'info@sertifikatet.no')
            smtp_password = os.getenv('ADMIN_MAIL_PASSWORD')
            admin_email = os.getenv('SUPER_ADMIN_EMAIL', 'viktorandreas@hotmail.com')
            
            if not smtp_password:
                logger.error("Cannot send alert: ADMIN_MAIL_PASSWORD not configured")
                return
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f'Sertifikatet Backup System <{smtp_username}>'
            msg['To'] = admin_email
            msg['Subject'] = f'🚨 Database Backup Alert - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            
            body = f"""
Database Backup Alert
=====================

Timestamp: {datetime.now().isoformat()}
Server: {os.getenv('SERVER_NAME', 'localhost')}
Database: {self.db_config['database']}

Issue: {message}

Please check the backup system immediately.

Best regards,
Sertifikatet Backup System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {admin_email}")
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
    
    def get_backup_status(self):
        """Get status of recent backups"""
        backup_files = list(self.backup_dir.glob('*.sql*'))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        status = {
            'total_backups': len(backup_files),
            'latest_backup': None,
            'backup_sizes': [],
            'disk_usage': sum(f.stat().st_size for f in backup_files)
        }
        
        if backup_files:
            latest = backup_files[0]
            status['latest_backup'] = {
                'filename': latest.name,
                'created': datetime.fromtimestamp(latest.stat().st_mtime),
                'size': latest.stat().st_size
            }
            
            # Get recent backup sizes for trend analysis
            for backup_file in backup_files[:7]:  # Last 7 backups
                status['backup_sizes'].append({
                    'date': datetime.fromtimestamp(backup_file.stat().st_mtime),
                    'size': backup_file.stat().st_size
                })
        
        return status


def main():
    """Main backup function"""
    logger.info("=" * 60)
    logger.info("STARTING DATABASE BACKUP")
    logger.info("=" * 60)
    
    backup_system = DatabaseBackup()
    
    try:
        # Create backup
        backup_path = backup_system.create_backup()
        
        if backup_path:
            # Cleanup old backups
            backup_system.cleanup_old_backups()
            
            # Show backup status
            status = backup_system.get_backup_status()
            logger.info(f"Backup system status:")
            logger.info(f"  Total backups: {status['total_backups']}")
            logger.info(f"  Disk usage: {status['disk_usage']:,} bytes")
            
            if status['latest_backup']:
                logger.info(f"  Latest backup: {status['latest_backup']['filename']}")
                logger.info(f"  Created: {status['latest_backup']['created']}")
                logger.info(f"  Size: {status['latest_backup']['size']:,} bytes")
            
            logger.info("DATABASE BACKUP COMPLETED SUCCESSFULLY")
            return True
        else:
            logger.error("DATABASE BACKUP FAILED")
            return False
            
    except Exception as e:
        logger.error(f"Backup script failed: {e}")
        backup_system._send_alert(f"Backup script exception: {e}")
        return False
    
    finally:
        logger.info("=" * 60)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
