#!/usr/bin/env python3
"""
Process all DailyMed ZIP files to extract comprehensive medicine data
"""

import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import logging
from pathlib import Path
import os
import re
from datetime import datetime

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('all_zips_processing.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def setup_database():
    """Setup database connection"""
    conn = sqlite3.connect("src/database/app.db")
    cursor = conn.cursor()
    
    # Create comprehensive DailyMed table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicine_dailymed_complete (
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
            zip_source TEXT,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn, cursor

def extract_comprehensive_info(xml_content):
    """Extract comprehensive information from DailyMed XML"""
    try:
        root = ET.fromstring(xml_content)
        
        # Define namespaces
        namespaces = {
            'spl': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        info = {
            'set_id': '',
            'trade_name': '',
            'generic_name': '',
            'active_ingredients': '',
            'dosage_form': '',
            'strength': '',
            'manufacturer': '',
            'ndc': '',
            'xml_source': 'unknown'
        }
        
        # Extract set ID
        set_id_elem = root.find('.//spl:setId', namespaces)
        if set_id_elem is not None and set_id_elem.text:
            info['set_id'] = set_id_elem.text.strip()
        
        # Extract title (trade name) - try multiple paths
        title_paths = [
            './/spl:title',
            './/spl:document/spl:title',
            './/spl:component/spl:structuredBody/spl:component/spl:section/spl:title'
        ]
        
        for path in title_paths:
            title_elem = root.find(path, namespaces)
            if title_elem is not None and title_elem.text:
                info['trade_name'] = title_elem.text.strip()
                break
        
        # Extract manufacturer - try multiple paths
        manufacturer_paths = [
            './/spl:assignedEntity/spl:assignedOrganization/spl:name',
            './/spl:author/spl:assignedEntity/spl:assignedOrganization/spl:name',
            './/spl:responsibleParty/spl:assignedEntity/spl:assignedOrganization/spl:name'
        ]
        
        for path in manufacturer_paths:
            org_elem = root.find(path, namespaces)
            if org_elem is not None and org_elem.text:
                info['manufacturer'] = org_elem.text.strip()
                break
        
        # Extract active ingredients - try multiple approaches
        ingredients = []
        
        # Method 1: Look for ingredient elements
        ingredient_elems = root.findall('.//spl:ingredient[@classCode="ACTIM"]', namespaces)
        for elem in ingredient_elems:
            name_elem = elem.find('.//spl:ingredientSubstance/spl:name', namespaces)
            if name_elem is not None and name_elem.text:
                ingredients.append(name_elem.text.strip())
        
        # Method 2: Look for active ingredients in text sections
        if not ingredients:
            text_elems = root.findall('.//spl:text', namespaces)
            for text_elem in text_elems:
                if text_elem.text:
                    text = text_elem.text.lower()
                    if 'active ingredient' in text or 'ingredients:' in text:
                        lines = text_elem.text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and len(line) > 3 and not line.startswith('*'):
                                ingredients.append(line)
        
        info['active_ingredients'] = '; '.join(ingredients)
        
        # Extract generic name (first active ingredient or from title)
        if ingredients:
            info['generic_name'] = ingredients[0]
        elif info['trade_name']:
            # Try to extract generic name from trade name
            trade_name = info['trade_name']
            if '(' in trade_name and ')' in trade_name:
                generic_part = trade_name.split('(')[1].split(')')[0]
                info['generic_name'] = generic_part
        
        # Extract NDC - try multiple paths
        ndc_paths = [
            './/spl:code[@codeSystem="2.16.840.1.113883.6.69"]',
            './/spl:code[@codeSystem="2.16.840.1.113883.6.69"]/@code',
            './/spl:product/spl:manufacturedProduct/spl:manufacturedProduct/spl:code'
        ]
        
        for path in ndc_paths:
            ndc_elem = root.find(path, namespaces)
            if ndc_elem is not None:
                if hasattr(ndc_elem, 'get') and ndc_elem.get('code'):
                    info['ndc'] = ndc_elem.get('code')
                elif ndc_elem.text:
                    info['ndc'] = ndc_elem.text.strip()
                break
        
        # Extract dosage form
        form_elem = root.find('.//spl:formCode', namespaces)
        if form_elem is not None and form_elem.get('displayName'):
            info['dosage_form'] = form_elem.get('displayName')
        
        # Extract strength
        strength_elem = root.find('.//spl:quantity/spl:numerator', namespaces)
        if strength_elem is not None and strength_elem.text:
            info['strength'] = strength_elem.text.strip()
        
        return info
        
    except Exception as e:
        return None

def process_single_zip_file(zip_path, logger, max_files_per_zip=500):
    """Process a single ZIP file and return count of processed medicines"""
    logger.info(f"Processing ZIP file: {zip_path}")
    
    # Setup database
    conn, cursor = setup_database()
    
    processed_count = 0
    error_count = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as main_zip:
            # Get list of nested ZIP files
            nested_zips = [f for f in main_zip.namelist() if f.endswith('.zip')]
            logger.info(f"Found {len(nested_zips)} nested ZIP files in {zip_path.name}")
            
            # Process nested ZIP files (limit for efficiency)
            for i, nested_zip_name in enumerate(nested_zips[:max_files_per_zip]):
                try:
                    if i % 50 == 0:
                        logger.info(f"Processing nested ZIP {i+1}/{min(len(nested_zips), max_files_per_zip)} from {zip_path.name}")
                    
                    # Read nested ZIP content
                    with main_zip.open(nested_zip_name) as nested_zip_data:
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
                                    info = extract_comprehensive_info(xml_content)
                                    
                                    if info and info.get('trade_name'):
                                        # Save to database
                                        cursor.execute('''
                                            INSERT INTO medicine_dailymed_complete 
                                            (set_id, trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc, xml_source, zip_source)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        ''', (
                                            info.get('set_id'),
                                            info.get('trade_name'),
                                            info.get('generic_name'),
                                            info.get('active_ingredients'),
                                            info.get('dosage_form'),
                                            info.get('strength'),
                                            info.get('manufacturer'),
                                            info.get('ndc'),
                                            f"{nested_zip_name}/{xml_file_name}",
                                            zip_path.name
                                        ))
                                        processed_count += 1
                                        
                                        if processed_count % 100 == 0:
                                            logger.info(f"Saved {processed_count} medicines from {zip_path.name}...")
                                    
                                except Exception as e:
                                    error_count += 1
                                    if error_count < 10:
                                        logger.error(f"Error processing XML {xml_file_name}: {e}")
                
                except Exception as e:
                    error_count += 1
                    if error_count < 10:
                        logger.error(f"Error processing nested ZIP {nested_zip_name}: {e}")
            
            conn.commit()
            logger.info(f"Completed {zip_path.name}: Processed {processed_count}, Errors {error_count}")
            
    except Exception as e:
        logger.error(f"Error processing main ZIP file {zip_path}: {e}")
    finally:
        conn.close()
    
    return processed_count, error_count

def process_all_zip_files():
    """Process all ZIP files in the Data directory"""
    logger = setup_logging()
    
    print("🔬 Processing All DailyMed ZIP Files")
    print("=" * 60)
    
    # Find all ZIP files
    data_path = Path("Data")
    zip_files = list(data_path.glob("*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found in Data directory")
        return
    
    print(f"📁 Found {len(zip_files)} ZIP files to process:")
    for i, zip_file in enumerate(zip_files, 1):
        size_gb = zip_file.stat().st_size / (1024**3)
        print(f"   {i}. {zip_file.name} ({size_gb:.1f} GB)")
    
    # Confirm processing
    confirm = input(f"\n🚀 Process all {len(zip_files)} ZIP files? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Processing cancelled")
        return
    
    total_processed = 0
    total_errors = 0
    
    # Process each ZIP file
    for i, zip_file in enumerate(zip_files, 1):
        print(f"\n📦 Processing ZIP {i}/{len(zip_files)}: {zip_file.name}")
        print("-" * 50)
        
        processed, errors = process_single_zip_file(zip_file, logger, max_files_per_zip=500)
        total_processed += processed
        total_errors += errors
        
        print(f"✅ Completed {zip_file.name}: {processed} medicines, {errors} errors")
    
    # Final summary
    print(f"\n🎯 Processing Complete!")
    print("=" * 60)
    print(f"📊 Total medicines extracted: {total_processed:,}")
    print(f"❌ Total errors: {total_errors}")
    print(f"📁 ZIP files processed: {len(zip_files)}")
    
    # Show database statistics
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM medicine_dailymed_complete")
        total_in_db = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_dailymed_complete WHERE trade_name IS NOT NULL")
        unique_medicines = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT zip_source) FROM medicine_dailymed_complete")
        zip_sources = cursor.fetchone()[0]
        
        print(f"\n📋 Database Statistics:")
        print(f"   Total records in database: {total_in_db:,}")
        print(f"   Unique medicines: {unique_medicines:,}")
        print(f"   ZIP sources: {zip_sources}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")

if __name__ == "__main__":
    process_all_zip_files() 