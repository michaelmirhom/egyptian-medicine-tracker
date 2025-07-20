#!/usr/bin/env python3
"""
Process DailyMed XML files with proper XML structure handling
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
            logging.FileHandler('dailymed_xml_processing.log'),
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
        print(f"Error parsing XML: {e}")
        return None

def process_zip_file(zip_path, logger, max_files=50):
    """Process a single ZIP file"""
    logger.info(f"Processing ZIP file: {zip_path}")
    
    # Setup database
    conn, cursor = setup_database()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in ZIP")
            
            # Filter for XML files
            xml_files = [f for f in file_list if f.endswith('.xml')]
            logger.info(f"Found {len(xml_files)} XML files")
            
            processed_count = 0
            error_count = 0
            
            # Process XML files (limit to max_files for testing)
            for i, filename in enumerate(xml_files[:max_files]):
                try:
                    logger.info(f"Processing XML file {i+1}/{min(len(xml_files), max_files)}: {filename}")
                    
                    # Read XML content
                    with zip_ref.open(filename) as xml_file:
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
                            filename
                        ))
                        processed_count += 1
                        logger.info(f"Saved: {info.get('trade_name')} - {info.get('generic_name')}")
                    else:
                        error_count += 1
                        logger.warning(f"No valid data found in {filename}")
                        
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
                    error_count += 1
            
            conn.commit()
            logger.info(f"Processing complete! Processed: {processed_count}, Errors: {error_count}")
            
    except Exception as e:
        logger.error(f"Error processing ZIP file: {e}")
    finally:
        conn.close()

def main():
    """Main function"""
    logger = setup_logging()
    
    print("🔬 DailyMed XML Processor")
    print("=" * 50)
    
    # Find ZIP files
    data_path = Path("Data")
    zip_files = list(data_path.glob("*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found in Data directory")
        return
    
    print(f"📁 Found {len(zip_files)} ZIP files:")
    for i, zip_file in enumerate(zip_files, 1):
        print(f"   {i}. {zip_file.name} ({zip_file.stat().st_size / (1024**3):.1f} GB)")
    
    # Process first ZIP file
    if zip_files:
        print(f"\n🚀 Processing first ZIP file: {zip_files[0].name}")
        print("📝 Processing first 50 XML files as a test...")
        process_zip_file(zip_files[0], logger, max_files=50)

if __name__ == "__main__":
    main() 