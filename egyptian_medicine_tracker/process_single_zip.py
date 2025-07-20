#!/usr/bin/env python3
"""
Process a single DailyMed ZIP file
"""

import zipfile
import xml.etree.ElementTree as ET
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
            logging.FileHandler('single_zip_processing.log'),
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

def extract_simple_info(xml_content):
    """Extract basic information from XML content"""
    try:
        root = ET.fromstring(xml_content)
        
        # Extract basic info
        info = {
            'set_id': '',
            'trade_name': '',
            'generic_name': '',
            'manufacturer': '',
            'xml_source': 'unknown'
        }
        
        # Try to find title (trade name)
        title_elem = root.find('.//title')
        if title_elem is not None and title_elem.text:
            info['trade_name'] = title_elem.text.strip()
        
        # Try to find manufacturer
        org_elem = root.find('.//assignedOrganization/name')
        if org_elem is not None and org_elem.text:
            info['manufacturer'] = org_elem.text.strip()
        
        # Try to find generic name
        ingredient_elem = root.find('.//ingredientSubstance/name')
        if ingredient_elem is not None and ingredient_elem.text:
            info['generic_name'] = ingredient_elem.text.strip()
        
        return info
        
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

def process_zip_file(zip_path, logger):
    """Process a single ZIP file"""
    logger.info(f"Processing ZIP file: {zip_path}")
    
    # Setup database
    conn, cursor = setup_database()
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get list of files in ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Found {len(file_list)} files in ZIP")
            
            processed_count = 0
            error_count = 0
            
            # Process first 10 files as a test
            for i, filename in enumerate(file_list[:10]):
                if filename.endswith('.xml'):
                    try:
                        logger.info(f"Processing file {i+1}/10: {filename}")
                        
                        # Read XML content
                        with zip_ref.open(filename) as xml_file:
                            xml_content = xml_file.read()
                        
                        # Extract info
                        info = extract_simple_info(xml_content)
                        
                        if info and info.get('trade_name'):
                            # Save to database
                            cursor.execute('''
                                INSERT INTO medicine_dailymed 
                                (set_id, trade_name, generic_name, manufacturer, xml_source)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                info.get('set_id'),
                                info.get('trade_name'),
                                info.get('generic_name'),
                                info.get('manufacturer'),
                                filename
                            ))
                            processed_count += 1
                            logger.info(f"Saved: {info.get('trade_name')}")
                        else:
                            error_count += 1
                            
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
    
    print("🔬 Single ZIP DailyMed Processor")
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
        process_zip_file(zip_files[0], logger)

if __name__ == "__main__":
    main() 