#!/usr/bin/env python3
"""
Comprehensive Database Summary - Shows all extracted medicine data
"""

import sqlite3
import os

def database_summary():
    """Show comprehensive database summary"""
    
    print("🏥 Egyptian Medicine Tracker - Database Summary")
    print("=" * 70)
    
    # Connect to database
    db_path = "src/database/app.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📋 Database Tables:")
        print("-" * 40)
        
        total_records = 0
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            print(f"   {table_name}: {count:,} records")
        
        print(f"\n📊 Total Records: {total_records:,}")
        
        # Show DailyMed data specifically
        print(f"\n🔬 DailyMed Data Analysis:")
        print("-" * 40)
        
        # Check both DailyMed tables
        dailymed_tables = ['medicine_dailymed', 'medicine_dailymed_improved']
        
        for table in dailymed_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"\n📄 {table}: {count:,} records")
                
                # Get sample data
                cursor.execute(f"""
                    SELECT trade_name, generic_name, dosage_form, ndc
                    FROM {table}
                    WHERE trade_name IS NOT NULL
                    ORDER BY id
                    LIMIT 5
                """)
                
                samples = cursor.fetchall()
                print(f"   Sample medicines:")
                for i, sample in enumerate(samples, 1):
                    trade_name, generic_name, dosage_form, ndc = sample
                    print(f"     {i}. {trade_name}")
                    print(f"        Generic: {generic_name or 'N/A'}")
                    print(f"        Dosage Form: {dosage_form or 'N/A'}")
                    print(f"        NDC: {ndc or 'N/A'}")
        
        # Show original medicine data
        print(f"\n💊 Original Medicine Data:")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM medicine")
        original_count = cursor.fetchone()[0]
        print(f"   Original medicines: {original_count}")
        
        if original_count > 0:
            cursor.execute("""
                SELECT trade_name, generic_name, price, manufacturer
                FROM medicine
                ORDER BY id
                LIMIT 3
            """)
            
            original_samples = cursor.fetchall()
            print(f"   Sample original medicines:")
            for i, sample in enumerate(original_samples, 1):
                trade_name, generic_name, price, manufacturer = sample
                print(f"     {i}. {trade_name}")
                print(f"        Generic: {generic_name}")
                print(f"        Price: {price} EGP")
                print(f"        Manufacturer: {manufacturer}")
        
        # Show user data
        print(f"\n👥 User Data:")
        print("-" * 40)
        
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"   Users: {user_count}")
        
        # Show database file size
        file_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        print(f"\n💾 Database Size: {file_size:.2f} MB")
        
        # Summary
        print(f"\n🎯 Summary:")
        print("-" * 40)
        print(f"   • Total medicine records: {total_records:,}")
        
        # Calculate DailyMed total
        dailymed_total = 0
        for table in dailymed_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                dailymed_total += cursor.fetchone()[0]
            except:
                pass
        print(f"   • DailyMed data: {dailymed_total:,}")
        print(f"   • Original medicines: {original_count}")
        print(f"   • Users: {user_count}")
        print(f"   • Database size: {file_size:.2f} MB")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    database_summary() 