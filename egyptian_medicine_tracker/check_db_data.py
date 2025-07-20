#!/usr/bin/env python3
"""
Script to check database statistics and data counts
"""

import sqlite3
import os
from pathlib import Path

def check_database_data():
    """Check the data in the SQLite database"""
    
    # Find the database file
    db_paths = [
        "src/database/app.db",
        "app.db",
        "instance/app.db"
    ]
    
    db_file = None
    for path in db_paths:
        if os.path.exists(path):
            db_file = path
            break
    
    if not db_file:
        print("❌ Database file not found!")
        return
    
    print(f"📊 Database file: {db_file}")
    print(f"📁 File size: {os.path.getsize(db_file) / 1024:.2f} KB")
    print("-" * 50)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📋 Database Tables and Record Counts:")
        print("=" * 50)
        
        total_records = 0
        
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                
                # Get sample data structure
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                print(f"📄 {table_name}: {count:,} records")
                print(f"   Columns: {', '.join(column_names)}")
                
                # Show sample data for small tables
                if count > 0 and count <= 5:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"   Sample data:")
                    for i, sample in enumerate(samples, 1):
                        print(f"     {i}. {sample}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error reading table {table_name}: {e}")
        
        print("=" * 50)
        print(f"📈 Total records across all tables: {total_records:,}")
        
        # Check database info
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchall()
        print(f"🗄️  Database version: {db_info[0][2] if db_info else 'Unknown'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")

if __name__ == "__main__":
    check_database_data() 