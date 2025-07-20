#!/usr/bin/env python3
"""
Process nested ZIP files from DailyMed data
"""

import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import logging
from pathlib import Path
import os
import re

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('nested_zip_processing.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def setup_database():
    """Setup database connection"""
    conn = sqlite3.connect("src/database/app.db")
    cursor = conn.cursor()
    
    # Create DailyMed table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicine_dailymed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_id TEXT,
            trade_name TEXT,
            generic_name TEXT,
            active_ingredients TEXT,
            dosage_form TEXT,
            strength TEXT,
            manufacturer TEXT,
            ndc TEXT,
            rx_otc TEXT,
            application_number TEXT,
            labeler TEXT,
            package_description TEXT,
            indications TEXT,
            contraindications TEXT,
            warnings TEXT,
            dosage_administration TEXT,
            side_effects TEXT,
            drug_interactions TEXT,
            pregnancy_category TEXT,
            storage_conditions TEXT,
            xml_source TEXT,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn, cursor

def extract_dailymed_info(xml_content):
    """Extract information from DailyMed XML with proper namespace handling"""
    try:
        root = ET.fromstring(xml_content)
        
        # Define namespaces used in DailyMed XML
        namespaces = {
            'spl': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        info = {
            'set_id': '',
            'trade_name': '',
            'generic_name': '',
            'active_ingredients': '',
            'manufacturer': '',
            'ndc': '',
            'xml_source': 'unknown'
        }
        
        # Extract set ID
        set_id_elem = root.find('.//spl:setId', namespaces)
        if set_id_elem is not None and set_id_elem.text:
            info['set_id'] = set_id_elem.text.strip()
        
        # Extract title (trade name)
        title_elem = root.find('.//spl:title', namespaces)
        if title_elem is not None and title_elem.text:
            info['trade_name'] = title_elem.text.strip()
        
        # Extract manufacturer
        org_elem = root.find('.//spl:assignedEntity/spl:assignedOrganization/spl:name', namespaces)
        if org_elem is not None and org_elem.text:
            info['manufacturer'] = org_elem.text.strip()
        
        # Extract active ingredients
        ingredients = []
        ingredient_elems = root.findall('.//spl:ingredient[@classCode="ACTIM"]', namespaces)
        for elem in ingredient_elems:
            name_elem = elem.find('.//spl:ingredientSubstance/spl:name', namespaces)
            if name_elem is not None and name_elem.text:
                ingredients.append(name_elem.text.strip())
        info['active_ingredients'] = '; '.join(ingredients)
        
        # Extract NDC
        ndc_elem = root.find('.//spl:code[@codeSystem="2.16.840.1.113883.6.69"]', namespaces)
        if ndc_elem is not None:
            info['ndc'] = ndc_elem.get('code', '')
        
        # Extract generic name (first active ingredient)
        if ingredients:
            info['generic_name'] = ingredients[0]
        
        return info
        
    except Exception as e:
        return None

def process_nested_zip(main_zip_path, logger, max_files=100):
    """Process nested ZIP files"""
    logger.info(f"Processing nested ZIP file: {main_zip_path}")
    
    # Setup database
    conn, cursor = setup_database()
    
    try:
        with zipfile.ZipFile(main_zip_path, 'r') as main_zip:
            # Get list of nested ZIP files
            nested_zips = [f for f in main_zip.namelist() if f.endswith('.zip')]
            logger.info(f"Found {len(nested_zips)} nested ZIP files")
            
            processed_count = 0
            error_count = 0
            
            # Process nested ZIP files (limit for testing)
            for i, nested_zip_name in enumerate(nested_zips[:max_files]):
                try:
                    if i % 10 == 0:
                        logger.info(f"Processing nested ZIP {i+1}/{min(len(nested_zips), max_files)}: {nested_zip_name}")
                    
                    # Read nested ZIP content
                    with main_zip.open(nested_zip_name) as nested_zip_data:
                        # Create a BytesIO object to treat the data as a file
                        import io
                        nested_zip_bytes = io.BytesIO(nested_zip_data.read())
                        
                        # Open the nested ZIP
                        with zipfile.ZipFile(nested_zip_bytes, 'r') as nested_zip:
                            # Look for XML files in the nested ZIP
                            xml_files = [f for f in nested_zip.namelist() if f.endswith('.xml')]
                            
                            for xml_file_name in xml_files:
                                try:
                                    # Read XML content
                                    with nested_zip.open(xml_file_name) as xml_file:
                                        xml_content = xml_file.read()
                                    
                                    # Extract info
                                    info = extract_dailymed_info(xml_content)
                                    
                                    if info and info.get('trade_name'):
                                        # Save to database
                                        cursor.execute('''
                                            INSERT INTO medicine_dailymed 
                                            (set_id, trade_name, generic_name, active_ingredients, manufacturer, ndc, xml_source)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        ''', (
                                            info.get('set_id'),
                                            info.get('trade_name'),
                                            info.get('generic_name'),
                                            info.get('active_ingredients'),
                                            info.get('manufacturer'),
                                            info.get('ndc'),
                                            f"{nested_zip_name}/{xml_file_name}"
                                        ))
                                        processed_count += 1
                                        
                                        if processed_count % 10 == 0:
                                            logger.info(f"Saved {processed_count} medicines so far...")
                                    
                                except Exception as e:
                                    error_count += 1
                                    if error_count < 5:  # Log first few errors
                                        logger.error(f"Error processing XML {xml_file_name}: {e}")
                
                except Exception as e:
                    error_count += 1
                    if error_count < 5:  # Log first few errors
                        logger.error(f"Error processing nested ZIP {nested_zip_name}: {e}")
            
            conn.commit()
            logger.info(f"Processing complete! Processed: {processed_count}, Errors: {error_count}")
            
    except Exception as e:
        logger.error(f"Error processing main ZIP file: {e}")
    finally:
        conn.close()

def main():
    """Main function"""
    logger = setup_logging()
    
    print("🔬 Nested ZIP DailyMed Processor")
    print("=" * 50)
    
    # Find ZIP files
    data_path = Path("Data")
    zip_files = list(data_path.glob("*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found in Data directory")
        return
    
    print(f"📁 Found {len(zip_files)} main ZIP files:")
    for i, zip_file in enumerate(zip_files, 1):
        print(f"   {i}. {zip_file.name} ({zip_file.stat().st_size / (1024**3):.1f} GB)")
    
    # Process first ZIP file
    if zip_files:
        print(f"\n🚀 Processing first ZIP file: {zip_files[0].name}")
        print("📝 Processing first 100 nested ZIP files as a test...")
        process_nested_zip(zip_files[0], logger, max_files=100)

if __name__ == "__main__":
    main() 