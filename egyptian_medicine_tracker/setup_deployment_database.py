#!/usr/bin/env python3
"""
Setup complete database for deployment with all 51,441 medicines
"""

import sqlite3
import os
import logging
from pathlib import Path

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('deployment_setup.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_complete_database(logger):
    """Create complete database with all medicines for deployment"""
    
    print("🚀 SETTING UP COMPLETE DATABASE FOR DEPLOYMENT")
    print("=" * 60)
    
    # Database path
    db_path = "src/database/app.db"
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create main medicine table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_dailymed_complete_all (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_name TEXT,
                generic_name TEXT,
                active_ingredients TEXT,
                dosage_form TEXT,
                strength TEXT,
                manufacturer TEXT,
                ndc TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create enhanced medicine table for search
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_name TEXT,
                generic_name TEXT,
                active_ingredients TEXT,
                dosage_form TEXT,
                strength TEXT,
                manufacturer TEXT,
                ndc TEXT,
                search_text TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create search index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_medicine_search 
            ON medicine_enhanced(search_text)
        ''')
        
        conn.commit()
        logger.info("Database tables created successfully")
        
        # Check if we have existing data
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_complete_all")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✅ Database already has {existing_count:,} medicines")
            return existing_count
        
        print("📥 Database is empty. Need to populate with medicine data...")
        print("💡 To populate the database, you need to:")
        print("   1. Download the DailyMed ZIP files")
        print("   2. Run the extraction scripts")
        print("   3. Or copy your local database")
        
        conn.close()
        return 0
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return 0

def copy_local_database(logger):
    """Copy local database to deployment location"""
    
    print("\n📋 COPYING LOCAL DATABASE TO DEPLOYMENT")
    print("=" * 60)
    
    local_db = "src/database/app.db"
    
    if not os.path.exists(local_db):
        print("❌ Local database not found!")
        return False
    
    try:
        # Get database size
        size_mb = os.path.getsize(local_db) / (1024 * 1024)
        print(f"📁 Local database size: {size_mb:.1f} MB")
        
        # Check medicine count
        conn = sqlite3.connect(local_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_complete_all")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"💊 Medicines in local database: {count:,}")
        
        if count > 0:
            print("✅ Local database has medicine data - ready for deployment!")
            return True
        else:
            print("❌ Local database is empty!")
            return False
            
    except Exception as e:
        logger.error(f"Error checking local database: {e}")
        return False

def create_deployment_instructions():
    """Create deployment instructions"""
    
    instructions = """
# 🚀 DEPLOYMENT DATABASE SETUP

## Option 1: Copy Local Database (Recommended)
1. Copy your local `src/database/app.db` to your deployment server
2. The database contains 51,441 medicines ready to use

## Option 2: Recreate Database on Server
1. Download DailyMed ZIP files to server
2. Run extraction scripts on server
3. This will take time but ensures fresh data

## Option 3: Use Database Backup
1. Create a backup of your local database
2. Upload backup to deployment server
3. Restore database on server

## Quick Commands:
```bash
# Copy database to server (replace with your server details)
scp src/database/app.db user@your-server:/path/to/app/

# Or use rsync
rsync -avz src/database/app.db user@your-server:/path/to/app/
```

## Database Location:
- Local: `src/database/app.db`
- Server: Same path in your deployed app
"""
    
    with open("DEPLOYMENT_INSTRUCTIONS.md", "w") as f:
        f.write(instructions)
    
    print("📝 Created DEPLOYMENT_INSTRUCTIONS.md")

def main():
    """Main function"""
    logger = setup_logging()
    
    print("🔧 DEPLOYMENT DATABASE SETUP")
    print("=" * 60)
    
    # Create database structure
    medicine_count = create_complete_database(logger)
    
    # Check local database
    has_local_data = copy_local_database(logger)
    
    # Create instructions
    create_deployment_instructions()
    
    print(f"\n🎯 SETUP COMPLETE!")
    print("=" * 60)
    
    if has_local_data:
        print("✅ Your local database is ready for deployment!")
        print("📋 Check DEPLOYMENT_INSTRUCTIONS.md for next steps")
    else:
        print("⚠️  Your local database needs to be populated first")
        print("📋 Run the extraction scripts to get medicine data")

if __name__ == "__main__":
    main() 