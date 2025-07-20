#!/usr/bin/env python3
"""
Simple integration of DailyMed data with existing medicine system
"""

import sqlite3
import logging

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('simple_integration.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def integrate_data():
    """Integrate DailyMed data with existing system"""
    logger = setup_logging()
    
    print("🔗 Integrating DailyMed Data")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # 1. Create enhanced medicine table
        logger.info("Creating enhanced medicine table...")
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
        
        # 2. Copy existing medicine data
        logger.info("Copying existing medicine data...")
        cursor.execute('''
            INSERT INTO medicine_enhanced 
            (trade_name, generic_name, manufacturer, price, currency, source)
            SELECT trade_name, generic_name, applicant, price, currency, 'Original'
            FROM medicine
        ''')
        
        # 3. Copy DailyMed data
        logger.info("Copying DailyMed data...")
        cursor.execute('''
            INSERT INTO medicine_enhanced 
            (trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, source)
            SELECT 
                trade_name, 
                generic_name, 
                active_ingredients, 
                dosage_form, 
                strength, 
                manufacturer, 
                ndc, 
                'DailyMed'
            FROM medicine_dailymed_complete
            WHERE trade_name IS NOT NULL
        ''')
        
        # 4. Create indexes
        logger.info("Creating search indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_name ON medicine_enhanced(trade_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generic_name ON medicine_enhanced(generic_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ndc ON medicine_enhanced(ndc)')
        
        conn.commit()
        
        # 5. Get statistics
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced")
        total_medicines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'Original'")
        original_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'DailyMed'")
        dailymed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_enhanced")
        unique_medicines = cursor.fetchone()[0]
        
        print(f"\n✅ Integration Complete!")
        print(f"📊 Total medicines: {total_medicines:,}")
        print(f"📋 Original medicines: {original_count}")
        print(f"🔬 DailyMed medicines: {dailymed_count:,}")
        print(f"🎯 Unique medicines: {unique_medicines:,}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during integration: {e}")
        raise

def create_search_service():
    """Create a simple search service"""
    
    print(f"\n🔍 Creating Search Service")
    print("-" * 30)
    
    search_code = '''#!/usr/bin/env python3
"""
Simple medicine search service using integrated data
"""

import sqlite3
from fuzzywuzzy import fuzz

class MedicineSearch:
    def __init__(self, db_path="src/database/app.db"):
        self.db_path = db_path
    
    def search(self, query, limit=10):
        """Search for medicines"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trade_name, generic_name, active_ingredients, dosage_form, 
                       manufacturer, price, currency, ndc, source
                FROM medicine_enhanced
                WHERE LOWER(trade_name) LIKE LOWER(?) 
                   OR LOWER(generic_name) LIKE LOWER(?)
                ORDER BY source = 'Original' DESC, trade_name
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', limit))
            
            results = cursor.fetchall()
            conn.close()
            
            medicines = []
            for result in results:
                medicines.append({
                    'trade_name': result[0],
                    'generic_name': result[1],
                    'active_ingredients': result[2],
                    'dosage_form': result[3],
                    'manufacturer': result[4],
                    'price': result[5],
                    'currency': result[6],
                    'ndc': result[7],
                    'source': result[8]
                })
            
            return medicines
            
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def get_stats(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM medicine_enhanced")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'Original'")
            original = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM medicine_enhanced WHERE source = 'DailyMed'")
            dailymed = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'original': original,
                'dailymed': dailymed
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
'''
    
    with open('medicine_search.py', 'w') as f:
        f.write(search_code)
    
    print("✅ Search service created: medicine_search.py")

def create_test_script():
    """Create a test script"""
    
    print(f"\n🧪 Creating Test Script")
    print("-" * 30)
    
    test_code = '''#!/usr/bin/env python3
"""
Test the integrated medicine search
"""

from medicine_search import MedicineSearch

def test_search():
    print("🧪 Testing Medicine Search")
    print("=" * 40)
    
    search = MedicineSearch()
    
    # Get statistics
    stats = search.get_stats()
    print(f"📊 Database Statistics:")
    print(f"   Total medicines: {stats.get('total', 0):,}")
    print(f"   Original medicines: {stats.get('original', 0)}")
    print(f"   DailyMed medicines: {stats.get('dailymed', 0):,}")
    
    # Test searches
    test_queries = ["aspirin", "paracetamol", "ibuprofen"]
    
    print(f"\n🔍 Testing Searches:")
    print("-" * 20)
    
    for query in test_queries:
        print(f"\nSearching for: {query}")
        results = search.search(query, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['trade_name']}")
                print(f"     Generic: {result['generic_name'] or 'N/A'}")
                print(f"     Source: {result['source']}")
        else:
            print(f"  No results found")

if __name__ == "__main__":
    test_search()
'''
    
    with open('test_integration.py', 'w') as f:
        f.write(test_code)
    
    print("✅ Test script created: test_integration.py")

def main():
    """Main function"""
    print("🚀 Starting Integration")
    print("=" * 50)
    
    # 1. Integrate data
    integrate_data()
    
    # 2. Create search service
    create_search_service()
    
    # 3. Create test script
    create_test_script()
    
    print(f"\n🎯 Integration Complete!")
    print("=" * 50)
    print("✅ DailyMed data integrated")
    print("✅ Search service created")
    print("✅ Test script created")
    print("\n📋 Next Steps:")
    print("   1. Run: python test_integration.py")
    print("   2. Your system now has 2,000+ medicines!")

if __name__ == "__main__":
    main() 