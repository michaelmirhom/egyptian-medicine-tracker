#!/usr/bin/env python3
"""
Check ZIP file contents to see what types of files are inside
"""

import zipfile
from pathlib import Path
from collections import Counter

def check_zip_contents(zip_path):
    """Check what types of files are in a ZIP file"""
    print(f"🔍 Checking contents of: {zip_path}")
    print("=" * 60)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            print(f"📁 Total files: {len(file_list)}")
            
            # Get file extensions
            extensions = []
            for filename in file_list:
                if '.' in filename:
                    ext = filename.split('.')[-1].lower()
                    extensions.append(ext)
                else:
                    extensions.append('no_extension')
            
            # Count extensions
            ext_counts = Counter(extensions)
            
            print(f"\n📋 File types found:")
            for ext, count in ext_counts.most_common(10):
                print(f"   .{ext}: {count:,} files")
            
            # Show first few files
            print(f"\n📄 First 10 files:")
            for i, filename in enumerate(file_list[:10], 1):
                print(f"   {i}. {filename}")
            
            # Check for any files that might be XML-like
            xml_like = [f for f in file_list if any(xml_ext in f.lower() for xml_ext in ['.xml', '.spl', '.hl7'])]
            if xml_like:
                print(f"\n🔍 Found {len(xml_like)} XML-like files:")
                for filename in xml_like[:5]:
                    print(f"   - {filename}")
            
            # Check file sizes
            print(f"\n📊 File size analysis:")
            total_size = 0
            for info in zip_ref.infolist():
                total_size += info.file_size
            
            print(f"   Total uncompressed size: {total_size / (1024**3):.2f} GB")
            print(f"   Average file size: {total_size / len(file_list) / 1024:.1f} KB")
            
    except Exception as e:
        print(f"❌ Error reading ZIP file: {e}")

def main():
    """Main function"""
    print("🔍 ZIP Contents Checker")
    print("=" * 50)
    
    # Find ZIP files
    data_path = Path("Data")
    zip_files = list(data_path.glob("*.zip"))
    
    if not zip_files:
        print("❌ No ZIP files found in Data directory")
        return
    
    # Check first ZIP file
    if zip_files:
        check_zip_contents(zip_files[0])

if __name__ == "__main__":
    main() 