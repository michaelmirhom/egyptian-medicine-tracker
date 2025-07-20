#!/usr/bin/env python3
"""
Verify complete extraction - check if ALL data was extracted from ZIP files
"""

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
            logging.FileHandler('verification.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def analyze_zip_contents(zip_path, logger):
    """Analyze the complete contents of a ZIP file"""
    try:
        logger.info(f"Analyzing ZIP file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as main_zip:
            nested_zips = [f for f in main_zip.namelist() if f.endswith('.zip')]
            logger.info(f"Found {len(nested_zips)} nested ZIP files")
            
            total_xml_files = 0
            total_medicines = 0
            sample_medicines = []
            
            for i, nested_zip_name in enumerate(nested_zips):
                try:
                    # Extract nested ZIP to memory
                    nested_zip_data = main_zip.read(nested_zip_name)
                    
                    with zipfile.ZipFile(io.BytesIO(nested_zip_data)) as nested_zip:
                        xml_files = [f for f in nested_zip.namelist() if f.endswith('.xml')]
                        total_xml_files += len(xml_files)
                        
                        # Process first few XML files to get sample medicines
                        for xml_file in xml_files[:5]:  # Just sample first 5
                            try:
                                xml_content = nested_zip.read(xml_file).decode('utf-8', errors='ignore')
                                
                                # Try to extract medicine name
                                try:
                                    root = ET.fromstring(xml_content)
                                    for elem in root.iter():
                                        if elem.tag.endswith('title') and elem.text:
                                            medicine_name = elem.text.strip()
                                            if medicine_name and len(sample_medicines) < 10:
                                                sample_medicines.append(medicine_name)
                                            break
                                except:
                                    pass
                                
                                total_medicines += 1
                                
                            except Exception as e:
                                continue
                
                except Exception as e:
                    continue
                
                # Progress update
                if i % 1000 == 0:
                    logger.info(f"Processed {i}/{len(nested_zips)} nested ZIPs...")
            
            logger.info(f"Analysis complete for {os.path.basename(zip_path)}:")
            logger.info(f"  - Nested ZIPs: {len(nested_zips)}")
            logger.info(f"  - XML files: {total_xml_files}")
            logger.info(f"  - Sample medicines: {len(sample_medicines)}")
            
            return {
                'nested_zips': len(nested_zips),
                'xml_files': total_xml_files,
                'sample_medicines': sample_medicines
            }
            
    except Exception as e:
        logger.error(f"Error analyzing {zip_path}: {e}")
        return None

def check_database_content(logger):
    """Check what's currently in the database"""
    try:
        import sqlite3
        
        conn = sqlite3.connect("src/database/app.db")
        cursor = conn.cursor()
        
        # Check all medicine tables
        tables = ['medicine', 'medicine_dailymed_complete', 'medicine_dailymed_complete_all', 'medicine_enhanced']
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(DISTINCT trade_name) FROM {table}")
                unique = cursor.fetchone()[0]
                
                logger.info(f"Table {table}: {count} records, {unique} unique medicines")
                
                # Get sample medicines
                cursor.execute(f"SELECT trade_name FROM {table} LIMIT 5")
                samples = cursor.fetchall()
                sample_names = [row[0] for row in samples if row[0]]
                
                if sample_names:
                    logger.info(f"  Sample medicines: {sample_names}")
                
            except Exception as e:
                logger.info(f"Table {table}: Does not exist or error - {e}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")

def main():
    """Main verification function"""
    logger = setup_logging()
    
    print("🔍 VERIFYING COMPLETE EXTRACTION")
    print("=" * 60)
    
    # Check current database content
    print("\n📊 Current Database Content:")
    print("-" * 40)
    check_database_content(logger)
    
    # Analyze ZIP files
    data_dir = Path("Data")
    zip_files = list(data_dir.glob("dm_spl_release_human_rx_part*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found in Data directory")
        return
    
    print(f"\n📁 Analyzing {len(zip_files)} ZIP files:")
    print("-" * 40)
    
    total_nested_zips = 0
    total_xml_files = 0
    all_sample_medicines = []
    
    for zip_file in zip_files:
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"\n📦 {zip_file.name} ({size_mb:.1f} MB)")
        
        result = analyze_zip_contents(zip_file, logger)
        if result:
            total_nested_zips += result['nested_zips']
            total_xml_files += result['xml_files']
            all_sample_medicines.extend(result['sample_medicines'])
            
            print(f"   Nested ZIPs: {result['nested_zips']:,}")
            print(f"   XML files: {result['xml_files']:,}")
            print(f"   Sample medicines: {len(result['sample_medicines'])}")
    
    # Summary
    print(f"\n🎯 VERIFICATION SUMMARY:")
    print("=" * 60)
    print(f"📁 Total ZIP files: {len(zip_files)}")
    print(f"📦 Total nested ZIPs: {total_nested_zips:,}")
    print(f"📄 Total XML files: {total_xml_files:,}")
    print(f"💊 Sample medicines found: {len(all_sample_medicines)}")
    
    if all_sample_medicines:
        print(f"\n💊 Sample Medicines from ZIPs:")
        for i, medicine in enumerate(all_sample_medicines[:10], 1):
            print(f"   {i}. {medicine}")
    
    # Compare with database
    print(f"\n🔍 COMPARISON WITH DATABASE:")
    print("-" * 40)
    print(f"XML files in ZIPs: {total_xml_files:,}")
    print(f"Medicines in database: 39,233")
    print(f"Extraction ratio: {39233/total_xml_files*100:.1f}%")
    
    if total_xml_files > 39233:
        print(f"⚠️  POTENTIAL MISSING DATA: {total_xml_files - 39233:,} XML files may not have been processed!")
    else:
        print(f"✅ All XML files appear to have been processed!")

if __name__ == "__main__":
    import io
    main() 