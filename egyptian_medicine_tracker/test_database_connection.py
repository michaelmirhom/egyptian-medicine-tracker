#!/usr/bin/env python3
"""
Test script to verify database connection and query functions
"""

import sqlite3
import os

def test_database_connection():
    """Test direct database connection and queries"""
    db_path = "deployment_database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='medicine_dailymed_complete_all'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Table 'medicine_dailymed_complete_all' not found")
            return False
        
        print("✅ Table 'medicine_dailymed_complete_all' exists")
        
        # Test 2: Check table structure
        cursor.execute("PRAGMA table_info(medicine_dailymed_complete_all)")
        columns = cursor.fetchall()
        print(f"✅ Table has {len(columns)} columns: {[col[1] for col in columns]}")
        
        # Test 3: Count total records
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_complete_all")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total records: {total_count}")
        
        # Test 4: Query for RENESE
        cursor.execute("""
            SELECT trade_name, generic_name, active_ingredients 
            FROM medicine_dailymed_complete_all 
            WHERE LOWER(trade_name) LIKE '%renese%' 
               OR LOWER(generic_name) LIKE '%renese%'
            LIMIT 5
        """)
        renese_results = cursor.fetchall()
        print(f"✅ RENESE query results: {len(renese_results)} records")
        for row in renese_results:
            print(f"   - Trade: '{row[0]}', Generic: '{row[1]}', Ingredients: '{row[2]}'")
        
        # Test 5: Query for Mykrox
        cursor.execute("""
            SELECT trade_name, generic_name, active_ingredients 
            FROM medicine_dailymed_complete_all 
            WHERE LOWER(trade_name) LIKE '%mykrox%' 
               OR LOWER(generic_name) LIKE '%mykrox%'
            LIMIT 5
        """)
        mykrox_results = cursor.fetchall()
        print(f"✅ Mykrox query results: {len(mykrox_results)} records")
        for row in mykrox_results:
            print(f"   - Trade: '{row[0]}', Generic: '{row[1]}', Ingredients: '{row[2]}'")
        
        # Test 6: Query for Tolinase
        cursor.execute("""
            SELECT trade_name, generic_name, active_ingredients 
            FROM medicine_dailymed_complete_all 
            WHERE LOWER(trade_name) LIKE '%tolinase%' 
               OR LOWER(generic_name) LIKE '%tolinase%'
            LIMIT 5
        """)
        tolinase_results = cursor.fetchall()
        print(f"✅ Tolinase query results: {len(tolinase_results)} records")
        for row in tolinase_results:
            print(f"   - Trade: '{row[0]}', Generic: '{row[1]}', Ingredients: '{row[2]}'")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_medicine_functions():
    """Test the medicine functions from the routes"""
    try:
        # Import the functions
        import sys
        sys.path.append('src')
        
        from routes.medicine import get_active_ingredients_from_database, get_medicine_usage_from_database
        
        print("\n🧪 Testing medicine functions...")
        
        # Test RENESE
        print("\n📋 Testing RENESE:")
        ingredients = get_active_ingredients_from_database("RENESE")
        print(f"   Ingredients: {ingredients}")
        
        usage = get_medicine_usage_from_database("RENESE")
        print(f"   Usage: {usage}")
        
        # Test Mykrox
        print("\n📋 Testing Mykrox:")
        ingredients = get_active_ingredients_from_database("Mykrox")
        print(f"   Ingredients: {ingredients}")
        
        usage = get_medicine_usage_from_database("Mykrox")
        print(f"   Usage: {usage}")
        
        # Test Tolinase
        print("\n📋 Testing Tolinase:")
        ingredients = get_active_ingredients_from_database("Tolinase")
        print(f"   Ingredients: {ingredients}")
        
        usage = get_medicine_usage_from_database("Tolinase")
        print(f"   Usage: {usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Function test error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Database Connection and Functions")
    print("=" * 50)
    
    # Test 1: Direct database connection
    db_success = test_database_connection()
    
    # Test 2: Medicine functions
    func_success = test_medicine_functions()
    
    print("\n" + "=" * 50)
    if db_success and func_success:
        print("✅ All tests passed! Database is working correctly.")
    else:
        print("❌ Some tests failed. Check the errors above.") 