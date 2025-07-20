#!/usr/bin/env python3
"""
PDF Medicine Information Extractor and Database Populator
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# PDF processing libraries
try:
    import PyPDF2
    import pdfplumber
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
except ImportError as e:
    print(f"Missing required libraries: {e}")
    print("Install with: pip install PyPDF2 pdfplumber pdf2image pytesseract opencv-python pillow")

class PDFMedicineAnalyzer:
    """Analyzes PDF files to extract medicine information and populate database"""
    
    def __init__(self, db_path: str = "src/database/app.db"):
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
        
        # Medicine patterns for extraction
        self.medicine_patterns = {
            'trade_name': r'(?i)(?:trade\s*name|brand\s*name|product\s*name)[:\s]*([A-Za-z0-9\s\-]+)',
            'generic_name': r'(?i)(?:generic\s*name|active\s*ingredient|ingredient)[:\s]*([A-Za-z0-9\s\-/]+)',
            'price': r'(?i)(?:price|cost)[:\s]*([0-9,\.]+)\s*(EGP|USD|EUR|GBP)?',
            'dosage': r'(?i)(?:dosage|strength)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ml|mcg)',
            'manufacturer': r'(?i)(?:manufacturer|company|producer)[:\s]*([A-Za-z\s&]+)',
            'registration': r'(?i)(?:registration|reg\s*no|license)[:\s]*([A-Za-z0-9\-]+)',
            'arabic_name': r'[\u0600-\u06FF\s]+',  # Arabic text
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pdf_analysis.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup database connection and create tables if needed"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create enhanced medicine table if it doesn't exist
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS medicine_pdf (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_name TEXT,
                    generic_name TEXT,
                    arabic_name TEXT,
                    dosage TEXT,
                    price REAL,
                    currency TEXT DEFAULT 'EGP',
                    manufacturer TEXT,
                    registration_no TEXT,
                    pdf_source TEXT,
                    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL,
                    raw_text TEXT
                )
            ''')
            
            self.conn.commit()
            self.logger.info("Database setup completed")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        try:
            # Method 1: PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # Method 2: pdfplumber (better for complex layouts)
            if not text.strip():
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            
            # Method 3: OCR for image-based PDFs
            if not text.strip():
                self.logger.info("Attempting OCR extraction...")
                text = self.extract_text_with_ocr(pdf_path)
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR for image-based PDFs"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            text = ""
            
            for i, image in enumerate(images):
                # Convert PIL image to OpenCV format
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Preprocess image for better OCR
                gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
                # OCR
                ocr_text = pytesseract.image_to_string(thresh, lang='eng+ara')
                text += ocr_text + "\n"
                
                self.logger.info(f"OCR completed for page {i+1}")
            
            return text
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_medicine_info(self, text: str) -> List[Dict]:
        """Extract medicine information from text"""
        medicines = []
        
        # Split text into potential medicine sections
        sections = self.split_into_sections(text)
        
        for section in sections:
            medicine_info = self.parse_medicine_section(section)
            if medicine_info:
                medicines.append(medicine_info)
        
        return medicines
    
    def split_into_sections(self, text: str) -> List[str]:
        """Split text into potential medicine sections"""
        # Split by common medicine document patterns
        patterns = [
            r'(?i)(?:medicine|drug|product|medication)[:\s]*',
            r'(?i)(?:trade\s*name|brand\s*name)',
            r'(?i)(?:generic\s*name|active\s*ingredient)',
            r'[A-Z][A-Z\s]{2,}',  # All caps words (likely medicine names)
        ]
        
        sections = [text]  # Start with full text
        
        for pattern in patterns:
            new_sections = []
            for section in sections:
                splits = re.split(pattern, section)
                new_sections.extend([s.strip() for s in splits if s.strip()])
            sections = new_sections
        
        return sections
    
    def parse_medicine_section(self, section: str) -> Optional[Dict]:
        """Parse a text section for medicine information"""
        if len(section.strip()) < 10:  # Too short to be meaningful
            return None
        
        medicine_info = {
            'trade_name': None,
            'generic_name': None,
            'arabic_name': None,
            'dosage': None,
            'price': None,
            'currency': 'EGP',
            'manufacturer': None,
            'registration_no': None,
            'confidence_score': 0.0,
            'raw_text': section
        }
        
        # Extract information using patterns
        for field, pattern in self.medicine_patterns.items():
            matches = re.findall(pattern, section, re.IGNORECASE | re.MULTILINE)
            if matches:
                if field == 'price':
                    # Handle price extraction
                    for match in matches:
                        if isinstance(match, tuple):
                            price_str = match[0].replace(',', '')
                            currency = match[1] if len(match) > 1 else 'EGP'
                            try:
                                medicine_info['price'] = float(price_str)
                                medicine_info['currency'] = currency
                                break
                            except ValueError:
                                continue
                else:
                    # Handle other fields
                    value = matches[0] if isinstance(matches[0], str) else matches[0][0]
                    medicine_info[field] = value.strip()
        
        # Calculate confidence score
        confidence = 0.0
        if medicine_info['trade_name']:
            confidence += 0.3
        if medicine_info['generic_name']:
            confidence += 0.3
        if medicine_info['price']:
            confidence += 0.2
        if medicine_info['dosage']:
            confidence += 0.1
        if medicine_info['manufacturer']:
            confidence += 0.1
        
        medicine_info['confidence_score'] = confidence
        
        # Only return if we have at least some basic info
        return medicine_info if confidence > 0.2 else None
    
    def save_to_database(self, medicines: List[Dict], pdf_source: str):
        """Save extracted medicine information to database"""
        try:
            for medicine in medicines:
                self.cursor.execute('''
                    INSERT INTO medicine_pdf 
                    (trade_name, generic_name, arabic_name, dosage, price, currency, 
                     manufacturer, registration_no, pdf_source, confidence_score, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    medicine.get('trade_name'),
                    medicine.get('generic_name'),
                    medicine.get('arabic_name'),
                    medicine.get('dosage'),
                    medicine.get('price'),
                    medicine.get('currency'),
                    medicine.get('manufacturer'),
                    medicine.get('registration_no'),
                    pdf_source,
                    medicine.get('confidence_score'),
                    medicine.get('raw_text')
                ))
            
            self.conn.commit()
            self.logger.info(f"Saved {len(medicines)} medicine records from {pdf_source}")
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            self.conn.rollback()
    
    def analyze_pdf_directory(self, directory_path: str):
        """Analyze all PDF files in a directory"""
        pdf_dir = Path(directory_path)
        if not pdf_dir.exists():
            self.logger.error(f"Directory not found: {directory_path}")
            return
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        self.logger.info(f"Found {len(pdf_files)} PDF files to analyze")
        
        total_medicines = 0
        
        for pdf_file in pdf_files:
            self.logger.info(f"Analyzing: {pdf_file.name}")
            
            try:
                # Extract text
                text = self.extract_text_from_pdf(str(pdf_file))
                if not text:
                    self.logger.warning(f"No text extracted from {pdf_file.name}")
                    continue
                
                # Extract medicine information
                medicines = self.extract_medicine_info(text)
                
                if medicines:
                    # Save to database
                    self.save_to_database(medicines, pdf_file.name)
                    total_medicines += len(medicines)
                    self.logger.info(f"Extracted {len(medicines)} medicines from {pdf_file.name}")
                else:
                    self.logger.warning(f"No medicine information found in {pdf_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {pdf_file.name}: {e}")
        
        self.logger.info(f"Analysis complete! Total medicines extracted: {total_medicines}")
    
    def get_database_stats(self):
        """Get statistics about the extracted data"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM medicine_pdf")
            total_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_pdf WHERE trade_name IS NOT NULL")
            unique_medicines = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT pdf_source) FROM medicine_pdf")
            pdf_sources = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT AVG(confidence_score) FROM medicine_pdf")
            avg_confidence = self.cursor.fetchone()[0] or 0
            
            return {
                'total_records': total_count,
                'unique_medicines': unique_medicines,
                'pdf_sources': pdf_sources,
                'average_confidence': round(avg_confidence, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function to run PDF analysis"""
    analyzer = PDFMedicineAnalyzer()
    
    # Example usage
    print("🔍 PDF Medicine Information Extractor")
    print("=" * 50)
    
    # Ask user for PDF directory
    pdf_dir = input("Enter path to PDF directory (or press Enter for 'pdfs' folder): ").strip()
    if not pdf_dir:
        pdf_dir = "pdfs"
    
    # Create directory if it doesn't exist
    os.makedirs(pdf_dir, exist_ok=True)
    
    print(f"\n📁 Analyzing PDFs in: {pdf_dir}")
    print("⏳ This may take a while depending on the number and size of PDFs...")
    
    try:
        # Analyze PDFs
        analyzer.analyze_pdf_directory(pdf_dir)
        
        # Show results
        stats = analyzer.get_database_stats()
        print("\n📊 Analysis Results:")
        print("=" * 30)
        print(f"Total records: {stats.get('total_records', 0)}")
        print(f"Unique medicines: {stats.get('unique_medicines', 0)}")
        print(f"PDF sources: {stats.get('pdf_sources', 0)}")
        print(f"Average confidence: {stats.get('average_confidence', 0)}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main() 