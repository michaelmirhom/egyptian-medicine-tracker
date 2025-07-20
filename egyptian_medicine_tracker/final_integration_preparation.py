#!/usr/bin/env python3
"""
Final Integration Preparation - Ready for complete dataset integration
"""

import sqlite3
import logging
from pathlib import Path

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('final_integration_prep.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_extraction_status():
    """Check the current extraction status"""
    logger = setup_logging()
    
    print("🔍 CHECKING EXTRACTION STATUS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Check all medicine tables
        tables = [
            'medicine', 
            'medicine_dailymed_complete', 
            'medicine_dailymed_complete_all', 
            'medicine_enhanced',
            'medicine_dailymed_final_complete'
        ]
        
        print("📊 Current Database Status:")
        print("-" * 30)
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(DISTINCT trade_name) FROM {table}")
                unique = cursor.fetchone()[0]
                
                print(f"   {table}: {count:,} records, {unique:,} unique medicines")
                
            except Exception as e:
                print(f"   {table}: Does not exist yet")
        
        conn.close()
        
        # Check extraction log
        log_file = Path("final_complete_extraction.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"\n📋 Extraction Log Status:")
                print(f"   Log file size: {log_file.stat().st_size} bytes")
                print(f"   Log entries: {len(lines)}")
                
                if lines:
                    last_line = lines[-1].strip()
                    print(f"   Last entry: {last_line}")
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")

def create_final_integration_plan():
    """Create the final integration plan"""
    
    print(f"\n🛠️ FINAL INTEGRATION PLAN")
    print("=" * 50)
    
    plan = """
    ## 🎯 FINAL INTEGRATION STRATEGY
    
    ### 1. Data Consolidation
    - Merge all medicine tables into one comprehensive table
    - Remove duplicates and standardize data format
    - Create unified medicine database
    
    ### 2. Enhanced Search System
    - Create optimized search indexes
    - Implement fuzzy matching for medicine names
    - Add advanced filtering capabilities
    
    ### 3. Chat System Enhancement
    - Update chat agents with complete medicine data
    - Implement fallback to local database
    - Add comprehensive medicine information responses
    
    ### 4. Performance Optimization
    - Create database indexes for fast queries
    - Implement caching for frequently accessed data
    - Optimize search algorithms
    
    ### 5. User Interface Updates
    - Enhanced search interface
    - Comprehensive medicine details display
    - Improved user experience
    """
    
    print(plan)

def create_integration_script():
    """Create the final integration script"""
    
    print(f"\n📝 CREATING FINAL INTEGRATION SCRIPT")
    print("-" * 40)
    
    integration_code = '''#!/usr/bin/env python3
"""
FINAL COMPLETE INTEGRATION - Merge all medicine data
"""

import sqlite3
import logging
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('final_integration.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def create_unified_medicine_table():
    """Create unified medicine table with all data"""
    logger = setup_logging()
    
    print("🔗 Creating Unified Medicine Database")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Create unified table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medicine_unified (
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
                source TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Copy original medicines
        print("Copying original medicines...")
        cursor.execute('''
            INSERT INTO medicine_unified 
            (trade_name, generic_name, manufacturer, price, currency, source)
            SELECT trade_name, generic_name, applicant, price, currency, 'Original'
            FROM medicine
        ''')
        
        # Copy final complete DailyMed data
        print("Copying complete DailyMed data...")
        cursor.execute('''
            INSERT INTO medicine_unified 
            (trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, source)
            SELECT trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, 'DailyMed'
            FROM medicine_dailymed_final_complete
            WHERE trade_name IS NOT NULL
        ''')
        
        # Create indexes
        print("Creating search indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_trade_name ON medicine_unified(trade_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_generic_name ON medicine_unified(generic_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_ndc ON medicine_unified(ndc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_unified_source ON medicine_unified(source)')
        
        conn.commit()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM medicine_unified")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_unified WHERE source = 'Original'")
        original = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medicine_unified WHERE source = 'DailyMed'")
        dailymed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_unified")
        unique = cursor.fetchone()[0]
        
        print(f"\\n✅ Unified Database Created!")
        print(f"📊 Total medicines: {total:,}")
        print(f"📋 Original medicines: {original}")
        print(f"🔬 DailyMed medicines: {dailymed:,}")
        print(f"🎯 Unique medicines: {unique:,}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating unified table: {e}")

def create_enhanced_search_service():
    """Create enhanced search service"""
    
    print(f"\\n🔍 Creating Enhanced Search Service")
    print("-" * 40)
    
    search_code = '''#!/usr/bin/env python3
"""
Enhanced Medicine Search Service
"""

import sqlite3
from fuzzywuzzy import fuzz
from typing import List, Dict, Optional

class UnifiedMedicineSearch:
    def __init__(self, db_path="src/database/app.db"):
        self.db_path = db_path
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for medicines using unified database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First try exact match
            cursor.execute('''
                SELECT trade_name, generic_name, active_ingredients, dosage_form, 
                       manufacturer, price, currency, ndc, source
                FROM medicine_unified
                WHERE LOWER(trade_name) LIKE LOWER(?) 
                   OR LOWER(generic_name) LIKE LOWER(?)
                   OR LOWER(active_ingredients) LIKE LOWER(?)
                ORDER BY source = 'Original' DESC, trade_name
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
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
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM medicine_unified")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM medicine_unified WHERE source = 'Original'")
            original = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM medicine_unified WHERE source = 'DailyMed'")
            dailymed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_unified")
            unique = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'original': original,
                'dailymed': dailymed,
                'unique': unique
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
'''
    
    with open('unified_medicine_search.py', 'w') as f:
        f.write(search_code)
    
    print("✅ Enhanced search service created: unified_medicine_search.py")

def main():
    """Main integration function"""
    print("🚀 FINAL INTEGRATION PREPARATION")
    print("=" * 50)
    
    # Check current status
    check_extraction_status()
    
    # Create integration plan
    create_final_integration_plan()
    
    # Create integration script
    create_integration_script()
    
    print(f"\\n🎯 PREPARATION COMPLETE!")
    print("=" * 50)
    print("✅ Status checked")
    print("✅ Integration plan created")
    print("✅ Integration script prepared")
    print("\\n📋 Ready for final integration once extraction completes!")

if __name__ == "__main__":
    main()
'''
    
    with open('final_integration_script.py', 'w') as f:
        f.write(integration_code)
    
    print("✅ Final integration script created: final_integration_script.py")

def main():
    """Main preparation function"""
    print("🚀 FINAL INTEGRATION PREPARATION")
    print("=" * 50)
    
    # Check current status
    check_extraction_status()
    
    # Create integration plan
    create_final_integration_plan()
    
    # Create integration script
    create_integration_script()
    
    print(f"\n🎯 PREPARATION COMPLETE!")
    print("=" * 50)
    print("✅ Status checked")
    print("✅ Integration plan created")
    print("✅ Integration script prepared")
    print("\n📋 Ready for final integration once extraction completes!")

if __name__ == "__main__":
    main() 