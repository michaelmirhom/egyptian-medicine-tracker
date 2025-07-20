#!/usr/bin/env python3
"""
Check improved DailyMed data extraction results
"""

import sqlite3
import os

def check_improved_data():
    """Check the improved DailyMed data"""
    
    print("📊 Improved DailyMed Data Analysis")
    print("=" * 60)
    
    # Connect to database
    db_path = "src/database/app.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if improved table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medicine_dailymed_improved'")
        if not cursor.fetchone():
            print("❌ Improved DailyMed table not found!")
            return
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved")
        total_count = cursor.fetchone()[0]
        
        print(f"📈 Total records extracted: {total_count:,}")
        
        # Show sample medicines with better data
        print(f"\n💊 Sample Medicines with Improved Data (first 10):")
        print("-" * 60)
        
        cursor.execute("""
            SELECT trade_name, generic_name, manufacturer, active_ingredients, dosage_form, strength
            FROM medicine_dailymed_improved 
            WHERE trade_name IS NOT NULL 
            ORDER BY id 
            LIMIT 10
        """)
        
        medicines = cursor.fetchall()
        for i, medicine in enumerate(medicines, 1):
            trade_name, generic_name, manufacturer, ingredients, dosage_form, strength = medicine
            print(f"{i:2d}. {trade_name or 'N/A'}")
            print(f"    Generic: {generic_name or 'N/A'}")
            print(f"    Manufacturer: {manufacturer or 'N/A'}")
            print(f"    Ingredients: {ingredients or 'N/A'}")
            print(f"    Dosage Form: {dosage_form or 'N/A'}")
            print(f"    Strength: {strength or 'N/A'}")
            print()
        
        # Show statistics
        print(f"📊 Data Quality Statistics:")
        print("-" * 60)
        
        # Medicines with generic names
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved WHERE generic_name IS NOT NULL AND generic_name != ''")
        with_generic = cursor.fetchone()[0]
        print(f"Medicines with generic names: {with_generic} ({with_generic/total_count*100:.1f}%)")
        
        # Medicines with manufacturers
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved WHERE manufacturer IS NOT NULL AND manufacturer != ''")
        with_manufacturer = cursor.fetchone()[0]
        print(f"Medicines with manufacturers: {with_manufacturer} ({with_manufacturer/total_count*100:.1f}%)")
        
        # Medicines with active ingredients
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved WHERE active_ingredients IS NOT NULL AND active_ingredients != ''")
        with_ingredients = cursor.fetchone()[0]
        print(f"Medicines with active ingredients: {with_ingredients} ({with_ingredients/total_count*100:.1f}%)")
        
        # Medicines with NDC codes
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved WHERE ndc IS NOT NULL AND ndc != ''")
        with_ndc = cursor.fetchone()[0]
        print(f"Medicines with NDC codes: {with_ndc} ({with_ndc/total_count*100:.1f}%)")
        
        # Medicines with dosage forms
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_improved WHERE dosage_form IS NOT NULL AND dosage_form != ''")
        with_dosage_form = cursor.fetchone()[0]
        print(f"Medicines with dosage forms: {with_dosage_form} ({with_dosage_form/total_count*100:.1f}%)")
        
        # Show some complete records
        print(f"\n🔍 Complete Records (with most data):")
        print("-" * 60)
        
        cursor.execute("""
            SELECT trade_name, generic_name, manufacturer, active_ingredients, dosage_form, strength, ndc
            FROM medicine_dailymed_improved 
            WHERE generic_name IS NOT NULL AND generic_name != ''
            AND manufacturer IS NOT NULL AND manufacturer != ''
            AND active_ingredients IS NOT NULL AND active_ingredients != ''
            ORDER BY id 
            LIMIT 5
        """)
        
        complete_records = cursor.fetchall()
        for i, record in enumerate(complete_records, 1):
            trade_name, generic_name, manufacturer, ingredients, dosage_form, strength, ndc = record
            print(f"{i}. {trade_name}")
            print(f"   Generic: {generic_name}")
            print(f"   Manufacturer: {manufacturer}")
            print(f"   Ingredients: {ingredients}")
            print(f"   Dosage Form: {dosage_form}")
            print(f"   Strength: {strength}")
            print(f"   NDC: {ndc}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    check_improved_data() 