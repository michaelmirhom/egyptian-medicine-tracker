#!/usr/bin/env python3
"""
Show detailed information about extracted DailyMed data
"""

import sqlite3
import os

def show_extracted_data():
    """Show detailed information about extracted data"""
    
    print("📊 DailyMed Extracted Data Analysis")
    print("=" * 60)
    
    # Connect to database
    db_path = "src/database/app.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed")
        total_count = cursor.fetchone()[0]
        
        print(f"📈 Total records extracted: {total_count:,}")
        
        # Show sample medicines
        print(f"\n💊 Sample Medicines (first 10):")
        print("-" * 60)
        
        cursor.execute("""
            SELECT trade_name, generic_name, manufacturer, active_ingredients
            FROM medicine_dailymed 
            WHERE trade_name IS NOT NULL 
            ORDER BY id 
            LIMIT 10
        """)
        
        medicines = cursor.fetchall()
        for i, medicine in enumerate(medicines, 1):
            trade_name, generic_name, manufacturer, ingredients = medicine
            print(f"{i:2d}. {trade_name or 'N/A'}")
            print(f"    Generic: {generic_name or 'N/A'}")
            print(f"    Manufacturer: {manufacturer or 'N/A'}")
            print(f"    Ingredients: {ingredients or 'N/A'}")
            print()
        
        # Show statistics
        print(f"📊 Statistics:")
        print("-" * 60)
        
        # Unique manufacturers
        cursor.execute("SELECT COUNT(DISTINCT manufacturer) FROM medicine_dailymed WHERE manufacturer IS NOT NULL")
        unique_manufacturers = cursor.fetchone()[0]
        print(f"Unique manufacturers: {unique_manufacturers}")
        
        # Top manufacturers
        cursor.execute("""
            SELECT manufacturer, COUNT(*) as count 
            FROM medicine_dailymed 
            WHERE manufacturer IS NOT NULL 
            GROUP BY manufacturer 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_manufacturers = cursor.fetchall()
        print(f"\nTop manufacturers:")
        for manufacturer, count in top_manufacturers:
            print(f"  {manufacturer}: {count} medicines")
        
        # Medicines with NDC codes
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed WHERE ndc IS NOT NULL AND ndc != ''")
        with_ndc = cursor.fetchone()[0]
        print(f"\nMedicines with NDC codes: {with_ndc}")
        
        # Medicines with active ingredients
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed WHERE active_ingredients IS NOT NULL AND active_ingredients != ''")
        with_ingredients = cursor.fetchone()[0]
        print(f"Medicines with active ingredients: {with_ingredients}")
        
        # Show some interesting medicines
        print(f"\n🔍 Interesting Medicines:")
        print("-" * 60)
        
        # Medicines with multiple ingredients
        cursor.execute("""
            SELECT trade_name, active_ingredients 
            FROM medicine_dailymed 
            WHERE active_ingredients LIKE '%;%' 
            ORDER BY LENGTH(active_ingredients) DESC 
            LIMIT 5
        """)
        multi_ingredient = cursor.fetchall()
        print(f"Medicines with multiple ingredients:")
        for trade_name, ingredients in multi_ingredient:
            print(f"  {trade_name}: {ingredients}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")

if __name__ == "__main__":
    show_extracted_data() 