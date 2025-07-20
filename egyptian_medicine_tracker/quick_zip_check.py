#!/usr/bin/env python3
"""
Quick check to count all XML files in ZIP files
"""

import zipfile
import os
from pathlib import Path

def count_xml_files_in_zip(zip_path):
    """Count all XML files in a ZIP file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as main_zip:
            nested_zips = [f for f in main_zip.namelist() if f.endswith('.zip')]
            total_xml = 0
            
            print(f"📦 {os.path.basename(zip_path)}: {len(nested_zips)} nested ZIPs")
            
            for i, nested_zip_name in enumerate(nested_zips):
                try:
                    nested_zip_data = main_zip.read(nested_zip_name)
                    with zipfile.ZipFile(io.BytesIO(nested_zip_data)) as nested_zip:
                        xml_files = [f for f in nested_zip.namelist() if f.endswith('.xml')]
                        total_xml += len(xml_files)
                        
                        if i % 2000 == 0:
                            print(f"   Processed {i}/{len(nested_zips)} nested ZIPs...")
                
                except Exception as e:
                    continue
            
            print(f"   Total XML files: {total_xml:,}")
            return total_xml
            
    except Exception as e:
        print(f"Error processing {zip_path}: {e}")
        return 0

def main():
    print("🔍 QUICK ZIP FILE ANALYSIS")
    print("=" * 50)
    
    data_dir = Path("Data")
    zip_files = list(data_dir.glob("dm_spl_release_human_rx_part*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found")
        return
    
    total_xml_files = 0
    
    for zip_file in zip_files:
        size_mb = zip_file.stat().st_size / (1024 * 1024)
        print(f"\n📁 {zip_file.name} ({size_mb:.1f} MB)")
        
        xml_count = count_xml_files_in_zip(zip_file)
        total_xml_files += xml_count
    
    print(f"\n🎯 SUMMARY:")
    print("=" * 50)
    print(f"Total XML files in all ZIPs: {total_xml_files:,}")
    print(f"Medicines in database: 39,233")
    
    if total_xml_files > 39233:
        print(f"⚠️  POTENTIAL MISSING: {total_xml_files - 39233:,} XML files!")
        print(f"Extraction ratio: {39233/total_xml_files*100:.1f}%")
    elif total_xml_files == 39233:
        print(f"✅ PERFECT MATCH! All XML files extracted!")
    else:
        print(f"✅ All XML files processed (some may be duplicates)")

if __name__ == "__main__":
    import io
    main() 