#!/usr/bin/env python3
"""
Database Restoration Script
Safely restore database from backup files
"""

import os
import sys
import subprocess
import gzip
from datetime import datetime
from pathlib import Path
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BACKUP_DIR = Path("backups/database")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class DatabaseRestore:
    """Handle MySQL database restoration from backups"""
    
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
    
    def list_backups(self):
        """List all available backup files"""
        backup_files = []
        
        # Find all backup files
        for pattern in ['*.sql', '*.sql.gz']:
            backup_files.extend(self.backup_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return backup_files
    
    def show_backup_info(self, backup_file):
        """Show information about a backup file"""
        stat = backup_file.stat()
        
        return {
            'filename': backup_file.name,
            'path': backup_file,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_mtime),
            'compressed': backup_file.suffix == '.gz'
        }
    
    def create_pre_restore_backup(self):
        """Create a backup before restoration (safety measure)"""
        logger.info("Creating pre-restoration backup...")
        
        from scripts.database_backup import DatabaseBackup
        backup_system = DatabaseBackup()
        
        # Create a timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_backup = backup_system.create_backup()
        
        if safety_backup:
            # Rename to indicate it's a pre-restore backup
            safety_name = f"pre_restore_{timestamp}_{safety_backup.name}"
            safety_path = safety_backup.parent / safety_name
            safety_backup.rename(safety_path)
            
            logger.info(f"Pre-restoration backup created: {safety_path}")
            return safety_path
        else:
            logger.error("Failed to create pre-restoration backup")
            return None
    
    def restore_from_backup(self, backup_file, create_safety_backup=True):
        """Restore database from a backup file"""
        logger.info(f"Starting restoration from: {backup_file}")
        
        # Verify backup file exists
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Create safety backup if requested
        if create_safety_backup:
            safety_backup = self.create_pre_restore_backup()
            if not safety_backup:
                logger.error("Safety backup failed - aborting restoration")
                return False
        
        try:
            # Build mysql command
            cmd = [
                'mysql',
                f'--host={self.db_config["host"]}',
                f'--port={self.db_config["port"]}',
                f'--user={self.db_config["user"]}',
                f'--password={self.db_config["password"]}',
                '--verbose',
                self.db_config['database']
            ]
            
            # Handle compressed files
            if backup_file.suffix == '.gz':
                logger.info("Decompressing backup file...")
                with gzip.open(backup_file, 'rt') as backup_content:
                    result = subprocess.run(
                        cmd,
                        input=backup_content.read(),
                        text=True,
                        capture_output=True,
                        timeout=3600  # 1 hour timeout
                    )
            else:
                with open(backup_file, 'r') as backup_content:
                    result = subprocess.run(
                        cmd,
                        input=backup_content.read(),
                        text=True,
                        capture_output=True,
                        timeout=3600  # 1 hour timeout
                    )
            
            if result.returncode != 0:
                logger.error(f"MySQL restoration failed: {result.stderr}")
                return False
            
            logger.info("Database restoration completed successfully")
            
            # Verify restoration
            if self._verify_restoration():
                logger.info("Restoration verification successful")
                return True
            else:
                logger.error("Restoration verification failed")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Restoration timeout")
            return False
        except Exception as e:
            logger.error(f"Restoration failed: {e}")
            return False
    
    def _verify_restoration(self):
        """Verify that restoration was successful"""
        try:
            import mysql.connector
            
            # Connect to database
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Check table count
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_count = len(tables)
            
            # Check user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # Check subscription plans
            cursor.execute("SELECT COUNT(*) FROM subscription_plans")
            plan_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            logger.info(f"Restoration verification:")
            logger.info(f"  Tables: {table_count}")
            logger.info(f"  Users: {user_count}")
            logger.info(f"  Subscription plans: {plan_count}")
            
            # Basic sanity checks
            if table_count < 50:
                logger.error(f"Too few tables after restoration: {table_count}")
                return False
            
            if plan_count < 3:
                logger.error(f"Missing subscription plans: {plan_count}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False


def interactive_restore():
    """Interactive restoration process"""
    print("🔄 DATABASE RESTORATION TOOL")
    print("=" * 50)
    
    restore_system = DatabaseRestore()
    
    # List available backups
    backups = restore_system.list_backups()
    
    if not backups:
        print("❌ No backup files found in:", restore_system.backup_dir)
        return False
    
    print(f"📁 Found {len(backups)} backup files:")
    print()
    
    # Show backup options
    for i, backup_file in enumerate(backups, 1):
        info = restore_system.show_backup_info(backup_file)
        size_mb = info['size'] / (1024 * 1024)
        compressed = " (compressed)" if info['compressed'] else ""
        
        print(f"{i:2d}. {info['filename']}")
        print(f"     Created: {info['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     Size: {size_mb:.1f} MB{compressed}")
        print()
    
    # Get user choice
    while True:
        try:
            choice = input(f"Select backup to restore (1-{len(backups)}) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                print("Restoration cancelled.")
                return False
            
            backup_index = int(choice) - 1
            if 0 <= backup_index < len(backups):
                selected_backup = backups[backup_index]
                break
            else:
                print(f"Please enter a number between 1 and {len(backups)}")
                
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
    
    # Confirm restoration
    info = restore_system.show_backup_info(selected_backup)
    print(f"\n⚠️  CONFIRMATION REQUIRED")
    print(f"You are about to restore from: {info['filename']}")
    print(f"Created: {info['created'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Size: {info['size'] / (1024 * 1024):.1f} MB")
    print()
    print("⚠️  WARNING: This will:")
    print("   • Create a safety backup of current database")
    print("   • Replace ALL current data with backup data")
    print("   • This action cannot be undone (except via the safety backup)")
    print()
    
    confirm = input("Type 'RESTORE' to confirm restoration: ").strip()
    
    if confirm != 'RESTORE':
        print("Restoration cancelled.")
        return False
    
    # Perform restoration
    print(f"\n🔄 Starting restoration from {info['filename']}...")
    success = restore_system.restore_from_backup(selected_backup)
    
    if success:
        print("✅ Database restoration completed successfully!")
        print("🎉 Your database has been restored from the backup.")
        return True
    else:
        print("❌ Database restoration failed!")
        print("💡 Check the logs above for error details.")
        print("💡 Your original database should still be intact.")
        return False


def main():
    """Main restoration function"""
    if len(sys.argv) > 1:
        # Non-interactive mode with backup file argument
        backup_file = Path(sys.argv[1])
        
        restore_system = DatabaseRestore()
        success = restore_system.restore_from_backup(backup_file)
        
        return success
    else:
        # Interactive mode
        return interactive_restore()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
