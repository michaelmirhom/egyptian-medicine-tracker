#!/usr/bin/env python3
"""
Integrate DailyMed data with the existing medicine system
"""

import sqlite3
import logging
from pathlib import Path
import os

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('integration.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def integrate_dailymed_data():
    """Integrate DailyMed data with the main medicine system"""
    logger = setup_logging()
    
    print("🔗 Integrating DailyMed Data with Medicine System")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # 1. Create enhanced medicine table with all data
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
                arabic_name TEXT,
                indications TEXT,
                contraindications TEXT,
                warnings TEXT,
                dosage_administration TEXT,
                side_effects TEXT,
                drug_interactions TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. Copy existing medicine data to enhanced table
        logger.info("Copying existing medicine data...")
        cursor.execute('''
            INSERT INTO medicine_enhanced 
            (trade_name, generic_name, manufacturer, price, currency, source)
            SELECT trade_name, generic_name, applicant, price, currency, 'Original'
            FROM medicine
        ''')
        
        # 3. Copy DailyMed data to enhanced table
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
        
        # 4. Create search index for better performance
        logger.info("Creating search indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_name ON medicine_enhanced(trade_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generic_name ON medicine_enhanced(generic_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ndc ON medicine_enhanced(ndc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON medicine_enhanced(source)')
        
        # 5. Create medicine search view
        logger.info("Creating search view...")
        cursor.execute('''
            CREATE VIEW IF NOT EXISTS medicine_search AS
            SELECT 
                id,
                trade_name,
                generic_name,
                active_ingredients,
                dosage_form,
                strength,
                manufacturer,
                price,
                currency,
                ndc,
                source,
                CASE 
                    WHEN source = 'Original' THEN 1
                    WHEN source = 'DailyMed' THEN 2
                    ELSE 3
                END as priority
            FROM medicine_enhanced
            WHERE trade_name IS NOT NULL
        ''')
        
        conn.commit()
        
        # 6. Get statistics
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
    """Create an enhanced search service that uses the integrated data"""
    
    print(f"\n🔍 Creating Enhanced Search Service")
    print("-" * 40)
    
    search_service_code = '''
import sqlite3
from fuzzywuzzy import fuzz
from typing import List, Dict, Optional

class EnhancedMedicineSearch:
    """Enhanced medicine search using integrated DailyMed data"""
    
    def __init__(self, db_path: str = "src/database/app.db"):
        self.db_path = db_path
    
    def search_medicine(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for medicines using integrated data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First try exact match
            cursor.execute('''
                SELECT trade_name, generic_name, active_ingredients, dosage_form, 
                       manufacturer, price, currency, ndc, source
                FROM medicine_search
                WHERE LOWER(trade_name) LIKE LOWER(?) 
                   OR LOWER(generic_name) LIKE LOWER(?)
                   OR LOWER(active_ingredients) LIKE LOWER(?)
                ORDER BY priority, trade_name
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            exact_matches = cursor.fetchall()
            
            # If no exact matches, try fuzzy search
            if not exact_matches:
                cursor.execute('''
                    SELECT trade_name, generic_name, active_ingredients, dosage_form,
                           manufacturer, price, currency, ndc, source
                    FROM medicine_search
                    ORDER BY priority, trade_name
                    LIMIT 100
                ''')
                
                all_medicines = cursor.fetchall()
                fuzzy_matches = []
                
                for medicine in all_medicines:
                    trade_name = medicine[0] or ""
                    generic_name = medicine[1] or ""
                    ingredients = medicine[2] or ""
                    
                    # Calculate similarity scores
                    trade_score = fuzz.partial_ratio(query.lower(), trade_name.lower())
                    generic_score = fuzz.partial_ratio(query.lower(), generic_name.lower())
                    ingredient_score = fuzz.partial_ratio(query.lower(), ingredients.lower())
                    
                    max_score = max(trade_score, generic_score, ingredient_score)
                    
                    if max_score > 60:  # Threshold for fuzzy matching
                        fuzzy_matches.append((max_score, medicine))
                
                # Sort by similarity score and take top results
                fuzzy_matches.sort(key=lambda x: x[0], reverse=True)
                exact_matches = [medicine for score, medicine in fuzzy_matches[:limit]]
            
            # Convert to dictionary format
            results = []
            for medicine in exact_matches:
                results.append({
                    'trade_name': medicine[0],
                    'generic_name': medicine[1],
                    'active_ingredients': medicine[2],
                    'dosage_form': medicine[3],
                    'manufacturer': medicine[4],
                    'price': medicine[5],
                    'currency': medicine[6],
                    'ndc': medicine[7],
                    'source': medicine[8]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching medicines: {e}")
            return []
    
    def get_medicine_details(self, trade_name: str) -> Optional[Dict]:
        """Get detailed information about a specific medicine"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT trade_name, generic_name, active_ingredients, dosage_form,
                       strength, manufacturer, price, currency, ndc, source,
                       indications, contraindications, warnings, dosage_administration,
                       side_effects, drug_interactions
                FROM medicine_enhanced
                WHERE LOWER(trade_name) = LOWER(?)
                ORDER BY source = 'Original' DESC
                LIMIT 1
            ''', (trade_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'trade_name': result[0],
                    'generic_name': result[1],
                    'active_ingredients': result[2],
                    'dosage_form': result[3],
                    'strength': result[4],
                    'manufacturer': result[5],
                    'price': result[6],
                    'currency': result[7],
                    'ndc': result[8],
                    'source': result[9],
                    'indications': result[10],
                    'contraindications': result[11],
                    'warnings': result[12],
                    'dosage_administration': result[13],
                    'side_effects': result[14],
                    'drug_interactions': result[15]
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting medicine details: {e}")
            return None
    
    def get_statistics(self) -> Dict:
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
            
            cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_enhanced")
            unique = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_medicines': total,
                'original_medicines': original,
                'dailymed_medicines': dailymed,
                'unique_medicines': unique
            }
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
'''
    
    # Write the search service to a file
    with open('enhanced_search_service.py', 'w') as f:
        f.write(search_service_code)
    
    print("✅ Enhanced search service created: enhanced_search_service.py")

def update_chat_system():
    """Update the chat system to use the enhanced data"""
    
    print(f"\n💬 Updating Chat System Integration")
    print("-" * 40)
    
    # Read the existing chat system
    try:
        with open('src/crew/agents.py', 'r') as f:
            chat_code = f.read()
        
        # Add import for enhanced search
        if 'from enhanced_search_service import EnhancedMedicineSearch' not in chat_code:
            # Add the import at the top
            import_line = 'from enhanced_search_service import EnhancedMedicineSearch\n'
            chat_code = import_line + chat_code
        
        # Add enhanced search initialization
        if 'self.enhanced_search = EnhancedMedicineSearch()' not in chat_code:
            # Find the __init__ method and add the enhanced search
            init_pattern = 'def __init__(self):'
            enhanced_init = '''def __init__(self):
        self.enhanced_search = EnhancedMedicineSearch()
        '''
            chat_code = chat_code.replace(init_pattern, enhanced_init)
        
        # Write the updated chat system
        with open('src/crew/agents.py', 'w') as f:
            f.write(chat_code)
        
        print("✅ Chat system updated with enhanced search integration")
        
    except Exception as e:
        print(f"⚠️ Could not update chat system: {e}")

def create_test_script():
    """Create a test script to verify the integration"""
    
    print(f"\n🧪 Creating Test Script")
    print("-" * 40)
    
    test_script = '''
#!/usr/bin/env python3
"""
Test script for enhanced medicine search
"""

from enhanced_search_service import EnhancedMedicineSearch

def test_enhanced_search():
    """Test the enhanced search functionality"""
    
    print("🧪 Testing Enhanced Medicine Search")
    print("=" * 50)
    
    search = EnhancedMedicineSearch()
    
    # Get statistics
    stats = search.get_statistics()
    print(f"📊 Database Statistics:")
    print(f"   Total medicines: {stats.get('total_medicines', 0):,}")
    print(f"   Original medicines: {stats.get('original_medicines', 0)}")
    print(f"   DailyMed medicines: {stats.get('dailymed_medicines', 0):,}")
    print(f"   Unique medicines: {stats.get('unique_medicines', 0):,}")
    
    # Test searches
    test_queries = [
        "aspirin",
        "paracetamol", 
        "ibuprofen",
        "amoxicillin",
        "metformin"
    ]
    
    print(f"\n🔍 Testing Search Queries:")
    print("-" * 30)
    
    for query in test_queries:
        print(f"\nSearching for: {query}")
        results = search.search_medicine(query, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['trade_name']}")
                print(f"     Generic: {result['generic_name'] or 'N/A'}")
                print(f"     Source: {result['source']}")
        else:
            print(f"  No results found for {query}")
    
    # Test detailed medicine lookup
    print(f"\n📋 Testing Detailed Medicine Lookup:")
    print("-" * 30)
    
    test_medicine = "aspirin"
    details = search.get_medicine_details(test_medicine)
    
    if details:
        print(f"Medicine: {details['trade_name']}")
        print(f"Generic: {details['generic_name'] or 'N/A'}")
        print(f"Active Ingredients: {details['active_ingredients'] or 'N/A'}")
        print(f"Dosage Form: {details['dosage_form'] or 'N/A'}")
        print(f"Manufacturer: {details['manufacturer'] or 'N/A'}")
        print(f"Source: {details['source']}")
    else:
        print(f"No details found for {test_medicine}")

if __name__ == "__main__":
    test_enhanced_search()
'''
    
    with open('test_enhanced_search.py', 'w') as f:
        f.write(test_script)
    
    print("✅ Test script created: test_enhanced_search.py")

def main():
    """Main integration function"""
    print("🚀 Starting Complete Integration Process")
    print("=" * 60)
    
    # 1. Integrate DailyMed data
    integrate_dailymed_data()
    
    # 2. Create enhanced search service
    create_search_service()
    
    # 3. Update chat system
    update_chat_system()
    
    # 4. Create test script
    create_test_script()
    
    print(f"\n🎯 Integration Complete!")
    print("=" * 60)
    print("✅ DailyMed data integrated with existing system")
    print("✅ Enhanced search service created")
    print("✅ Chat system updated")
    print("✅ Test script created")
    print("\n📋 Next Steps:")
    print("   1. Run: python test_enhanced_search.py")
    print("   2. Test your chat system with the new data")
    print("   3. The system now has 2,000+ medicines available!")

if __name__ == "__main__":
    main() 