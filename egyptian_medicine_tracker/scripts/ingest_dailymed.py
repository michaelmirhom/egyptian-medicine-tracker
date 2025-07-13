#!/usr/bin/env python3
"""
DailyMed Archive Ingestion Script
Processes ZIP archives and extracts label data into SQLite database
"""

import os
import zipfile
import glob
from lxml import etree
from tqdm import tqdm
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, db
from models.dailymed import DailyMedLabel

def extract_text(element, tag_name):
    """Extract text from XML element by tag name"""
    if element is None:
        return ""
    
    # Define namespaces used in DailyMed XML
    namespaces = {
        'hl7': 'urn:hl7-org:v3',
        'voc': 'http://www.hl7.org/v3/voc'
    }
    
    # Try different approaches to find the element
    search_paths = [
        f'.//{tag_name}',
        f'.//hl7:{tag_name}',
        f'.//*[local-name()="{tag_name}"]'
    ]
    
    for path in search_paths:
        try:
            elements = element.xpath(path, namespaces=namespaces)
            if elements and len(elements) > 0:
                element_text = elements[0].text
                if element_text:
                    return element_text.strip()
        except Exception:
            continue
    
    return ""

def extract_ingredients(element):
    """Extract all active ingredients from HL7 v3 format"""
    ingredients = []
    
    try:
        # Define namespaces
        namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'voc': 'http://www.hl7.org/v3/voc'
        }
        
        # Try different paths for active ingredients in HL7 v3 format
        ingredient_paths = [
            './/hl7:activeIngredient//hl7:name',
            './/activeIngredient//name',
            './/*[local-name()="activeIngredient"]//*[local-name()="name"]',
            './/hl7:activeIngredientSubstance//hl7:name',
            './/activeIngredientSubstance//name',
            './/*[local-name()="activeIngredientSubstance"]//*[local-name()="name"]'
        ]
        
        for path in ingredient_paths:
            try:
                elements = element.xpath(path, namespaces=namespaces)
                for elem in elements:
                    if elem.text and elem.text.strip():
                        ingredients.append(elem.text.strip())
                if ingredients:
                    break
            except Exception:
                continue
        
        return ', '.join(ingredients)
    except Exception:
        return ""

def process_xml_file(xml_content):
    """Process a single XML file and extract label data"""
    try:
        root = etree.fromstring(xml_content)
        
        # Extract setid from the setId element
        setid = ""
        try:
            setId_elements = root.xpath('.//*[local-name()="setId"]', namespaces={'hl7': 'urn:hl7-org:v3'})
            if setId_elements:
                setid = setId_elements[0].get('root', '')
        except Exception:
            pass
        
        # Extract brand name from title or manufacturedProduct
        brand = ""
        try:
            # Try title first
            title_elements = root.xpath('.//*[local-name()="title"]', namespaces={'hl7': 'urn:hl7-org:v3'})
            if title_elements and title_elements[0].text:
                brand = title_elements[0].text.strip()
                # Clean up brand name (remove superscript, etc.)
                brand = brand.split('<')[0].strip()
            
            # If no title, try manufacturedProduct name
            if not brand:
                name_elements = root.xpath('.//*[local-name()="manufacturedProduct"]//*[local-name()="name"]', namespaces={'hl7': 'urn:hl7-org:v3'})
                if name_elements and name_elements[0].text:
                    brand = name_elements[0].text.strip()
        except Exception:
            pass
        
        # Extract generic name from activeIngredientSubstance
        generic = ""
        try:
            generic_elements = root.xpath('.//*[local-name()="activeIngredientSubstance"]//*[local-name()="name"]', namespaces={'hl7': 'urn:hl7-org:v3'})
            if generic_elements and generic_elements[0].text:
                generic = generic_elements[0].text.strip()
        except Exception:
            pass
        
        # Extract indications and contraindications from sections
        indications = ""
        contraind = ""
        try:
            # Look for sections with specific codes or titles
            sections = root.xpath('.//*[local-name()="section"]', namespaces={'hl7': 'urn:hl7-org:v3'})
            for section in sections:
                # Try to find section title or code
                title_elem = section.xpath('.//*[local-name()="title"]', namespaces={'hl7': 'urn:hl7-org:v3'})
                if title_elem and title_elem[0].text:
                    title_text = title_elem[0].text.lower()
                    # Get section text
                    text_elem = section.xpath('.//*[local-name()="text"]', namespaces={'hl7': 'urn:hl7-org:v3'})
                    if text_elem and text_elem[0].text:
                        section_text = text_elem[0].text.strip()
                        if 'indication' in title_text or 'usage' in title_text:
                            indications = section_text
                        elif 'contraindication' in title_text:
                            contraind = section_text
        except Exception:
            pass
        
        # Extract ingredients
        ingredients = extract_ingredients(root)
        
        # Skip if no essential data
        if not (brand or generic):
            return None
        
        return {
            'setid': setid,
            'brand': brand,
            'generic': generic.lower() if generic else '',
            'indications': indications,
            'contraind': contraind,
            'ingredients': ingredients
        }
        
    except Exception:
        # Silently skip malformed XML files
        return None

def ingest_archives():
    """Main ingestion function"""
    # Find all DailyMed archives
    archive_pattern = os.path.join('data', 'dm_spl_release_human_rx_part*.zip')
    archives = glob.glob(archive_pattern)
    
    if not archives:
        print(f"No archives found matching pattern: {archive_pattern}")
        print("Please ensure DailyMed archives are in the data/ directory")
        return
    
    print(f"Found {len(archives)} archives to process")
    
    total_processed = 0
    total_inserted = 0
    
    with app.app_context():
        # Create table if it doesn't exist
        db.create_all()
        
        for archive_path in archives:
            print(f"\nProcessing: {archive_path}")
            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    inner_zips = [f for f in zip_file.namelist() if f.endswith('.zip')]
                    print(f"  Found {len(inner_zips)} inner ZIP files in this archive.")
                    if not inner_zips:
                        print(f"  WARNING: No inner ZIP files found in {archive_path}!")
                    for inner_zip_name in tqdm(inner_zips, desc="Processing inner ZIPs"):
                        try:
                            with zip_file.open(inner_zip_name) as inner_zip_file:
                                with zipfile.ZipFile(inner_zip_file) as inner_zip:
                                    xml_names = [n for n in inner_zip.namelist() if n.endswith('.xml')]
                                    if not xml_names:
                                        continue
                                    xml_name = xml_names[0]
                                    with inner_zip.open(xml_name) as f:
                                        xml_content = f.read()
                                    label_data = process_xml_file(xml_content)
                                    if label_data:
                                        existing = DailyMedLabel.query.filter_by(setid=label_data['setid']).first()
                                        if existing:
                                            for key, value in label_data.items():
                                                setattr(existing, key, value)
                                        else:
                                            new_label = DailyMedLabel(**label_data)
                                            db.session.add(new_label)
                                            total_inserted += 1
                                        total_processed += 1
                                        if total_processed % 1000 == 0:
                                            db.session.commit()
                                            print(f"  Committed {total_processed} records...")
                        except Exception:
                            # Silently skip problematic inner ZIPs
                            continue
                    db.session.commit()
            except Exception as e:
                print(f"Error processing archive {archive_path}: {e}")
                continue

        # Print final count inside app context
        final_count = DailyMedLabel.query.count()
        print(f"\nIngestion complete!")
        print(f"Total records processed: {total_processed}")
        print(f"Total new records inserted: {total_inserted}")
        print(f"Total records in database: {final_count}")

if __name__ == '__main__':
    ingest_archives() 