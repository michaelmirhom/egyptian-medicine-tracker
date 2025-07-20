#!/usr/bin/env python3
"""
DailyMed Data Processor - Extracts medicine information from DailyMed ZIP files
"""

import os
import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re

class DailyMedProcessor:
    """Processes DailyMed ZIP files to extract medicine information"""
    
    def __init__(self, db_path: str = "src/database/app.db"):
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
        
        # XML namespaces used in DailyMed files
        self.namespaces = {
            'spl': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('dailymed_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_database(self):
        """Setup database connection and create tables if needed"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create DailyMed medicine table
            self.cursor.execute('''
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
            
            self.conn.commit()
            self.logger.info("Database setup completed")
            
        except Exception as e:
            self.logger.error(f"Database setup failed: {e}")
            raise
    
    def extract_zip_files(self, data_dir: str = "Data"):
        """Extract all ZIP files in the data directory"""
        data_path = Path(data_dir)
        if not data_path.exists():
            self.logger.error(f"Data directory not found: {data_dir}")
            return []
        
        zip_files = list(data_path.glob("*.zip"))
        self.logger.info(f"Found {len(zip_files)} ZIP files")
        
        extracted_files = []
        
        for zip_file in zip_files:
            self.logger.info(f"Extracting: {zip_file.name}")
            
            try:
                # Create extraction directory
                extract_dir = data_path / f"extracted_{zip_file.stem}"
                extract_dir.mkdir(exist_ok=True)
                
                # Extract ZIP file
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find XML files
                xml_files = list(extract_dir.rglob("*.xml"))
                extracted_files.extend(xml_files)
                
                self.logger.info(f"Extracted {len(xml_files)} XML files from {zip_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error extracting {zip_file.name}: {e}")
        
        return extracted_files
    
    def parse_xml_file(self, xml_file: Path) -> Optional[Dict]:
        """Parse a single XML file and extract medicine information"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Extract basic information
            medicine_info = {
                'set_id': self.get_text(root, './/spl:setId'),
                'trade_name': self.get_text(root, './/spl:title'),
                'generic_name': self.get_text(root, './/spl:ingredient[@classCode="ACTIM"]/spl:ingredientSubstance/spl:name'),
                'active_ingredients': self.get_active_ingredients(root),
                'dosage_form': self.get_text(root, './/spl:formCode'),
                'strength': self.get_strength(root),
                'manufacturer': self.get_text(root, './/spl:assignedEntity/spl:assignedOrganization/spl:name'),
                'ndc': self.get_ndc(root),
                'rx_otc': self.get_rx_otc_status(root),
                'application_number': self.get_text(root, './/spl:code[@codeSystem="2.16.840.1.113883.3.3.2.3.2"]'),
                'labeler': self.get_text(root, './/spl:assignedEntity/spl:assignedOrganization/spl:name'),
                'package_description': self.get_package_description(root),
                'indications': self.get_section_text(root, 'INDICATIONS AND USAGE'),
                'contraindications': self.get_section_text(root, 'CONTRAINDICATIONS'),
                'warnings': self.get_section_text(root, 'WARNINGS'),
                'dosage_administration': self.get_section_text(root, 'DOSAGE AND ADMINISTRATION'),
                'side_effects': self.get_section_text(root, 'ADVERSE REACTIONS'),
                'drug_interactions': self.get_section_text(root, 'DRUG INTERACTIONS'),
                'pregnancy_category': self.get_section_text(root, 'PREGNANCY'),
                'storage_conditions': self.get_section_text(root, 'STORAGE AND HANDLING'),
                'xml_source': xml_file.name
            }
            
            # Clean up text fields
            for key, value in medicine_info.items():
                if isinstance(value, str):
                    medicine_info[key] = self.clean_text(value)
            
            return medicine_info
            
        except Exception as e:
            self.logger.error(f"Error parsing {xml_file}: {e}")
            return None
    
    def get_text(self, root, xpath: str) -> str:
        """Extract text from XML element using XPath"""
        try:
            elements = root.findall(xpath, self.namespaces)
            if elements:
                return ' '.join([elem.text.strip() for elem in elements if elem.text])
        except Exception:
            pass
        return ""
    
    def get_active_ingredients(self, root) -> str:
        """Extract active ingredients"""
        ingredients = []
        try:
            ingredient_elements = root.findall('.//spl:ingredient[@classCode="ACTIM"]', self.namespaces)
            for elem in ingredient_elements:
                name = elem.find('.//spl:ingredientSubstance/spl:name', self.namespaces)
                strength = elem.find('.//spl:quantity/spl:numerator', self.namespaces)
                if name is not None and name.text:
                    ingredient = name.text.strip()
                    if strength is not None and strength.text:
                        ingredient += f" {strength.text.strip()}"
                    ingredients.append(ingredient)
        except Exception:
            pass
        return '; '.join(ingredients)
    
    def get_strength(self, root) -> str:
        """Extract medicine strength"""
        try:
            strength_elem = root.find('.//spl:quantity/spl:numerator', self.namespaces)
            if strength_elem is not None and strength_elem.text:
                return strength_elem.text.strip()
        except Exception:
            pass
        return ""
    
    def get_ndc(self, root) -> str:
        """Extract NDC (National Drug Code)"""
        try:
            ndc_elements = root.findall('.//spl:code[@codeSystem="2.16.840.1.113883.6.69"]', self.namespaces)
            if ndc_elements:
                return ndc_elements[0].get('code', '')
        except Exception:
            pass
        return ""
    
    def get_rx_otc_status(self, root) -> str:
        """Extract prescription/OTC status"""
        try:
            rx_elements = root.findall('.//spl:code[@codeSystem="2.16.840.1.113883.3.3.2.3.1"]', self.namespaces)
            if rx_elements:
                return rx_elements[0].get('displayName', '')
        except Exception:
            pass
        return ""
    
    def get_package_description(self, root) -> str:
        """Extract package description"""
        try:
            package_elements = root.findall('.//spl:subject/spl:manufacturedProduct/spl:manufacturedProduct/spl:formCode', self.namespaces)
            if package_elements:
                return '; '.join([elem.get('displayName', '') for elem in package_elements])
        except Exception:
            pass
        return ""
    
    def get_section_text(self, root, section_title: str) -> str:
        """Extract text from a specific section"""
        try:
            # Find section by title
            sections = root.findall('.//spl:section', self.namespaces)
            for section in sections:
                title_elem = section.find('.//spl:title', self.namespaces)
                if title_elem is not None and title_elem.text:
                    if section_title.lower() in title_elem.text.lower():
                        # Extract all text from this section
                        text_elements = section.findall('.//spl:text', self.namespaces)
                        texts = []
                        for text_elem in text_elements:
                            if text_elem.text:
                                texts.append(text_elem.text.strip())
                        return ' '.join(texts)
        except Exception:
            pass
        return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}]', '', text)
        
        # Limit length to prevent database issues
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text
    
    def save_to_database(self, medicine_info: Dict):
        """Save extracted medicine information to database"""
        try:
            self.cursor.execute('''
                INSERT INTO medicine_dailymed 
                (set_id, trade_name, generic_name, active_ingredients, dosage_form, strength,
                 manufacturer, ndc, rx_otc, application_number, labeler, package_description,
                 indications, contraindications, warnings, dosage_administration, side_effects,
                 drug_interactions, pregnancy_category, storage_conditions, xml_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                medicine_info.get('set_id'),
                medicine_info.get('trade_name'),
                medicine_info.get('generic_name'),
                medicine_info.get('active_ingredients'),
                medicine_info.get('dosage_form'),
                medicine_info.get('strength'),
                medicine_info.get('manufacturer'),
                medicine_info.get('ndc'),
                medicine_info.get('rx_otc'),
                medicine_info.get('application_number'),
                medicine_info.get('labeler'),
                medicine_info.get('package_description'),
                medicine_info.get('indications'),
                medicine_info.get('contraindications'),
                medicine_info.get('warnings'),
                medicine_info.get('dosage_administration'),
                medicine_info.get('side_effects'),
                medicine_info.get('drug_interactions'),
                medicine_info.get('pregnancy_category'),
                medicine_info.get('storage_conditions'),
                medicine_info.get('xml_source')
            ))
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
    
    def process_dailymed_data(self, data_dir: str = "Data"):
        """Main processing function"""
        self.logger.info("Starting DailyMed data processing...")
        
        # Extract ZIP files
        xml_files = self.extract_zip_files(data_dir)
        
        if not xml_files:
            self.logger.error("No XML files found after extraction")
            return
        
        self.logger.info(f"Processing {len(xml_files)} XML files...")
        
        processed_count = 0
        error_count = 0
        
        for i, xml_file in enumerate(xml_files, 1):
            if i % 100 == 0:
                self.logger.info(f"Processed {i}/{len(xml_files)} files...")
            
            try:
                medicine_info = self.parse_xml_file(xml_file)
                if medicine_info and medicine_info.get('trade_name'):
                    self.save_to_database(medicine_info)
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing {xml_file}: {e}")
                error_count += 1
        
        self.conn.commit()
        
        self.logger.info(f"Processing complete!")
        self.logger.info(f"Successfully processed: {processed_count}")
        self.logger.info(f"Errors: {error_count}")
        
        # Get final statistics
        stats = self.get_database_stats()
        self.logger.info(f"Total records in database: {stats.get('total_records', 0)}")
    
    def get_database_stats(self):
        """Get statistics about the processed data"""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM medicine_dailymed")
            total_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT trade_name) FROM medicine_dailymed WHERE trade_name IS NOT NULL")
            unique_medicines = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(DISTINCT xml_source) FROM medicine_dailymed")
            xml_sources = self.cursor.fetchone()[0]
            
            return {
                'total_records': total_count,
                'unique_medicines': unique_medicines,
                'xml_sources': xml_sources
            }
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    """Main function to run DailyMed processing"""
    print("🔬 DailyMed Data Processor")
    print("=" * 50)
    
    try:
        processor = DailyMedProcessor()
        processor.process_dailymed_data()
        
        # Show results
        stats = processor.get_database_stats()
        print("\n📊 Processing Results:")
        print("=" * 30)
        print(f"Total records: {stats.get('total_records', 0):,}")
        print(f"Unique medicines: {stats.get('unique_medicines', 0):,}")
        print(f"XML sources: {stats.get('xml_sources', 0)}")
        
        processor.close()
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")

if __name__ == "__main__":
    main() 