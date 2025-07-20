#!/usr/bin/env python3
"""
Simple script to run PDF analysis
"""

import os
import sys
from pathlib import Path

def main():
    print("🔍 PDF Medicine Information Extractor")
    print("=" * 50)
    
    # Check if required libraries are installed
    try:
        import PyPDF2
        import pdfplumber
        print("✅ PDF libraries found")
    except ImportError:
        print("❌ Missing PDF libraries!")
        print("Install with: pip install -r pdf_requirements.txt")
        return
    
    # Import the analyzer
    try:
        from pdf_analyzer import PDFMedicineAnalyzer
    except ImportError as e:
        print(f"❌ Error importing analyzer: {e}")
        return
    
    # Get PDF directory
    pdf_dir = input("📁 Enter path to PDF directory (or press Enter for 'pdfs' folder): ").strip()
    if not pdf_dir:
        pdf_dir = "pdfs"
    
    # Create directory if it doesn't exist
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        print(f"📁 Creating directory: {pdf_dir}")
        pdf_path.mkdir(exist_ok=True)
        print(f"📋 Please add your PDF files to the '{pdf_dir}' folder and run this script again.")
        return
    
    # Check if directory has PDF files
    pdf_files = list(pdf_path.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in '{pdf_dir}'")
        print(f"📋 Please add PDF files to the '{pdf_dir}' folder and run this script again.")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        print(f"   - {pdf_file.name}")
    
    # Confirm analysis
    confirm = input(f"\n🚀 Start analyzing {len(pdf_files)} PDF files? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Analysis cancelled")
        return
    
    # Run analysis
    try:
        analyzer = PDFMedicineAnalyzer()
        analyzer.analyze_pdf_directory(pdf_dir)
        
        # Show results
        stats = analyzer.get_database_stats()
        print("\n📊 Analysis Results:")
        print("=" * 30)
        print(f"Total records: {stats.get('total_records', 0)}")
        print(f"Unique medicines: {stats.get('unique_medicines', 0)}")
        print(f"PDF sources: {stats.get('pdf_sources', 0)}")
        print(f"Average confidence: {stats.get('average_confidence', 0)}")
        
        analyzer.close()
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return
    
    print("\n✅ Analysis complete! Check the database for extracted medicine information.")

if __name__ == "__main__":
    main() 