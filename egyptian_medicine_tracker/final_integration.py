#!/usr/bin/env python3
"""
Final integration of DailyMed data
"""

import sqlite3

def main():
    print("🔗 Final Integration of DailyMed Data")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Create enhanced table
        print("Creating enhanced medicine table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_enhanced (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_name TEXT,
                generic_name TEXT,
                active_ingredients TEXT,
                dosage_form TEXT,
                strength TEXT,
                manufacturer TEXT,
                price REAL,
                currency TEXT DEFAULT 'EGP',
                ndc TEXT,
                source TEXT DEFAULT 'DailyMed',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Copy existing data
        print("Copying existing medicine data...")
        cursor.execute('''
            INSERT INTO medicine_enhanced 
            (trade_name, generic_name, manufacturer, price, currency, source)
            SELECT trade_name, generic_name, applicant, price, currency, 'Original'
            FROM medicine
        ''')
        
        # Copy DailyMed data
        print("Copying DailyMed data...")
        cursor.execute('''
            INSERT INTO medicine_enhanced 
            (trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, source)
            SELECT trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, 'DailyMed'
            FROM medicine_dailymed_complete
            WHERE trade_name IS NOT NULL
        ''')
        
        # Create indexes
        print("Creating search indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_name ON medicine_enhanced(trade_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generic_name ON medicine_enhanced(generic_name)')
        
        conn.commit()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'Original'")
        original = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'DailyMed'")
        dailymed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_enhanced")
        unique = cursor.fetchone()[0]
        
        print(f"\n✅ Integration Complete!")
        print(f"📊 Total medicines: {total:,}")
        print(f"📋 Original medicines: {original}")
        print(f"🔬 DailyMed medicines: {dailymed:,}")
        print(f"🎯 Unique medicines: {unique:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 