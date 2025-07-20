#!/usr/bin/env python3
"""
Check DailyMed processing status and show extracted data
"""

import sqlite3
import os
from pathlib import Path

def check_processing_status():
    """Check the status of DailyMed processing"""
    
    print("🔍 DailyMed Processing Status Check")
    print("=" * 50)
    
    # Check database
    db_path = "src/database/app.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if DailyMed table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medicine_dailymed'")
        if not cursor.fetchone():
            print("❌ DailyMed table not found - processing may not have started yet")
            return
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_dailymed WHERE trade_name IS NOT NULL")
        unique_medicines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT xml_source) FROM medicine_dailymed")
        xml_sources = cursor.fetchone()[0]
        
        print(f"📊 Processing Statistics:")
        print(f"   Total records: {total_records:,}")
        print(f"   Unique medicines: {unique_medicines:,}")
        print(f"   XML sources processed: {xml_sources}")
        
        # Show recent entries
        print(f"\n📋 Recent Entries (last 5):")
        cursor.execute("""
            SELECT trade_name, generic_name, manufacturer, xml_source 
            FROM medicine_dailymed 
            WHERE trade_name IS NOT NULL 
            ORDER BY processed_date DESC 
            LIMIT 5
        """)
        
        recent_entries = cursor.fetchall()
        for i, entry in enumerate(recent_entries, 1):
            trade_name, generic_name, manufacturer, xml_source = entry
            print(f"   {i}. {trade_name or 'N/A'}")
            print(f"      Generic: {generic_name or 'N/A'}")
            print(f"      Manufacturer: {manufacturer or 'N/A'}")
            print(f"      Source: {xml_source}")
            print()
        
        # Check extraction directories
        data_path = Path("Data")
        if data_path.exists():
            extracted_dirs = list(data_path.glob("extracted_*"))
            print(f"📁 Extraction Directories: {len(extracted_dirs)}")
            for dir_path in extracted_dirs:
                xml_files = list(dir_path.rglob("*.xml"))
                print(f"   {dir_path.name}: {len(xml_files)} XML files")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")

if __name__ == "__main__":
    check_processing_status() 