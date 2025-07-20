#!/usr/bin/env python3
"""
Resume extraction from where it left off
"""

import sqlite3
import zipfile
import xml.etree.ElementTree as ET
import logging
import os
from pathlib import Path

def setup_logging():
    """Setup logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('resume_extraction.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def extract_medicine_info(xml_content):
    """Extract medicine information from XML content"""
    try:
        root = ET.fromstring(xml_content)
        
        # Extract trade name
        trade_name = None
        for elem in root.iter():
            if elem.tag.endswith('title') and elem.text:
                trade_name = elem.text.strip()
                break
        
        # Extract generic name
        generic_name = None
        for elem in root.iter():
            if elem.tag.endswith('openFda') and elem.find('.//genericName') is not None:
                generic_name = elem.find('.//genericName').text
                break
        
        # Extract active ingredients
        active_ingredients = []
        for elem in root.iter():
            if elem.tag.endswith('activeIngredient'):
                for ingredient in elem.iter():
                    if ingredient.tag.endswith('ingredientName') and ingredient.text:
                        active_ingredients.append(ingredient.text.strip())
        
        # Extract dosage form
        dosage_form = None
        for elem in root.iter():
            if elem.tag.endswith('openFda') and elem.find('.//dosageForm') is not None:
                dosage_form = elem.find('.//dosageForm').text
                break
        
        # Extract strength
        strength = None
        for elem in root.iter():
            if elem.tag.endswith('openFda') and elem.find('.//activeIngredientUnit') is not None:
                strength = elem.find('.//activeIngredientUnit').text
                break
        
        # Extract manufacturer
        manufacturer = None
        for elem in root.iter():
            if elem.tag.endswith('openFda') and elem.find('.//manufacturerName') is not None:
                manufacturer = elem.find('.//manufacturerName').text
                break
        
        # Extract NDC
        ndc = None
        for elem in root.iter():
            if elem.tag.endswith('openFda') and elem.find('.//productNdc') is not None:
                ndc = elem.find('.//productNdc').text
                break
        
        if trade_name:
            return {
                'trade_name': trade_name,
                'generic_name': generic_name,
                'active_ingredients': ', '.join(active_ingredients) if active_ingredients else None,
                'dosage_form': dosage_form,
                'strength': strength,
                'manufacturer': manufacturer,
                'ndc': ndc
            }
        
        return None
        
    except Exception as e:
        return None

def process_remaining_zips(logger):
    """Process the remaining ZIP files (4 and 5)"""
    
    print("🔄 RESUMING EXTRACTION - REMAINING ZIP FILES")
    print("=" * 60)
    
    # Find remaining ZIP files
    data_dir = Path("Data")
    zip_files = list(data_dir.glob("dm_spl_release_human_rx_part*.zip"))
    
    # Process only ZIP 4 and 5 (remaining files)
    remaining_zips = [z for z in zip_files if 'part4' in z.name or 'part5' in z.name]
    
    if not remaining_zips:
        print("❌ No remaining ZIP files found")
        return
    
    print(f"📁 Found {len(remaining_zips)} remaining ZIP files:")
    for zip_file in remaining_zips:
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"   • {zip_file.name} ({size_mb:.1f} MB)")
    
    all_medicines = []
    total_processed = 0
    total_errors = 0
    total_xml_files = 0
    
    for i, zip_file in enumerate(remaining_zips, 1):
        print(f"\n📦 Processing remaining ZIP {i}/{len(remaining_zips)}: {zip_file.name}")
        print("-" * 60)
        
        medicines, processed, errors, xml_count = process_single_zip_complete(zip_file, logger)
        all_medicines.extend(medicines)
        total_processed += processed
        total_errors += errors
        total_xml_files += xml_count
        
        print(f"✅ Completed {zip_file.name}: {processed} medicines, {errors} errors, {xml_count} XML files")
    
    # Save medicines to database
    print(f"\n💾 Saving remaining medicines to database...")
    save_medicines_to_db(all_medicines, "medicine_dailymed_resume", logger)
    
    # Final summary
    print(f"\n🎯 RESUME EXTRACTION FINISHED!")
    print("=" * 60)
    print(f"📊 Additional medicines extracted: {len(all_medicines):,}")
    print(f"❌ Total errors: {total_errors}")
    print(f"📁 ZIP files processed: {len(remaining_zips)}")
    print(f"📄 Total XML files processed: {total_xml_files:,}")

def process_single_zip_complete(zip_path, logger):
    """Process ALL XML files from ALL nested ZIPs in a single main ZIP"""
    try:
        logger.info(f"Processing ZIP file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as main_zip:
            nested_zips = [f for f in main_zip.namelist() if f.endswith('.zip')]
            logger.info(f"Found {len(nested_zips)} nested ZIP files in {os.path.basename(zip_path)}")
            
            medicines = []
            processed_count = 0
            error_count = 0
            total_xml_files = 0
            
            for i, nested_zip_name in enumerate(nested_zips):
                try:
                    # Extract nested ZIP to memory
                    nested_zip_data = main_zip.read(nested_zip_name)
                    
                    with zipfile.ZipFile(io.BytesIO(nested_zip_data)) as nested_zip:
                        xml_files = [f for f in nested_zip.namelist() if f.endswith('.xml')]
                        total_xml_files += len(xml_files)
                        
                        # Process ALL XML files in this nested ZIP
                        for xml_file in xml_files:
                            try:
                                xml_content = nested_zip.read(xml_file).decode('utf-8', errors='ignore')
                                medicine_info = extract_medicine_info(xml_content)
                                
                                if medicine_info:
                                    medicines.append(medicine_info)
                                    processed_count += 1
                                    
                                    if processed_count % 1000 == 0:
                                        logger.info(f"Processed {processed_count} medicines from {os.path.basename(zip_path)}...")
                                
                            except Exception as e:
                                error_count += 1
                                continue
                
                except Exception as e:
                    error_count += 1
                    continue
                
                # Progress update
                if i % 1000 == 0:
                    logger.info(f"Processed {i}/{len(nested_zips)} nested ZIPs from {os.path.basename(zip_path)}...")
            
            logger.info(f"Completed {os.path.basename(zip_path)}: Processed {processed_count}, Errors {error_count}, XML files {total_xml_files}")
            return medicines, processed_count, error_count, total_xml_files
            
    except Exception as e:
        logger.error(f"Error processing {zip_path}: {e}")
        return [], 0, 1, 0

def save_medicines_to_db(medicines, table_name, logger):
    """Save medicines to database"""
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_name TEXT,
                generic_name TEXT,
                active_ingredients TEXT,
                dosage_form TEXT,
                strength TEXT,
                manufacturer TEXT,
                ndc TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert medicines
        for medicine in medicines:
            cursor.execute(f'''
                INSERT INTO {table_name} 
                (trade_name, generic_name, active_ingredients, dosage_form, strength, manufacturer, ndc)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                medicine.get('trade_name'),
                medicine.get('generic_name'),
                medicine.get('active_ingredients'),
                medicine.get('dosage_form'),
                medicine.get('strength'),
                medicine.get('manufacturer'),
                medicine.get('ndc')
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Saved {len(medicines)} medicines to {table_name}")
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")

def main():
    """Main function to resume extraction"""
    logger = setup_logging()
    
    print("🚀 RESUMING DAILYMED EXTRACTION")
    print("=" * 60)
    
    # Process remaining ZIP files
    process_remaining_zips(logger)
    
    # Get final statistics
    try:
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Check all medicine tables
        tables = ['medicine_dailymed_complete_all', 'medicine_dailymed_resume']
        total_medicines = 0
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_medicines += count
                print(f"   {table}: {count:,} medicines")
            except:
                print(f"   {table}: Does not exist")
        
        print(f"\n📊 TOTAL MEDICINES: {total_medicines:,}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting final stats: {e}")

if __name__ == "__main__":
    import io
    main() 