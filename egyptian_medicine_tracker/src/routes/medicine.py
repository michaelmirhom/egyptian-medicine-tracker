#!/usr/bin/env python3
"""
Medicine routes for the Egyptian Medicine Tracker API
Enhanced with comprehensive medical information from multiple APIs
"""

import json
import time
import re
import requests
from flask import Blueprint, request, jsonify
from fuzzywuzzy import fuzz
from src.models.medicine import Medicine, db
from src.services.medicine_api import medicine_api
from src.services.rxnav_api import rxnav_api
from src.services.usage_fallback import get_usage_generic, get_local_usage
from src.services.name_resolver import arabic_to_english, is_arabic_text

medicine_bp = Blueprint('medicine', __name__)

def extract_base_medicine_name(full_name: str) -> str:
    """
    Extract the base medicine name from a full product name.
    This removes dosage, form, and other modifiers.
    
    Args:
        full_name (str): Full product name (e.g., "Lipitor 20mg tablet")
        
    Returns:
        str: Base medicine name (e.g., "Lipitor")
    """
    if not full_name:
        return ""
    
    # Remove common dosage patterns
    dosage_patterns = [
        r'\d+\s*mg',  # 20mg, 50 mg
        r'\d+\s*mcg',  # 10mcg
        r'\d+\s*g',    # 1g
        r'\d+\s*ml',   # 5ml
        r'\d+\s*IU',   # 100IU
        r'\d+\s*units', #10 units
        r'\d+\s*%',    #5%
    ]
    
    base_name = full_name
    for pattern in dosage_patterns:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    
    # Remove common form patterns
    form_patterns = [
        r'\s+tablets?',
        r'\s+capsules?',
        r'\s+injection',
        r'\s+cream',
        r'\s+gel',
        r'\s+ointment',
        r'\s+suspension',
        r'\s+syrup',
        r'\s+drops',
        r'\s+spray',
        r'\s+inhaler',
        r'\s+patch',
        r'\s+suppository',
        r'\s+powder',
        r'\s+solution',
    ]
    
    for pattern in form_patterns:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    
    # Remove common quantity patterns
    quantity_patterns = [
        r'\s+\d+\s*tabs?',
        r'\s+\d+\s*caps?',
        r'\s+\d+\s*amps?',
        r'\s+\d+\s*vials?',
        r'\s+\d+\s*tubes?',
        r'\s+\d+\s*bottle[s]?',
    ]
    
    for pattern in quantity_patterns:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    
    # Clean up extra spaces and punctuation
    base_name = re.sub(r'\s+', ' ', base_name).strip()
    base_name = re.sub(r'[^\w\s-]', '', base_name).strip()
    
    return base_name

def clean_medicine_name(medicine_name: str) -> str:
    """
    Clean and normalize medicine name for better matching.
    
    Args:
        medicine_name (str): Raw medicine name
        
    Returns:
        str: Cleaned medicine name
    """
    if not medicine_name:
        return ""
    
    # Convert to lowercase
    cleaned = medicine_name.lower()
    
    # Remove common prefixes and suffixes
    prefixes_to_remove = ['dr.', 'doctor', 'prof.', 'professor']
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove extra spaces and normalize
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned

@medicine_bp.route('/medicines', methods=['GET'])
def get_medicines():
    """Get all medicines from database"""
    medicines = Medicine.query.all()
    return jsonify([medicine.to_dict() for medicine in medicines])

@medicine_bp.route('/medicines/search', methods=['GET'])
def search_medicines():
    """Search medicines by name in local database"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    medicines = Medicine.query.filter(
        Medicine.trade_name.contains(query) | 
        Medicine.generic_name.contains(query)
    ).all()
    
    return jsonify([medicine.to_dict() for medicine in medicines])

@medicine_bp.route('/medicines/api-search', methods=['GET'])
def api_search_medicines():
    """Search medicines using external API for real-time data, with comprehensive medical information for every product."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    cleaned_query = clean_medicine_name(query)
    cleaned_query = re.sub(r'\b\d+\b', '', cleaned_query).strip()
    
    # Get real-time data from external API
    success, products, error = medicine_api.search_and_get_details(query)
    if not success:
        return jsonify({'error': error}), 500
    
    # Filter products for relevance
    filtered_products = []
    for product in products:
        trade_name = (product.get('trade_name') or product.get('name') or '').lower()
        generic_name = (product.get('generic_name') or '').lower()
        # Substring match or fuzzy match >80
        if cleaned_query in trade_name or cleaned_query in generic_name or \
           fuzz.partial_ratio(cleaned_query, trade_name) > 80 or fuzz.partial_ratio(cleaned_query, generic_name) > 80:
            filtered_products.append(product)
    
    # If no filtered products, fallback to all products
    if not filtered_products:
        filtered_products = products
    
    # Format the response with comprehensive information for every product
    formatted_products = []
    for product in filtered_products:
        product_name = product.get('name', '')
        generic_name = extract_generic_name_from_trade_name(product_name)
        # Get comprehensive medical information for every product
        medical_info = get_comprehensive_medical_info(product_name, generic_name, query)
        # Merge/override with any info already present in the product
        if 'components' in product and product['components']:
            medical_info['active_ingredients'] = product['components']
        if 'desc' in product and product['desc']:
            medical_info['usage'] = product['desc']
        formatted_product = {
            'id': product.get('id'),
            'trade_name': product.get('name', ''),
            'price': product.get('price'),
            'currency': 'EGP',
            'image': product.get('image'),
            'description': product.get('desc', ''),
            'components': product.get('components', []),
            'company': product.get('company', ''),
            'usage': medical_info['usage'],
            'source': 'External API',
            'last_updated': time.time(),
            'medical_info': medical_info
        }
        formatted_products.append(formatted_product)
    
    return jsonify({
        'success': True,
        'products': formatted_products,
        'count': len(formatted_products)
    })

def get_comprehensive_medical_info(trade_name: str, generic_name: str, original_query: str) -> dict:
    """
    Get comprehensive medical information for a medicine including:
    - Active ingredients
    - Usage/indications
    - Contraindications
    - Warnings
    - Side effects
    - Dosage information
    - Drug interactions
    """
    medical_info = {
        'active_ingredients': [],
        'usage': '',
        'contraindications': '',
        'warnings': '',
        'side_effects': '',
        'dosage': '',
        'drug_interactions': '',
        'generic_name': generic_name,
        'drug_class': '',
        'pregnancy_category': '',
        'breastfeeding': '',
        'pediatric_use': '',
        'geriatric_use': ''
    }
    
    # Try to get information from multiple sources
    medicine_name = trade_name or original_query
    
    # 1. Get active ingredients from local database
    active_ingredients = get_active_ingredients(medicine_name)
    if active_ingredients:
        medical_info['active_ingredients'] = active_ingredients
    
    # 2. Get usage information from fallback chain
    usage_info = get_usage_generic(medicine_name, generic_name)
    if usage_info:
        medical_info['usage'] = usage_info
    
    # 3. Get detailed information from RxNav API
    try:
        success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
        if success and drug_info:
            # Extract additional information from RxNav
            if drug_info.get('usage_text'):
                medical_info['usage'] = drug_info['usage_text']
            
            # Get drug class and other properties
            rxcui = drug_info.get('rxcui')
            if rxcui:
                additional_info = get_rxnav_detailed_info(rxcui)
                medical_info.update(additional_info)
    except Exception as e:
        print(f"[DEBUG] RxNav API error for {medicine_name}: {e}")
    
    # 4. Get additional information from openFDA API
    try:
        fda_info = get_openfda_detailed_info(medicine_name, generic_name)
        if fda_info:
            medical_info.update(fda_info)
    except Exception as e:
        print(f"[DEBUG] openFDA API error for {medicine_name}: {e}")
    
    # 5. Get additional information from DailyMed API
    try:
        dailymed_info = get_dailymed_detailed_info(medicine_name, generic_name)
        if dailymed_info:
            medical_info.update(dailymed_info)
    except Exception as e:
        print(f"[DEBUG] DailyMed API error for {medicine_name}: {e}")
    
    return medical_info

def get_active_ingredients(medicine_name: str) -> list:
    """Get active ingredients for a medicine from local database."""
    print(f"[DEBUG] [get_active_ingredients] Looking for: {medicine_name}")
    
    # FIRST: Try the actual database (your extracted data)
    db_ingredients = get_active_ingredients_from_database(medicine_name)
    if db_ingredients:
        print(f"[DEBUG] [get_active_ingredients] Found in database: {db_ingredients}")
        return db_ingredients
    
    # FALLBACK: Use hardcoded dictionary for common medicines
    active_ingredients_db = {
        'lipitor': ['Atorvastatin'],
        'ليبيتور': ['Atorvastatin'],
        'atorvastatin': ['Atorvastatin'],
        'panadol': ['Paracetamol', 'Acetaminophen'],
        'بانادول': ['Paracetamol', 'Acetaminophen'],
        'paracetamol': ['Paracetamol', 'Acetaminophen'],
        'acetaminophen': ['Acetaminophen', 'Paracetamol'],
        'advil': ['Ibuprofen'],
        'motrin': ['Ibuprofen'],
        'ibuprofen': ['Ibuprofen'],
        'brufen': ['Ibuprofen'],
        'aspirin': ['Acetylsalicylic acid'],
        'claritine': ['Loratadine'],
        'claritin': ['Loratadine'],
        'claratyne': ['Loratadine'],
        'loratadine': ['Loratadine'],
        'prozac': ['Fluoxetine'],
        'fluoxetine': ['Fluoxetine'],
        'zoloft': ['Sertraline'],
        'sertraline': ['Sertraline'],
        'augmentin': ['Amoxicillin', 'Clavulanic acid'],
        'amoxicillin': ['Amoxicillin'],
        'voltaren': ['Diclofenac'],
        'diclofenac': ['Diclofenac'],
        'rivo': ['Rivaroxaban'],
        'rivaroxaban': ['Rivaroxaban'],
        'xarelto': ['Rivaroxaban'],
        'metformin': ['Metformin'],
        'glucophage': ['Metformin'],
        'cidophage': ['Metformin'],
        'ozempic': ['Semaglutide'],
        'semaglutide': ['Semaglutide'],
        'lantus': ['Insulin glargine'],
        'insulin glargine': ['Insulin glargine'],
        'humalog': ['Insulin lispro'],
        'insulin lispro': ['Insulin lispro'],
        'concor': ['Bisoprolol'],
        'bisoprolol': ['Bisoprolol'],
        'norvasc': ['Amlodipine'],
        'amlor': ['Amlodipine'],
        'amlodipine': ['Amlodipine'],
        'zocor': ['Simvastatin'],
        'simvastatin': ['Simvastatin'],
        'crestor': ['Rosuvastatin'],
        'rosuvastatin': ['Rosuvastatin'],
        'plavix': ['Clopidogrel'],
        'clopidogrel': ['Clopidogrel'],
        'zyrtec': ['Cetirizine'],
        'cetirizine': ['Cetirizine'],
        'alerid': ['Cetirizine'],
        'allegra': ['Fexofenadine'],
        'fexofenadine': ['Fexofenadine'],
        'benadryl': ['Diphenhydramine'],
        'diphenhydramine': ['Diphenhydramine'],
        
        # FIXED: Added missing medicines from user's questions
        'protonix': ['Pantoprazole'],
        'pantoprazole': ['Pantoprazole'],
        'omeprazole': ['Omeprazole'],
        'prilosec': ['Omeprazole'],
        'losec': ['Omeprazole'],
        'nexium': ['Esomeprazole'],
        'esomeprazole': ['Esomeprazole'],
        'zantac': ['Ranitidine'],
        'ranitidine': ['Ranitidine'],
        'levothyroxine': ['Levothyroxine'],
        'synthroid': ['Levothyroxine'],
        'montelukast': ['Montelukast'],
        'singulair': ['Montelukast'],
        'lisinopril': ['Lisinopril'],
        'hydrochlorothiazide': ['Hydrochlorothiazide'],
        'metoprolol': ['Metoprolol'],
        'carvedilol': ['Carvedilol'],
        'warfarin': ['Warfarin'],
        'coumadin': ['Warfarin'],
        'digoxin': ['Digoxin'],
        'furosemide': ['Furosemide'],
        'lasix': ['Furosemide'],
        'naproxen': ['Naproxen'],
        'aleve': ['Naproxen'],
        'tylenol': ['Acetaminophen'],
        'celebrex': ['Celecoxib'],
        'celecoxib': ['Celecoxib'],
        'losartan': ['Losartan'],
        'cozaar': ['Losartan'],
        'valsartan': ['Valsartan'],
        'diovan': ['Valsartan'],
        
        # Antipsychotics
        'zyprexa': ['Olanzapine'],
        'olanzapine': ['Olanzapine'],
        'abilify': ['Aripiprazole'],
        'aripiprazole': ['Aripiprazole'],
        'risperdal': ['Risperidone'],
        'risperidone': ['Risperidone'],
        'seroquel': ['Quetiapine'],
        'quetiapine': ['Quetiapine'],
        
        # Other antidepressants
        'paxil': ['Paroxetine'],
        'paroxetine': ['Paroxetine'],
        'celexa': ['Citalopram'],
        'citalopram': ['Citalopram'],
        'lexapro': ['Escitalopram'],
        'escitalopram': ['Escitalopram'],
        'wellbutrin': ['Bupropion'],
        'bupropion': ['Bupropion'],
        'effexor': ['Venlafaxine'],
        'venlafaxine': ['Venlafaxine'],
        'cymbalta': ['Duloxetine'],
        'duloxetine': ['Duloxetine'],
        
        # Nasal sprays and allergy medications - FIXED: Added Flonase and related medicines
        'flonase': ['Fluticasone propionate'],
        'fluticasone': ['Fluticasone propionate'],
        'nasacort': ['Triamcinolone acetonide'],
        'triamcinolone': ['Triamcinolone acetonide'],
        'rhinocort': ['Budesonide'],
        'budesonide': ['Budesonide'],
        'nasonex': ['Mometasone furoate'],
        'mometasone': ['Mometasone furoate'],
        'afrin': ['Oxymetazoline'],
        'oxymetazoline': ['Oxymetazoline'],
        'sudafed': ['Pseudoephedrine'],
        'pseudoephedrine': ['Pseudoephedrine'],
        'claritin-d': ['Loratadine', 'Pseudoephedrine'],
        'mucinex': ['Guaifenesin'],
        'guaifenesin': ['Guaifenesin'],
        
        # Ibuprofen and common misspellings/brands
        'ibuprofen': ['Ibuprofen'],
        'أيبوبروفين': ['أيبوبروفين'],
        'الأيبوبروفين': ['الأيبوبروفين'],
        'brufen': ['Brufen'],
        'ibubrufen': ['Ibubrufen'],
        'ibuprufen': ['Ibuprufen'],
        'ibuprophen': ['Ibuprophen'],
        'ibuprofene': ['Ibuprofene'],
        'ibufren': ['Ibufren'],
        'epipen': 'epinephrine',
        'toprol xl': 'metoprolol',
        'toprol': 'metoprolol',
    }
    
    clean_name = medicine_name.lower().strip()
    
    # Check exact match
    if clean_name in active_ingredients_db:
        return active_ingredients_db[clean_name]
    
    # Check partial matches
    for key, ingredients in active_ingredients_db.items():
        if clean_name in key or key in clean_name:
            return ingredients
    
    # Extract base name from Arabic medicine names
    if is_arabic_text(clean_name):
        # Remove common Arabic words and dosage info
        arabic_clean = re.sub(r'\d+\s*مجم', '', clean_name)  # Remove mg dosage
        arabic_clean = re.sub(r'\d+\s*قرص', '', arabic_clean)  # Remove tablet count
        arabic_clean = re.sub(r'\d+\s*اقراص', '', arabic_clean)  # Remove tablet count (plural)
        arabic_clean = re.sub(r'\s+', ' ', arabic_clean).strip()  # Clean spaces
        
        # Check if cleaned Arabic name matches any known medicine
        if arabic_clean in active_ingredients_db:
            return active_ingredients_db[arabic_clean]
    
    print(f"[DEBUG] [get_active_ingredients] No ingredients found for: {medicine_name}")
    return []

def get_rxnav_detailed_info(rxcui: str) -> dict:
    """Get detailed information from RxNav API."""
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/allProperties.json"
        response = requests.get(url, params={"prop": "all"}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            info = {}
            
            if 'propConceptGroup' in data and 'propConcept' in data['propConceptGroup']:
                for prop in data['propConceptGroup']['propConcept']:
                    prop_name = prop.get('propName', '').lower()
                    prop_value = prop.get('propValue', '')
                    
                    if 'contraindication' in prop_name:
                        info['contraindications'] = prop_value
                    elif 'warning' in prop_name:
                        info['warnings'] = prop_value
                    elif 'side effect' in prop_name or 'adverse' in prop_name:
                        info['side_effects'] = prop_value
                    elif 'dosage' in prop_name or 'dose' in prop_name:
                        info['dosage'] = prop_value
                    elif 'interaction' in prop_name:
                        info['drug_interactions'] = prop_value
                    elif 'drug class' in prop_name or 'therapeutic class' in prop_name:
                        info['drug_class'] = prop_value
                    elif 'pregnancy' in prop_name:
                        info['pregnancy_category'] = prop_value
                    elif 'breastfeeding' in prop_name or 'lactation' in prop_name:
                        info['breastfeeding'] = prop_value
                    elif 'pediatric' in prop_name or 'children' in prop_name:
                        info['pediatric_use'] = prop_value
                    elif 'geriatric' in prop_name or 'elderly' in prop_name:
                        info['geriatric_use'] = prop_value
            
            return info
    except Exception as e:
        print(f"[DEBUG] RxNav detailed info error: {e}")
    
    return {}

def get_openfda_detailed_info(medicine_name: str, generic_name: str) -> dict:
    """Get detailed information from openFDA API."""
    try:
        # Try with generic name first, then trade name
        search_name = generic_name if generic_name else medicine_name
        
        url = "https://api.fda.gov/drug/label.json"
        params = {
            'search': f'openfda.generic_name:{search_name}',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                info = {}
                
                # Extract various sections
                if 'contraindications' in result:
                    info['contraindications'] = result['contraindications'][0] if result['contraindications'] else ''
                
                if 'warnings' in result:
                    info['warnings'] = result['warnings'][0] if result['warnings'] else ''
                
                if 'adverse_reactions' in result:
                    info['side_effects'] = result['adverse_reactions'][0] if result['adverse_reactions'] else ''
                
                if 'dosage_and_administration' in result:
                    info['dosage'] = result['dosage_and_administration'][0] if result['dosage_and_administration'] else ''
                
                if 'drug_interactions' in result:
                    info['drug_interactions'] = result['drug_interactions'][0] if result['drug_interactions'] else ''
                
                if 'pregnancy' in result:
                    info['pregnancy_category'] = result['pregnancy'][0] if result['pregnancy'] else ''
                
                if 'nursing_mothers' in result:
                    info['breastfeeding'] = result['nursing_mothers'][0] if result['nursing_mothers'] else ''
                
                if 'pediatric_use' in result:
                    info['pediatric_use'] = result['pediatric_use'][0] if result['pediatric_use'] else ''
                
                if 'geriatric_use' in result:
                    info['geriatric_use'] = result['geriatric_use'][0] if result['geriatric_use'] else ''
                
                return info
    except Exception as e:
        print(f"[DEBUG] openFDA detailed info error: {e}")
    
    return {}

def get_dailymed_detailed_info(medicine_name: str, generic_name: str) -> dict:
    """Get detailed information from DailyMed API."""
    try:
        # Try with generic name first, then trade name
        search_name = generic_name if generic_name else medicine_name
        
        # Step 1: Get drug names to find setid
        url1 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json"
        params1 = {'drug_name': search_name.lower()}
        
        response1 = requests.get(url1, params=params1, timeout=10)
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            if data1.get('data'):
                setid = data1['data'][0].get('setid')
                
                if setid:
                    # Step 2: Get detailed information
                    url2 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.json"
                    response2 = requests.get(url2, timeout=10)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        info = {}
                        
                        # Extract various sections from the label
                        if 'openfda' in data2:
                            openfda = data2['openfda']
                            
                            if 'generic_name' in openfda:
                                info['generic_name'] = openfda['generic_name'][0] if openfda['generic_name'] else ''
                            if 'brand_name' in openfda:
                                info['brand_name'] = openfda['brand_name'][0] if openfda['brand_name'] else ''
                        
                        # Extract active ingredients
                        if 'active_ingredient' in data2:
                            info['active_ingredients'] = data2['active_ingredient']
                        
                        # Extract other sections
                        sections = data2.get('sections', [])
                        for section in sections:
                            title = section.get('title', '').lower()
                            content = section.get('content', '')
                            
                            if 'contraindication' in title:
                                info['contraindications'] = content
                            elif 'warning' in title:
                                info['warnings'] = content
                            elif 'adverse' in title or 'side effect' in title:
                                info['side_effects'] = content
                            elif 'dosage' in title:
                                info['dosage'] = content
                            elif 'interaction' in title:
                                info['drug_interactions'] = content
                            elif 'pregnancy' in title:
                                info['pregnancy_category'] = content
                            elif 'nursing' in title or 'breastfeeding' in title:
                                info['breastfeeding'] = content
                            elif 'pediatric' in title:
                                info['pediatric_use'] = content
                            elif 'geriatric' in title:
                                info['geriatric_use'] = content
                        
                        return info
    except Exception as e:
        print(f"[DEBUG] DailyMed detailed info error: {e}")
    
    return {}

def extract_generic_name_from_trade_name(trade_name: str) -> str:
    """
    Extract generic name from trade name using common patterns.
    This is a simple heuristic and may not work for all cases.
    
    Args:
        trade_name (str): Trade name of the medicine
        
    Returns:
        str: Extracted generic name or empty string
    """
    # Common medicine mappings (including Arabic variations)
    medicine_mappings = {
        # Pain relievers
        'panadol': 'paracetamol',
        'بانادول': 'paracetamol',
        'tylenol': 'paracetamol',
        'acetaminophen': 'paracetamol',
        'advil': 'ibuprofen',
        'motrin': 'ibuprofen',
        'aspirin': 'acetylsalicylic acid',
        
        # Cholesterol medications
        'lipitor': 'atorvastatin',
        'ليبيتور': 'atorvastatin',
        'zocor': 'simvastatin',
        'crestor': 'rosuvastatin',
        'atorvastatin': 'atorvastatin',  # Generic name mapping
        'simvastatin': 'simvastatin',   # Generic name mapping
        'rosuvastatin': 'rosuvastatin', # Generic name mapping
        
        # Blood thinners
        'plavix': 'clopidogrel',
        'warfarin': 'warfarin',
        'coumadin': 'warfarin',
        
        # Antidepressants
        'zoloft': 'sertraline',
        'prozac': 'fluoxetine',
        'paxil': 'paroxetine',
        'celexa': 'citalopram',
        'lexapro': 'escitalopram',
        'wellbutrin': 'bupropion',
        'effexor': 'venlafaxine',
        'cymbalta': 'duloxetine',
        
        # Antipsychotics
        'zyprexa': 'olanzapine',
        'abilify': 'aripiprazole',
        'risperdal': 'risperidone',
        'seroquel': 'quetiapine',
        'geodon': 'ziprasidone',
        'invega': 'paliperidone',
        'latuda': 'lurasidone',
        'rexulti': 'brexpiprazole',
        'vraylar': 'cariprazine',
        'fanapt': 'iloperidone',
        'saphris': 'asenapine',
        
        # Antihistamines
        'claritine': 'loratadine',
        'claritin': 'loratadine',
        'claratyne': 'loratadine',
        'allegra': 'fexofenadine',
        'zyrtec': 'cetirizine',
        'benadryl': 'diphenhydramine',
        
        # Diabetes medications
        'ozempic': 'semaglutide',
        'lantus': 'insulin glargine',
        'humalog': 'insulin lispro',
        'glucophage': 'metformin',
        'cidophage': 'metformin',
        'metformin': 'metformin',   # Generic name mapping
        
        # Blood pressure medications
        'concor': 'bisoprolol',
        'norvasc': 'amlodipine',
        'amlor': 'amlodipine',
        'amlodipine': 'amlodipine', # Generic name mapping
        'lisinopril': 'lisinopril', # Generic name mapping
        'hydrochlorothiazide': 'hydrochlorothiazide', # Generic name mapping
        'metoprolol': 'metoprolol', # Generic name mapping
        'carvedilol': 'carvedilol', # Generic name mapping
        
        # Blood thinners
        'rivo': 'rivaroxaban',
        'xarelto': 'rivaroxaban',
        
        # Anti-inflammatory
        'voltaren': 'diclofenac',
        'cataflam': 'diclofenac',
        
        # Antibiotics
        'augmentin': 'amoxicillin',
        
        # Proton pump inhibitors / Acid reducers - FIXED: Added missing medicines
        'protonix': 'pantoprazole',
        'pantoprazole': 'pantoprazole', # Generic name mapping
        'prilosec': 'omeprazole',
        'losec': 'omeprazole',
        'omeprazole': 'omeprazole',   # Generic name mapping
        'nexium': 'esomeprazole',
        'esomeprazole': 'esomeprazole', # Generic name mapping
        'zantac': 'ranitidine',
        'ranitidine': 'ranitidine',   # Generic name mapping
        
        # Thyroid medications - FIXED: Added missing medicines
        'synthroid': 'levothyroxine',
        'levothyroxine': 'levothyroxine', # Generic name mapping
        
        # Asthma/Allergy medications - FIXED: Added missing medicines
        'singulair': 'montelukast',
        'montelukast': 'montelukast',   # Generic name mapping
        
        # Other cardiac medications
        'digoxin': 'digoxin',         # Generic name mapping
        'furosemide': 'furosemide',   # Generic name mapping
        'lasix': 'furosemide',
        
        # Other common medicines
        'brufen': 'ibuprofen',
        'alerid': 'cetirizine',
        'ibuprofen': 'ibuprofen',     # Generic name mapping
        'cetirizine': 'cetirizine',   # Generic name mapping
        'naproxen': 'naproxen',       # Generic name mapping
        'aleve': 'naproxen',
        
        # Nasal sprays - FIXED: Proper generic name mappings
        'flonase': 'fluticasone propionate',
        'fluticasone': 'fluticasone propionate',
        'nasacort': 'triamcinolone acetonide',
        'triamcinolone': 'triamcinolone acetonide',
        'rhinocort': 'budesonide',
        'budesonide': 'budesonide',
        'nasonex': 'mometasone furoate',
        'mometasone': 'mometasone furoate',
        'afrin': 'oxymetazoline',
        'oxymetazoline': 'oxymetazoline',
        'sudafed': 'pseudoephedrine',
        'pseudoephedrine': 'pseudoephedrine',
        'claritin-d': ['Loratadine', 'Pseudoephedrine'],
        'mucinex': ['Guaifenesin'],
        'guaifenesin': ['Guaifenesin'],
        
        # Ibuprofen and common misspellings/brands
        'ibuprofen': ['Ibuprofen'],
        'أيبوبروفين': ['أيبوبروفين'],
        'الأيبوبروفين': ['الأيبوبروفين'],
        'brufen': ['Brufen'],
        'ibubrufen': ['Ibubrufen'],
        'ibuprufen': ['Ibuprufen'],
        'ibuprophen': ['Ibuprophen'],
        'ibuprofene': ['Ibuprofene'],
        'ibufren': ['Ibufren'],
        'epipen': 'epinephrine',
        'toprol xl': 'metoprolol',
        'toprol': 'metoprolol',
    }
    
    clean_name = trade_name.lower().strip()
    
    # Check exact match
    if clean_name in medicine_mappings:
        return medicine_mappings[clean_name]
    
    # Check partial matches
    for trade, generic in medicine_mappings.items():
        if clean_name in trade or trade in clean_name:
            return generic
    
    # Extract base name from Arabic medicine names
    if is_arabic_text(clean_name):
        # Remove common Arabic words and dosage info
        arabic_clean = re.sub(r'\d+\s*مجم', '', clean_name)  # Remove mg dosage
        arabic_clean = re.sub(r'\d+\s*قرص', '', arabic_clean)  # Remove tablet count
        arabic_clean = re.sub(r'\d+\s*اقراص', '', arabic_clean)  # Remove tablet count (plural)
        arabic_clean = re.sub(r'\s+', ' ', arabic_clean).strip()  # Clean spaces
        
        # Check if cleaned Arabic name matches any known medicine
        if arabic_clean in medicine_mappings:
            return medicine_mappings[arabic_clean]
    
    return ""

# Global conversation memory (in production, use Redis or database)
conversation_context = {}

@medicine_bp.route('/medicines/chat', methods=['POST'])
def crewai_chat():
    """
    CrewAI-powered chat endpoint with persistent memory.
    Accepts: {"message": "<user text>", "question": "<user text>", "user_id": "<id>"}
    Returns: {"reply": "<bot answer>"}
    """
    data = request.get_json()
    print(f"[DEBUG] Raw data: {data}")  # Debug print for raw POST data
    question = (data.get("message") or data.get("question") or "").strip() if data else ''
    user_id = data.get("user_id", "default") if data else 'default'
    print(f"[DEBUG] Received chat: {question} from {user_id}")  # Debug print
    if not question:
        print("[DEBUG] No question provided.")
        return jsonify({"reply": "Please enter a message."})
    reply = answer_medicine_question(question, user_id)
    print(f"[DEBUG] Final reply: {reply}")  # Debug print
    return jsonify({"reply": reply})

def get_medicine_usage(medicine_name):
    """Get medicine usage information with API-first approach (RxNav, OpenFDA, DailyMed, then local DB)."""
    print(f"[DEBUG] [get_medicine_usage] Getting usage for: {medicine_name}")
    errors = []
    # PRIORITY 1: Try RxNav API first
    try:
        success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
        if success and drug_info:
            print(f"[DEBUG] [get_medicine_usage] Found data in RxNav API")
            if drug_info.get('usage_text') and drug_info['usage_text'] != 'Usage information not available':
                print(f"[DEBUG] [get_medicine_usage] Found detailed usage in RxNav API")
                return f"{medicine_name.title()} is used for: {drug_info['usage_text']}"
            elif drug_info.get('generic_name'):
                generic_name = drug_info['generic_name'].lower()
                print(f"[DEBUG] [get_medicine_usage] No detailed usage, but found generic name: {generic_name}")
                if 'statin' in generic_name or 'vastatin' in generic_name:
                    return f"{medicine_name.title()} is used for: {medicine_name.title()} ({drug_info['generic_name']}) is used to lower cholesterol and reduce the risk of heart disease and stroke."
                elif 'sartan' in generic_name:
                    return f"{medicine_name.title()} is used for: {medicine_name.title()} ({drug_info['generic_name']}) is used to treat high blood pressure and protect the kidneys in patients with diabetes."
                elif 'pril' in generic_name:
                    return f"{medicine_name.title()} is used for: {medicine_name.title()} ({drug_info['generic_name']}) is used to treat high blood pressure and heart failure."
                elif 'dipine' in generic_name:
                    return f"{medicine_name.title()} is used for: {medicine_name.title()} ({drug_info['generic_name']}) is used to treat high blood pressure and chest pain (angina)."
                else:
                    return f"{medicine_name.title()} is used for: {medicine_name.title()} contains {drug_info['generic_name']}. For specific usage information, please consult your doctor or pharmacist."
    except Exception as e:
        print(f"[DEBUG] [get_medicine_usage] RxNav API error: {e}")
        errors.append(f"RxNav: {e}")
    # PRIORITY 2: Try OpenFDA API
    try:
        print(f"[DEBUG] [get_medicine_usage] Trying openFDA for: {medicine_name}")
        import requests
        url = "https://api.fda.gov/drug/label.json"
        params = {
            'search': f'openfda.brand_name:"{medicine_name}"',
            'limit': 1
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                result = data['results'][0]
                if 'indications_and_usage' in result:
                    usage = result['indications_and_usage'][0]
                    print(f"[DEBUG] [get_medicine_usage] Found usage in OpenFDA: {usage}")
                    return f"{medicine_name.title()} is used for: {usage}"
    except Exception as e:
        print(f"[DEBUG] [get_medicine_usage] openFDA error: {e}")
        errors.append(f"OpenFDA: {e}")
    # PRIORITY 3: Try DailyMed API
    try:
        print(f"[DEBUG] [get_medicine_usage] Trying DailyMed for: {medicine_name}")
        import requests
        # Step 1: Get drug names to find setid
        url1 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json"
        params1 = {'drug_name': medicine_name.lower()}
        response1 = requests.get(url1, params=params1, timeout=10)
        if response1.status_code == 200:
            data1 = response1.json()
            if data1.get('data'):
                setid = data1['data'][0].get('setid')
                if setid:
                    # Step 2: Get detailed information
                    url2 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.json"
                    response2 = requests.get(url2, timeout=10)
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if 'indications_and_usage' in data2:
                            usage = data2['indications_and_usage']
                            print(f"[DEBUG] [get_medicine_usage] Found usage in DailyMed: {usage}")
                            return f"{medicine_name.title()} is used for: {usage}"
    except Exception as e:
        print(f"[DEBUG] [get_medicine_usage] DailyMed error: {e}")
        errors.append(f"DailyMed: {e}")
    # LAST RESORT: Check local database
    print(f"[DEBUG] [get_medicine_usage] APIs failed, trying local database")
    
    # Try the actual database first (your extracted data)
    db_usage = get_medicine_usage_from_database(medicine_name)
    if db_usage:
        print(f"[DEBUG] [get_medicine_usage] Found usage in database: {db_usage}")
        return f"{medicine_name.title()} is used for: {db_usage}"
    
    # Fallback to hardcoded usage
    usage = get_local_usage(medicine_name)
    if usage:
        print(f"[DEBUG] [get_medicine_usage] Found usage in hardcoded database")
        return f"{medicine_name.title()} is used for: {usage}"
    
    print(f"[DEBUG] [get_medicine_usage] No usage information found anywhere. Errors: {errors}")
    return f"Sorry, I couldn't find usage information for {medicine_name.title()}."

def get_medicine_price(medicine_name):
    success, products, error = medicine_api.search_and_get_details(medicine_name)
    if success and products:
        product = products[0]
        name = product.get('name', medicine_name.title())
        price = product.get('price', None)
        currency = 'EGP'
        if price:
            return f"The price of {name} is {price} {currency}."
        else:
            return f"Sorry, I couldn't find the price for {name}."
    return f"Sorry, I couldn't find any information for {medicine_name.title()}."

def answer_medicine_question(question: str, user_id: str = 'default') -> str:
    """Intelligent medicine Q&A system that can handle various types of questions."""
    global conversation_context
    print(f"[DEBUG] answer_medicine_question called with question='{question}', user_id='{user_id}'")

    # Store original question
    original_question = question.strip()
    question_lower = question.lower().strip()
    print(f"[DEBUG] Normalized question: '{question_lower}'")
    
    # Handle common greetings and non-medical queries FIRST
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'good afternoon']
    arabic_greetings = ['مرحبا', 'أهلا', 'اهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير']
    farewells = ['bye', 'goodbye', 'see you', 'thanks', 'thank you', 'شكرا', 'وداعا']
    
    # Check if the question is just a greeting
    if (question_lower in greetings or 
        any(greeting in question_lower for greeting in greetings + arabic_greetings) or
        question_lower in farewells or
        any(farewell in question_lower for farewell in farewells)):
        return "Hello! I'm here to help you with medicine information. You can ask me about:\n• Medicine prices: 'What is the price of Panadol?'\n• Medicine usage: 'What is Lipitor used for?'\n• Active ingredients: 'What are the ingredients in Claritine?'\n• Medicine comparisons: 'What is the difference between Panadol and Brufen?'\n\nHow can I help you today?"
    
    # Ensure user context exists first
    if user_id not in conversation_context:
        conversation_context[user_id] = {'last_medicine': None, 'variants': []}
        print(f"[DEBUG] Initialized conversation context for user: {user_id}")
    
    # Get user's conversation context
    user_context = conversation_context.get(user_id, {})
    last_medicine = user_context.get('last_medicine', None)
    variants = user_context.get('variants', [])
    print(f"[DEBUG] User context: last_medicine={last_medicine}, variants_count={len(variants)}")
    
    # --- NEW: Handle pending medicine confirmation ---
    if user_context.get('pending_medicine_confirmation'):
        if question_lower in ['yes', 'y', 'ايوه', 'نعم']:
            medicine_name = user_context['pending_medicine_confirmation']
            print(f"[DEBUG] User confirmed medicine: {medicine_name}")
            conversation_context[user_id]['last_medicine'] = medicine_name
            original_question_text = user_context.get('pending_question', '')
            conversation_context[user_id]['pending_medicine_confirmation'] = None
            conversation_context[user_id]['pending_question'] = None
            
            # Determine what type of question was asked and respond appropriately
            original_lower = original_question_text.lower()
            print(f"[DEBUG] Processing confirmed medicine '{medicine_name}' for original question: '{original_question_text}'")
            
            # Check what type of question was originally asked
            if any(keyword in original_lower for keyword in ['price', 'cost', 'how much', 'costs']):
                print(f"[DEBUG] Original was price question, getting price for {medicine_name}")
                return get_medicine_price(medicine_name)
            elif any(keyword in original_lower for keyword in ['usage', 'used for', 'indications', 'what is', 'what does', 'purpose', 'treat', 'treats']):
                print(f"[DEBUG] Original was usage question, getting usage for {medicine_name}")
                return get_medicine_usage(medicine_name)
            elif any(keyword in original_lower for keyword in ['active ingredient', 'ingredients', 'contains', 'what is in']):
                print(f"[DEBUG] Original was ingredient question, getting ingredients for {medicine_name}")
                ingredients = get_active_ingredients(medicine_name)
                if ingredients:
                    return f"The active ingredient(s) in {medicine_name.title()} is/are: {', '.join(ingredients)}"
                else:
                    return f"I couldn't find the active ingredients for {medicine_name.title()}."
            else:
                # For other questions, provide general info
                print(f"[DEBUG] Original was general question, getting general info for {medicine_name}")
                return get_medicine_usage(medicine_name)
                
        elif question_lower in ['no', 'n', 'لا', 'لأ', 'nope']:
            # Try next best match or ask for clarification
            prev_match = user_context['pending_medicine_confirmation']
            # Remove previous best match and try again
            # Get the medicine_names list from extract_medicine_name_from_question
            medicine_names = [
                'panadol', 'بانادول', 'البانادول', 'lipitor', 'ليبيتور', 'الليبيتور', 
                'claritine', 'claritin', 'claratyne', 'prozac', 'zoloft', 'augmentin', 'أوجمنتين', 'الأوجمنتين',
                'voltaren', 'فولتارين', 'الفولتارين', 'concor', 'كونكور', 'الكونكور', 
                'norvasc', 'zocor', 'crestor', 'plavix', 'zyprexa', 'abilify', 'risperdal', 'seroquel',
                'allegra', 'أليجرا', 'الأليجرا', 'zyrtec', 'زيرتيك', 'الزيرتيك', 
                'benadryl', 'بينادريل', 'البينادريل', 'tylenol', 'advil', 'motrin', 'aspirin', 'أسبيرين', 'الأسبيرين',
                'ozempic', 'lantus', 'humalog', 'glucophage', 'metformin', 'ميتفورمين', 'الميتفورمين',
                'rivo', 'ريفو', 'الريفو', 'xarelto', 'cetirizine', 'سيتريزين', 'السيتريزين',
                # Additional medicines - FIXED: Added missing medicines
                'aleve', 'naproxen', 'cozaar', 'losartan', 'nexium', 'esomeprazole', 'zantac', 'ranitidine',
                'prilosec', 'omeprazole', 'celebrex', 'celecoxib', 'diovan', 'valsartan',
                'protonix', 'pantoprazole', 'levothyroxine', 'synthroid', 'montelukast', 'singulair',
                'atorvastatin', 'simvastatin', 'rosuvastatin', 'amlodipine', 'lisinopril', 'hydrochlorothiazide',
                'warfarin', 'coumadin', 'digoxin', 'furosemide', 'lasix', 'metoprolol', 'carvedilol',
                # Nasal sprays and allergy medications - FIXED: Added Flonase and related medicines
                'flonase', 'nasacort', 'rhinocort', 'nasonex', 'afrin', 'sudafed', 'claritin-d', 'mucinex',
                'fluticasone', 'triamcinolone', 'budesonide', 'mometasone', 'oxymetazoline', 'pseudoephedrine',
                # Ibuprofen and common misspellings/brands
                'ibuprofen', 'أيبوبروفين', 'الأيبوبروفين', 'brufen', 'ibubrufen', 'ibuprufen', 'ibuprophen', 'ibuprofene', 'ibufren',
                # NEWLY ADDED: Missing medicines that users are asking about
                'proair hfa', 'proair', 'ventolin hfa', 'zithromax', 'azithromycin', 'neurontin', 'gabapentin',
                'amoxil', 'amoxicillin', 'keflex', 'cephalexin',
                'epipen', 'toprol xl', 'toprol',
            ]
            if prev_match in medicine_names:
                medicine_names.remove(prev_match)
            conversation_context[user_id]['pending_medicine_confirmation'] = None
            # Try to extract again
            from fuzzywuzzy import fuzz
            best_score = 0
            best_match = None
            question_text = user_context['pending_question']
            question_lower2 = question_text.lower()
            for name in medicine_names:
                score = fuzz.partial_ratio(name, question_lower2)
                if score > best_score:
                    best_score = score
                    best_match = name
            if best_score >= 70:
                conversation_context[user_id]['pending_medicine_confirmation'] = best_match
                return f"Did you mean '{best_match}'? (yes/no)"
            else:
                return "Sorry, I couldn't confidently identify the medicine. Please specify the medicine name more clearly."
        else:
            return f"Did you mean '{user_context['pending_medicine_confirmation']}'? (yes/no)"
    # --- END NEW ---
    
    # Handle variant selection by number
    if variants and question_lower.isdigit():
        variant_index = int(question_lower) - 1
        print(f"[DEBUG] User selected variant index: {variant_index}")
        if 0 <= variant_index < len(variants):
            selected_product = variants[variant_index]
            name = selected_product.get('name', 'Unknown')
            price = selected_product.get('price', 'N/A')
            currency = 'EGP'
            print(f"[DEBUG] Selected product: {selected_product}")
            
            # Extract base medicine name for usage lookup
            base_medicine_name = extract_base_medicine_name(name)
            print(f"[DEBUG] Extracted base medicine name: '{base_medicine_name}' from full name: '{name}'")
            
            # Update context
            conversation_context[user_id]['last_medicine'] = base_medicine_name
            conversation_context[user_id]['selected_variant'] = selected_product
            conversation_context[user_id]['full_variant_name'] = name
            print(f"[DEBUG] Updated context with selected variant: {name}, base name: {base_medicine_name}")
            return f"**{name}** costs **{price} {currency}**.\n\nYou can now ask:\n• 'What is the usage?' (for this variant)\n• 'Tell me more about it'\n• Or ask about another medicine"
    
    # Handle greetings and general conversation (English and Arabic)
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
    arabic_greetings = ['مرحبا', 'أهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير']
    
    if (any(greeting in question_lower for greeting in greetings) or 
        any(greeting in original_question for greeting in arabic_greetings)):
        print("[DEBUG] Greeting detected.")
        return "Hello! I'm your medicine assistant. I can help you with:\n• Medicine usage and indications\n• Medicine prices\n• General medicine information\n\nWhat would you like to know?"
    
    # Handle thanks and goodbyes
    thanks = ['thank', 'thanks', 'bye', 'goodbye', 'see you']
    if any(thank in question_lower for thank in thanks):
        print("[DEBUG] Thanks/goodbye detected.")
        return "You're welcome! Feel free to ask me anything about medicines anytime. Have a great day!"
    
    # Handle help requests
    if 'help' in question_lower or 'what can you do' in question_lower:
        print("[DEBUG] Help request detected.")
        return "I'm your medicine assistant! I can help you with:\n\n• **Usage Questions**: 'What is Panadol used for?' or 'What are the indications for Augmentin?'\n• **Price Questions**: 'What's the price of Voltaren?' or 'How much does Concor cost?'\n• **Comparison Questions**: 'What's the difference between Tylenol and Advil?'\n• **Administration Questions**: 'How should I take metformin?'\n• **General Info**: 'Tell me about Lipitor' or 'What is Rivo?'\n\nJust ask me anything about medicines!"
    
    # Handle comparison questions (check this first to avoid conflicts) (English and Arabic)
    comparison_keywords = ['difference', 'compare', 'versus', 'vs', 'between', 'and']
    arabic_comparison_keywords = ['الفرق', 'قارن', 'مقارنة', 'بين', 'و', 'أو']
    
    if (any(keyword in question_lower for keyword in comparison_keywords) or 
        any(keyword in original_question for keyword in arabic_comparison_keywords)):
        # Extract medicine names from question
        medicines = extract_multiple_medicines_from_question(question_lower)
        if len(medicines) >= 2:
            print(f"[DEBUG] Comparison question detected for medicines: {medicines}")
            comparison_info = compare_medicines(medicines[0], medicines[1])
            return comparison_info
        else:
            return "Please specify which two medicines you'd like to compare. For example:\n• 'What is the difference between Panadol and Rivo?'\n• 'Compare Lipitor and Crestor'\n• 'Panadol versus Tylenol'"
    
    # Handle active ingredient questions (English and Arabic)
    ingredient_keywords = ['active ingredient', 'active ingredint', 'ingredients', 'ingredint', 'contains', 'what is in', 'what\'s in', 'ingerin', 'ingreint', 'ingrediant', 'ingrediants', 'ingrient', 'ingrients', 'ingridient', 'ingridients']
    arabic_ingredient_keywords = ['المادة الفعالة', 'المواد الفعالة', 'المكونات', 'يحتوي', 'ما في', 'ماذا في']
    
    if (any(keyword in question_lower for keyword in ingredient_keywords) or 
        any(keyword in original_question for keyword in arabic_ingredient_keywords)):
        try:
            print(f"[DEBUG] Active ingredient question detected with keywords: {[k for k in ingredient_keywords if k in question_lower]}")
            # Extract medicine name from question text directly (API-first approach - don't check local DB first)
            potential_medicine = extract_medicine_name_from_question(question_lower, user_id)
            # If not found in local list, use the last significant word(s) as fallback
            if not potential_medicine:
                cleaned_question = question_lower
                ingredient_words = ['active', 'ingredient', 'ingredint', 'ingreint', 'ingrediant', 'ingrediants', 'ingrient', 'ingrients', 'ingridient', 'ingridients', 'ingerin', 'ingredients', 'contains', 'what', 'is', 'the', 'in', 'of', 'are']
                for word in ingredient_words:
                    cleaned_question = cleaned_question.replace(word, ' ')
                cleaned_question = re.sub(r'\s+', ' ', cleaned_question).strip()
                words = [w for w in cleaned_question.split() if len(w) > 2]
                if words:
                    # Use the last 2 words as a fallback medicine name (to handle things like 'Toprol XL')
                    fallback_medicine = ' '.join(words[-2:]) if len(words) >= 2 else words[-1]
                    print(f"[DEBUG] Fallback medicine name from question: '{fallback_medicine}'")
                    potential_medicine = fallback_medicine
            if not potential_medicine and last_medicine:
                print(f"[DEBUG] No medicine name found in question, using context: {last_medicine}")
                potential_medicine = last_medicine
            if potential_medicine:
                print(f"[DEBUG] Active ingredient question detected for medicine: {potential_medicine}")
                current_medicine = potential_medicine
                print(f"[DEBUG] Using API-first approach for: {current_medicine}")
                ingredients = get_active_ingredients_api_first(current_medicine)
                if ingredients:
                    conversation_context[user_id]['last_medicine'] = current_medicine
                    return f"The active ingredient(s) in {current_medicine.title()} is/are: {', '.join(ingredients)}"
                else:
                    return f"I couldn't find the active ingredients for {current_medicine.title()}. Please try searching for it in the search bar above."
            else:
                return "Please specify which medicine you'd like to know the active ingredients of. For example:\n• 'What is the active ingredient of Lipitor?'\n• 'What are the ingredients in Panadol?'"
        except Exception as e:
            print(f"[DEBUG] [answer_medicine_question] Exception in active ingredient logic: {e}")
            med_name = potential_medicine if 'potential_medicine' in locals() and potential_medicine else 'this medicine'
            return f"I couldn't find the active ingredients for {med_name.title()}. Please try searching for it in the search bar above."

    # Handle price questions (English and Arabic) - CHECK FIRST to avoid conflicts
    price_keywords = ['price', 'cost', 'how much', 'costs', 'prices', 'proices']
    arabic_price_keywords = ['سعر', 'تكلفة', 'كم', 'بكام', 'التكلفة', 'أسعار']
    all_prices_keywords = ['all prices', 'all proices', 'جميع الأسعار', 'كل الأسعار']
    
    # Check for "all prices" requests first
    if any(keyword in question_lower for keyword in all_prices_keywords):
        # Extract medicine name from question
        medicine_name = extract_medicine_name_from_question(question_lower, user_id)
        
        # If no medicine name found, try to use context from previous conversation
        if not medicine_name and last_medicine:
            print(f"[DEBUG] No medicine name found in all prices question, using context: {last_medicine}")
            medicine_name = last_medicine
        
        if medicine_name:
            print(f"[DEBUG] All prices question detected for medicine: {medicine_name}")
            # Update conversation context
            conversation_context[user_id]['last_medicine'] = medicine_name
            print(f"[DEBUG] Updated context with last_medicine: {medicine_name}")
            
            # Get all available products and their prices
            success, products, error = medicine_api.search_and_get_details(medicine_name)
            if success and products:
                price_list = f"**All available {medicine_name.title()} products and prices:**\n\n"
                for i, product in enumerate(products, 1):
                    name = product.get('name', 'Unknown')
                    price = product.get('price', 'N/A')
                    price_list += f"{i}. **{name}** - {price} EGP\n"
                
                # Store variants for potential selection
                conversation_context[user_id]['variants'] = products
                price_list += f"\n💡 You can type a number (1-{len(products)}) to select a specific product for more details."
                return price_list
            else:
                return f"Sorry, I couldn't find price information for {medicine_name.title()}."
        else:
            return "Please specify which medicine you'd like to see all prices for. For example:\n• 'Show me all prices of Panadol'\n• 'Give me all Augmentin prices'"
    
    elif (any(keyword in question_lower for keyword in price_keywords) or 
        any(keyword in original_question for keyword in arabic_price_keywords)):
        # For very short questions (like just "price"), prioritize context over fuzzy matching
        if len(question_lower.strip()) <= 10 and last_medicine:
            print(f"[DEBUG] Very short price question, using context: {last_medicine}")
            medicine_name = last_medicine
        else:
            # Extract medicine name from question
            medicine_name = extract_medicine_name_from_question(question_lower, user_id)
            
            # If no medicine name found, try to use context from previous conversation
            if not medicine_name and last_medicine:
                print(f"[DEBUG] No medicine name found in price question, using context: {last_medicine}")
                medicine_name = last_medicine
        
        if medicine_name:
            print(f"[DEBUG] Price question detected for medicine: {medicine_name}")
            # Update conversation context
            conversation_context[user_id]['last_medicine'] = medicine_name
            print(f"[DEBUG] Updated context with last_medicine: {medicine_name}")
            
            price_info = get_medicine_price(medicine_name)
            return price_info
        else:
            return "Please specify which medicine you'd like to know the price of. For example:\n• 'What is the price of Panadol?'\n• 'How much does Lipitor cost?'"

    # Handle usage questions (English and Arabic) - MORE SPECIFIC KEYWORDS
    usage_keywords = ['usage', 'used for', 'indications', 'purpose', 'treat', 'treats']
    # More specific usage patterns to avoid conflicts
    usage_patterns = ['what is.*used for', 'what does.*treat', 'what.*treats', 'indications for', 'purpose of']
    arabic_usage_keywords = ['استخدام', 'يستخدم', 'مؤشرات', 'الغرض', 'يعالج', 'علاج']
    
    # Check specific usage patterns first
    is_usage_question = False
    if any(keyword in question_lower for keyword in usage_keywords):
        is_usage_question = True
    elif any(keyword in original_question for keyword in arabic_usage_keywords):
        is_usage_question = True
    else:
        # Check usage patterns with regex
        for pattern in usage_patterns:
            if re.search(pattern, question_lower):
                is_usage_question = True
                break
    
    if is_usage_question:
        # Extract medicine name from question
        medicine_name = extract_medicine_name_from_question(question_lower, user_id)
        
        # If no medicine name found in local DB, try to extract from question text directly
        if not medicine_name:
            # Try to extract potential medicine name from question words
            potential_medicine = None
            question_words = question_lower.replace('usage', '').replace('used', '').replace('for', '').replace('what', '').replace('is', '').replace('the', '').replace('of', '').replace('does', '').replace('treat', '').replace('treats', '').strip()
            # Remove common words and get the remaining word as potential medicine name
            words = [w for w in question_words.split() if len(w) > 2 and w not in ['what', 'is', 'the', 'of', 'are', 'usage', 'used', 'for', 'does', 'treat', 'treats', 'purpose']]
            if words:
                potential_medicine = words[-1]  # Take the last meaningful word
                print(f"[DEBUG] Potential medicine name extracted from usage question: '{potential_medicine}'")
                
                # Try to get info from APIs for this unknown medicine
                if potential_medicine:
                    print(f"[DEBUG] Trying APIs for unknown medicine: '{potential_medicine}'")
                    try:
                        success, drug_info, error = rxnav_api.get_drug_info(potential_medicine)
                        if success and drug_info:
                            print(f"[DEBUG] Found '{potential_medicine}' in RxNav API")
                            medicine_name = potential_medicine
                            # Update conversation context
                            conversation_context[user_id]['last_medicine'] = medicine_name
                            
                            # Return the usage information from the API
                            if 'usage_text' in drug_info and drug_info['usage_text']:
                                return f"{medicine_name.title()} is used for: {drug_info['usage_text']}"
                    except Exception as e:
                        print(f"[DEBUG] RxNav API error for {potential_medicine}: {e}")
        
        # If still no medicine name found, try to use context from previous conversation
        if not medicine_name and last_medicine:
            print(f"[DEBUG] No medicine name found in usage question, using context: {last_medicine}")
            medicine_name = last_medicine
        
        if medicine_name:
            print(f"[DEBUG] Usage question detected for medicine: {medicine_name}")
            # Update conversation context
            conversation_context[user_id]['last_medicine'] = medicine_name
            print(f"[DEBUG] Updated context with last_medicine: {medicine_name}")
            
            usage_info = get_medicine_usage(medicine_name)
            return usage_info
        else:
            return "Please specify which medicine you'd like to know about. For example:\n• 'What is Panadol used for?'\n• 'What are the indications for Lipitor?'\n• 'What does Claritine treat?'"
    
    # Handle contraindication questions (English and Arabic)
    contraindication_keywords = ['contraindication', 'contraindications', 'side effect', 'side effects', 'warnings', 'precautions']
    arabic_contraindication_keywords = ['موانع الاستعمال', 'الآثار الجانبية', 'تحذيرات', 'احتياطات']
    
    if (any(keyword in question_lower for keyword in contraindication_keywords) or 
        any(keyword in original_question for keyword in arabic_contraindication_keywords)):
        # Extract medicine name from question
        medicine_name = extract_medicine_name_from_question(question_lower, user_id)
        
        # If no medicine name found, try to use context from previous conversation
        if not medicine_name and last_medicine:
            print(f"[DEBUG] No medicine name found in contraindication question, using context: {last_medicine}")
            medicine_name = last_medicine
        
        if medicine_name:
            print(f"[DEBUG] Contraindication question detected for medicine: {medicine_name}")
            # Update conversation context
            conversation_context[user_id]['last_medicine'] = medicine_name
            print(f"[DEBUG] Updated context with last_medicine: {medicine_name}")
            
            # For now, provide general guidance since we don't have detailed contraindication data
            return f"I don't have detailed contraindication information for {medicine_name.title()} in my database. For safety information, side effects, and contraindications, please:\n• Consult your doctor or pharmacist\n• Read the medicine package insert\n• Check with a healthcare professional\n\nNever stop or start medications without medical supervision."
        else:
            return "Please specify which medicine you'd like to know the contraindications for. For example:\n• 'What are the contraindications of Panadol?'\n• 'Side effects of Lipitor'"

    # For now, return a simple response for other questions
    return "I understand you're asking about medicines. Please be more specific about what you'd like to know. For example:\n• 'What is the price of Lipitor?' or 'ما هو سعر الليبيتور؟'\n• 'What is Panadol used for?' or 'ما هو استخدام البانادول؟'\n• 'What is the difference between Panadol and Rivo?' or 'ما هو الفرق بين البانادول والريفو؟'"

def extract_medicine_name_from_question(question: str, user_id: str = None) -> str:
    """Extract medicine name from a question, using fuzzy matching if needed. If fuzzy match, ask for confirmation."""
    # Common medicine names to look for (English and Arabic) - including common misspellings
    medicine_names = [
        'panadol', 'بانادول', 'البانادول', 'lipitor', 'ليبيتور', 'الليبيتور', 
        'claritine', 'claritin', 'claratyne', 'prozac', 'zoloft', 'augmentin', 'أوجمنتين', 'الأوجمنتين',
        'voltaren', 'فولتارين', 'الفولتارين', 'concor', 'كونكور', 'الكونكور', 
        'norvasc', 'zocor', 'crestor', 'plavix', 'zyprexa', 'abilify', 'risperdal', 'seroquel',
        'allegra', 'أليجرا', 'الأليجرا', 'zyrtec', 'زيرتيك', 'الزيرتيك', 
        'benadryl', 'بينادريل', 'البينادريل', 'tylenol', 'advil', 'motrin', 'aspirin', 'أسبيرين', 'الأسبيرين',
        'ozempic', 'lantus', 'humalog', 'glucophage', 'metformin', 'ميتفورمين', 'الميتفورمين',
        'rivo', 'ريفو', 'الريفو', 'xarelto', 'cetirizine', 'سيتريزين', 'السيتريزين',
        # Additional medicines - FIXED: Added missing medicines
        'aleve', 'naproxen', 'cozaar', 'losartan', 'nexium', 'esomeprazole', 'zantac', 'ranitidine',
        'prilosec', 'omeprazole', 'celebrex', 'celecoxib', 'diovan', 'valsartan',
        'protonix', 'pantoprazole', 'levothyroxine', 'synthroid', 'montelukast', 'singulair',
        'atorvastatin', 'simvastatin', 'rosuvastatin', 'amlodipine', 'lisinopril', 'hydrochlorothiazide',
        'warfarin', 'coumadin', 'digoxin', 'furosemide', 'lasix', 'metoprolol', 'carvedilol',
        # Nasal sprays and allergy medications - FIXED: Added Flonase and related medicines
        'flonase', 'nasacort', 'rhinocort', 'nasonex', 'afrin', 'sudafed', 'claritin-d', 'mucinex',
        'fluticasone', 'triamcinolone', 'budesonide', 'mometasone', 'oxymetazoline', 'pseudoephedrine',
        # Ibuprofen and common misspellings/brands
        'ibuprofen', 'أيبوبروفين', 'الأيبوبروفين', 'brufen', 'ibubrufen', 'ibuprufen', 'ibuprophen', 'ibuprofene', 'ibufren',
        # NEWLY ADDED: Missing medicines that users are asking about
        'proair hfa', 'proair', 'ventolin hfa', 'zithromax', 'azithromycin', 'neurontin', 'gabapentin',
        'amoxil', 'amoxicillin', 'keflex', 'cephalexin',
        'epipen', 'toprol xl', 'toprol',
        # ADDED: Medicines from your database
        'renese', 'mykrox', 'tolinase', 'hypaque', 'halotestin', 'dantrium', 'lithane',
    ]
    
    question_lower = question.lower()
    
    # Handle common misspellings first
    misspelling_mapping = {
        'zertic': 'zyrtec',
        'pndol': 'panadol',
        'augmantin': 'augmentin',
        'liptior': 'lipitor',
        'liptor': 'lipitor',
        'lipitur': 'lipitor',
        'claritine': 'claritin',
        'proices': 'prices',
        # Ibuprofen misspellings/brands
        'ibubrufen': 'ibuprofen',
        'ibuprufen': 'ibuprofen',
        'ibuprophen': 'ibuprofen',
        'ibuprofene': 'ibuprofen',
        'ibufren': 'ibuprofen',
        'brufen': 'ibuprofen',
        # FIXED: Add the misspelling for plavix
        'palvix': 'plavix',
    }
    
    # Check for misspellings first
    for misspelling, correct in misspelling_mapping.items():
        if misspelling in question_lower:
            print(f"[DEBUG] [extract_medicine_name_from_question] Found misspelling '{misspelling}' -> '{correct}'")
            return correct
    
    # Check for exact matches first
    for name in medicine_names:
        if name in question_lower:
            return name
    
    # Add filtering to prevent fuzzy matching on common greetings and non-medical terms
    common_greetings = ['hi', 'hello', 'hey', 'good', 'morning', 'evening', 'afternoon', 'thanks', 'thank', 'bye', 'goodbye', 'yes', 'no', 'ok', 'okay']
    arabic_greetings = ['مرحبا', 'السلام', 'صباح', 'مساء', 'شكرا', 'وداعا', 'نعم', 'لا', 'أهلا', 'اهلا']
    all_greetings = common_greetings + arabic_greetings
    
    # Skip fuzzy matching if the question is likely a greeting or very short non-medical term
    question_words = question_lower.split()
    if len(question_words) <= 2 and any(word in all_greetings for word in question_words):
        print(f"[DEBUG] [extract_medicine_name_from_question] Skipping fuzzy matching for greeting: '{question_lower}'")
        return ''
    
    # Skip fuzzy matching for very short words (less than 4 characters) unless they're known medicines
    if len(question_lower.strip()) < 4:
        print(f"[DEBUG] [extract_medicine_name_from_question] Skipping fuzzy matching for very short text: '{question_lower}'")
        return ''
    
    # Fuzzy matching (ask for confirmation if not exact) - FIXED: Improved threshold and logic
    from fuzzywuzzy import fuzz
    best_score = 0
    best_match = None
    for name in medicine_names:
        # Use both partial_ratio and ratio for better matching
        partial_score = fuzz.partial_ratio(name, question_lower)
        ratio_score = fuzz.ratio(name, question_lower)
        # Take the higher of the two scores
        score = max(partial_score, ratio_score)
        
        if score > best_score:
            best_score = score
            best_match = name
    
    print(f"[DEBUG] [extract_medicine_name_from_question] Best fuzzy match: '{best_match}' with score {best_score}")
    
    # If a good fuzzy match is found but not perfect, ask for confirmation
    # FIXED: Raised threshold to 75 to reduce false positives
    if best_score >= 75 and best_score < 100 and user_id is not None:
        # Store the suggestion in user context
        if user_id not in conversation_context:
            conversation_context[user_id] = {}
        conversation_context[user_id]['pending_medicine_confirmation'] = best_match
        conversation_context[user_id]['pending_question'] = question
        return None  # Indicate that confirmation is needed
    elif best_score == 100:
        return best_match
    
    print(f"[DEBUG] [extract_medicine_name_from_question] No good match found for: '{question_lower}'")
    
    # NEW: Try to find the medicine in the database if not in hardcoded list
    print(f"[DEBUG] [extract_medicine_name_from_question] Trying database lookup for: '{question_lower}'")
    try:
        from src.models.medicine import db
        
        # Query the database for this medicine name
        query = """
        SELECT DISTINCT trade_name, generic_name 
        FROM medicine_dailymed_complete_all 
        WHERE LOWER(trade_name) LIKE ? 
           OR LOWER(generic_name) LIKE ?
        LIMIT 1
        """
        
        result = db.session.execute(query, (f"%{question_lower}%", f"%{question_lower}%"))
        row = result.fetchone()
        
        if row and row[0]:  # Found in database
            db_medicine_name = row[0].lower().strip()
            print(f"[DEBUG] [extract_medicine_name_from_question] Found in database: '{db_medicine_name}'")
            return db_medicine_name
        elif row and row[1]:  # Found generic name
            db_generic_name = row[1].lower().strip()
            print(f"[DEBUG] [extract_medicine_name_from_question] Found generic name in database: '{db_generic_name}'")
            return db_generic_name
            
    except Exception as e:
        print(f"[DEBUG] [extract_medicine_name_from_question] Database lookup error: {e}")
    
    return ''

def extract_multiple_medicines_from_question(question: str) -> list:
    """Extract multiple medicine names from a comparison question."""
    # Common medicine names to look for (English and Arabic) - including common misspellings
    medicine_names = [
        'panadol', 'بانادول', 'البانادول', 'lipitor', 'ليبيتور', 'الليبيتور', 
        'claritine', 'claritin', 'claratyne', 'prozac', 'zoloft', 'augmentin', 'أوجمنتين', 'الأوجمنتين',
        'voltaren', 'فولتارين', 'الفولتارين', 'concor', 'كونكور', 'الكونكور', 
        'norvasc', 'zocor', 'crestor', 'plavix', 'zyprexa', 'abilify', 'risperdal', 'seroquel',
        'allegra', 'أليجرا', 'الأليجرا', 'zyrtec', 'زيرتيك', 'الزيرتيك', 
        'benadryl', 'بينادريل', 'البينادريل', 'tylenol', 'advil', 'motrin', 'aspirin', 'أسبيرين', 'الأسبيرين',
        'ozempic', 'lantus', 'humalog', 'glucophage', 'metformin', 'ميتفورمين', 'الميتفورمين',
        'rivo', 'ريفو', 'الريفو', 'xarelto', 'cetirizine', 'سيتريزين', 'السيتريزين',
        # Additional medicines - FIXED: Added missing medicines for comparison queries too
        'aleve', 'naproxen', 'cozaar', 'losartan', 'nexium', 'esomeprazole', 'zantac', 'ranitidine',
        'prilosec', 'omeprazole', 'celebrex', 'celecoxib', 'diovan', 'valsartan',
        'protonix', 'pantoprazole', 'levothyroxine', 'synthroid', 'montelukast', 'singulair',
        'atorvastatin', 'simvastatin', 'rosuvastatin', 'amlodipine', 'lisinopril', 'hydrochlorothiazide',
        'warfarin', 'coumadin', 'digoxin', 'furosemide', 'lasix', 'metoprolol', 'carvedilol',
        # Ibuprofen and common misspellings/brands
        'ibuprofen', 'أيبوبروفين', 'الأيبوبروفين', 'brufen', 'ibubrufen', 'ibuprufen', 'ibuprophen', 'ibuprofene', 'ibufren',
        'epipen', 'toprol xl', 'toprol',
    ]
    
    question_lower = question.lower()
    # FIXED: Initialize found_medicines at the beginning
    found_medicines = []
    
    # ADDED: Debug output for misspelling detection
    print(f"[DEBUG] [extract_multiple_medicines_from_question] Original question: '{question_lower}'")
    print(f"[DEBUG] [extract_multiple_medicines_from_question] Checking misspellings...")
    
    # Handle common misspellings first
    misspelling_mapping = {
        'zertic': 'zyrtec',
        'pndol': 'panadol',
        'augmantin': 'augmentin',
        'liptior': 'lipitor',
        'liptor': 'lipitor',
        'lipitur': 'lipitor',
        'claritine': 'claritin',
        'proices': 'prices',
        # Ibuprofen misspellings/brands
        'ibubrufen': 'ibuprofen',
        'ibuprufen': 'ibuprofen',
        'ibuprophen': 'ibuprofen',
        'ibuprofene': 'ibuprofen',
        'ibufren': 'ibuprofen',
        'brufen': 'ibuprofen',
        # FIXED: Add the missing misspelling for plavix
        'palvix': 'plavix',
    }
    
    # Check for exact misspellings first and correct them
    for misspelling, correct_name in misspelling_mapping.items():
        if misspelling in question_lower:
            print(f"[DEBUG] [extract_multiple_medicines_from_question] Found misspelling '{misspelling}', correcting to '{correct_name}'")
            if correct_name not in found_medicines:
                found_medicines.append(correct_name)
            # Replace misspelling in question for further processing
            question_lower = question_lower.replace(misspelling, correct_name)
        
    print(f"[DEBUG] [extract_multiple_medicines_from_question] After misspelling correction: '{question_lower}'")
    
    found_medicines = []
    
    # First, try to convert Arabic text to English
    if is_arabic_text(question):
        print(f"[DEBUG] [extract_multiple_medicines_from_question] Arabic text detected: '{question}'")
        english_conversion = arabic_to_english(question)
        if english_conversion:
            print(f"[DEBUG] [extract_multiple_medicines_from_question] Converted to English: '{english_conversion}'")
            # Check if the converted English name is in our medicine list
            if english_conversion.lower() in medicine_names:
                if english_conversion.lower() not in found_medicines:
                    found_medicines.append(english_conversion.lower())
            # Also check if any medicine name is contained in the converted text
            for medicine in medicine_names:
                if medicine in english_conversion.lower() and medicine not in found_medicines:
                    found_medicines.append(medicine)
    
    # Look for medicine names in the original question (after misspelling correction)
    for medicine in medicine_names:
        if medicine in question_lower and medicine not in found_medicines:
            found_medicines.append(medicine)
    
    # Remove duplicates by normalizing to English equivalents
    normalized_medicines = []
    english_equivalents = set()  # Track English equivalents to avoid duplicates
    
    for medicine in found_medicines:
        # Convert Arabic to English if possible
        if is_arabic_text(medicine):
            english_equivalent = arabic_to_english(medicine)
            if english_equivalent:
                # Only add if we haven't seen this English equivalent before
                if english_equivalent not in english_equivalents:
                    normalized_medicines.append(english_equivalent)
                    english_equivalents.add(english_equivalent)
            else:
                # If no English equivalent found, keep the Arabic name
                if medicine not in normalized_medicines:
                    normalized_medicines.append(medicine)
        else:
            # For English names, check if we've already added an equivalent
            if medicine not in english_equivalents and medicine not in normalized_medicines:
                normalized_medicines.append(medicine)
                english_equivalents.add(medicine)
    
    found_medicines = normalized_medicines
    
    print(f"[DEBUG] [extract_multiple_medicines_from_question] After normalization: {found_medicines}")
    
    # Ensure we have exactly 2 different medicines for comparison
    if len(found_medicines) >= 2:
        # Take the first 2 unique medicines
        found_medicines = found_medicines[:2]
    
    print(f"[DEBUG] [extract_multiple_medicines_from_question] Found medicines: {found_medicines}")
    return found_medicines

def compare_medicines(medicine1: str, medicine2: str) -> str:
    """Compare two medicines and provide differences."""
    # Get information for both medicines
    usage1 = get_medicine_usage(medicine1)
    usage2 = get_medicine_usage(medicine2)
    ingredients1 = get_active_ingredients(medicine1)
    ingredients2 = get_active_ingredients(medicine2)
    
    # Get prices for both medicines
    price1 = get_medicine_price(medicine1)
    price2 = get_medicine_price(medicine2)
    
    comparison = f"**Comparison between {medicine1.title()} and {medicine2.title()}:**\n\n"
    
    # Compare active ingredients
    comparison += f"**Active Ingredients:**\n"
    comparison += f"• {medicine1.title()}: {', '.join(ingredients1) if ingredients1 else 'Not available'}\n"
    comparison += f"• {medicine2.title()}: {', '.join(ingredients2) if ingredients2 else 'Not available'}\n\n"
    
    # Compare usage
    comparison += f"**Usage:**\n"
    comparison += f"• {medicine1.title()}: {usage1}\n"
    comparison += f"• {medicine2.title()}: {usage2}\n\n"
    
    # Compare prices
    comparison += f"**Pricing:**\n"
    comparison += f"• {medicine1.title()}: {price1}\n"
    comparison += f"• {medicine2.title()}: {price2}\n\n"
    
    # Add key differences
    comparison += "**Key Differences:**\n"
    if ingredients1 != ingredients2:
        comparison += "• They have different active ingredients\n"
    else:
        comparison += "• They have similar active ingredients\n"
    
    # Add generic advice
    comparison += "• Always consult your doctor before switching between medicines\n"
    comparison += "• Dosage and administration may differ\n"
    comparison += "• Side effects and contraindications may vary\n"
    
    return comparison

def get_comprehensive_medicine_info(medicine_name: str) -> dict:
    """Get comprehensive medicine information from APIs with local DB as fallback"""
    print(f"[DEBUG] [get_comprehensive_medicine_info] Getting comprehensive info for: {medicine_name}")
    
    medicine_info = {
        'name': medicine_name,
        'active_ingredients': [],
        'usage': '',
        'contraindications': '',
        'side_effects': '',
        'warnings': '',
        'dosage': '',
        'drug_interactions': '',
        'generic_name': '',
        'found_in': []
    }
    
    # PRIORITY 1: Try RxNav API
    try:
        success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
        if success and drug_info:
            print(f"[DEBUG] [get_comprehensive_medicine_info] Found data in RxNav")
            medicine_info['found_in'].append('RxNav')
            
            if drug_info.get('usage_text') and drug_info['usage_text'] != 'Usage information not available':
                medicine_info['usage'] = drug_info['usage_text']
            
            if drug_info.get('generic_name'):
                medicine_info['generic_name'] = drug_info['generic_name']
                medicine_info['active_ingredients'].append(drug_info['generic_name'])
            
            if drug_info.get('drug_name') and drug_info['drug_name'] not in medicine_info['active_ingredients']:
                medicine_info['active_ingredients'].append(drug_info['drug_name'])
    except Exception as e:
        print(f"[DEBUG] [get_comprehensive_medicine_info] RxNav error: {e}")
    
    # PRIORITY 2: Try to get more detailed info from openFDA if we have the generic name
    if medicine_info['generic_name'] or medicine_info['active_ingredients']:
        try:
            print(f"[DEBUG] [get_comprehensive_medicine_info] Trying openFDA")
            # Add openFDA lookup here for detailed information
            # This would typically query the FDA drug database for detailed labeling info
        except Exception as e:
            print(f"[DEBUG] [get_comprehensive_medicine_info] openFDA error: {e}")
    
    # PRIORITY 3: Try DailyMed for comprehensive labeling information
    try:
        print(f"[DEBUG] [get_comprehensive_medicine_info] Trying DailyMed")
        # Add DailyMed lookup here for comprehensive drug labeling
    except Exception as e:
        print(f"[DEBUG] [get_comprehensive_medicine_info] DailyMed error: {e}")
    
    # LAST RESORT: Fill gaps with local database
    print(f"[DEBUG] [get_comprehensive_medicine_info] Filling gaps with local database")
    
    # Get active ingredients from local DB if not found in APIs
    if not medicine_info['active_ingredients']:
        local_ingredients = get_active_ingredients(medicine_name)
        if local_ingredients:
            medicine_info['active_ingredients'] = local_ingredients
            medicine_info['found_in'].append('Local DB (ingredients)')
    
    # Get usage from local DB if not found in APIs
    if not medicine_info['usage']:
        local_usage = get_local_usage(medicine_name)
        if local_usage:
            medicine_info['usage'] = local_usage
            medicine_info['found_in'].append('Local DB (usage)')
    
    print(f"[DEBUG] [get_comprehensive_medicine_info] Final info: {medicine_info}")
    return medicine_info

def get_active_ingredients_api_first(medicine_name: str) -> list:
    """Get active ingredients with API-first approach, robust fallback, and user-friendly error handling."""
    print(f"[DEBUG] [get_active_ingredients_api_first] Getting ingredients for: {medicine_name}")
    errors = []
    # PRIORITY 1: Try RxNav API FIRST (external API priority)
    try:
        success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
        if success and drug_info:
            ingredients = []
            if drug_info.get('generic_name'):
                ingredients.append(drug_info['generic_name'])
                print(f"[DEBUG] [get_active_ingredients_api_first] Found generic name in RxNav: {drug_info['generic_name']}")
            if drug_info.get('drug_name'):
                drug_name = drug_info.get('full_rxnorm_name', drug_info['drug_name'])
                print(f"[DEBUG] [get_active_ingredients_api_first] Parsing drug name: {drug_name}")
                parsed_ingredient = extract_active_ingredient_from_drug_name(drug_name)
                if parsed_ingredient and parsed_ingredient not in ingredients and parsed_ingredient.lower() != medicine_name.lower():
                    ingredients.append(parsed_ingredient)
                    print(f"[DEBUG] [get_active_ingredients_api_first] Extracted ingredient from drug name: {parsed_ingredient}")
            if drug_info.get('rxcui'):
                rxcui = drug_info['rxcui']
                print(f"[DEBUG] [get_active_ingredients_api_first] Trying detailed lookup with RxCUI: {rxcui}")
                try:
                    detailed_ingredients = get_ingredients_from_rxcui(rxcui)
                    for ingredient in detailed_ingredients:
                        if ingredient not in ingredients and ingredient.lower() != medicine_name.lower():
                            ingredients.append(ingredient)
                            print(f"[DEBUG] [get_active_ingredients_api_first] Found additional ingredient: {ingredient}")
                except Exception as e:
                    print(f"[DEBUG] [get_active_ingredients_api_first] RxNav detailed lookup error: {e}")
            if drug_info.get('rxcui') and not ingredients:
                print(f"[DEBUG] [get_active_ingredients_api_first] Trying advanced RxNav parsing")
                try:
                    advanced_ingredients = get_ingredients_from_rxnav_advanced(drug_info['rxcui'], medicine_name)
                    if advanced_ingredients:
                        ingredients.extend(advanced_ingredients)
                except Exception as e:
                    print(f"[DEBUG] [get_active_ingredients_api_first] RxNav advanced parsing error: {e}")
            if ingredients:
                cleaned_ingredients = []
                for ingredient in ingredients:
                    cleaned = clean_ingredient_name(ingredient)
                    if cleaned and cleaned not in cleaned_ingredients and cleaned.lower() != medicine_name.lower():
                        cleaned_ingredients.append(cleaned)
                print(f"[DEBUG] [get_active_ingredients_api_first] Final cleaned ingredients from RxNav: {cleaned_ingredients}")
                if cleaned_ingredients:
                    return cleaned_ingredients
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_api_first] RxNav error: {e}")
        errors.append(f"RxNav: {e}")
    # PRIORITY 2: Try Egyptian Medicine API
    try:
        print(f"[DEBUG] [get_active_ingredients_api_first] Trying Egyptian Medicine API")
        ingredients = get_ingredients_from_egyptian_api(medicine_name)
        if ingredients:
            filtered_ingredients = [ing for ing in ingredients if ing.lower() != medicine_name.lower()]
            if filtered_ingredients:
                print(f"[DEBUG] [get_active_ingredients_api_first] Found in Egyptian API: {filtered_ingredients}")
                return filtered_ingredients
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_api_first] Egyptian API error: {e}")
        errors.append(f"Egyptian API: {e}")
    # PRIORITY 3: Try to extract generic name using trade name mapping (enhanced)
    try:
        print(f"[DEBUG] [get_active_ingredients_api_first] Trying generic name extraction")
        generic_name = extract_generic_name_from_trade_name(medicine_name)
        if generic_name and generic_name.lower() != medicine_name.lower():
            print(f"[DEBUG] [get_active_ingredients_api_first] Found generic name: {generic_name}")
            return [generic_name.title()]
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_api_first] Generic name extraction error: {e}")
        errors.append(f"Generic name mapping: {e}")
    # PRIORITY 4: Try OpenFDA API (if available)
    try:
        print(f"[DEBUG] [get_active_ingredients_api_first] Trying OpenFDA API")
        fda_ingredients = get_ingredients_from_openfda(medicine_name)
        if fda_ingredients:
            filtered_fda = [ing for ing in fda_ingredients if ing.lower() != medicine_name.lower()]
            if filtered_fda:
                print(f"[DEBUG] [get_active_ingredients_api_first] Found in OpenFDA: {filtered_fda}")
                return filtered_fda
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_api_first] OpenFDA error: {e}")
        errors.append(f"OpenFDA: {e}")
    # LAST RESORT: Local database (only when ALL APIs fail)
    try:
        print(f"[DEBUG] [get_active_ingredients_api_first] ALL APIs failed, falling back to local database")
        
        # Try the actual database first (your extracted data)
        db_ingredients = get_active_ingredients_from_database(medicine_name)
        if db_ingredients:
            print(f"[DEBUG] [get_active_ingredients_api_first] Found in database: {db_ingredients}")
            return db_ingredients
        
        # Fallback to hardcoded database
        local_ingredients = get_active_ingredients(medicine_name)
        if local_ingredients:
            print(f"[DEBUG] [get_active_ingredients_api_first] Found in hardcoded database: {local_ingredients}")
            return local_ingredients
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_api_first] Local DB error: {e}")
        errors.append(f"Local DB: {e}")
    print(f"[DEBUG] [get_active_ingredients_api_first] No ingredients found anywhere. Errors: {errors}")
    return []  # Let the caller return a user-friendly not found message

def get_ingredients_from_rxnav_advanced(rxcui: str, medicine_name: str) -> list:
    """Advanced parsing of RxNav data to extract active ingredients"""
    try:
        import requests
        
        # Try to get related concepts that might contain ingredient info
        url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/related.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            ingredients = []
            
            # Look for ingredient-related concepts
            if 'relatedGroup' in data:
                related_group = data['relatedGroup']
                if 'conceptGroup' in related_group:
                    for concept_group in related_group['conceptGroup']:
                        if concept_group.get('tty') in ['IN', 'PIN']:  # Ingredient types
                            if 'conceptProperties' in concept_group:
                                for concept in concept_group['conceptProperties']:
                                    name = concept.get('name', '')
                                    if name and name.lower() != medicine_name.lower():
                                        ingredients.append(name.title())
                                        print(f"[DEBUG] [get_ingredients_from_rxnav_advanced] Found ingredient concept: {name}")
            
            return ingredients
            
    except Exception as e:
        print(f"[DEBUG] [get_ingredients_from_rxnav_advanced] Error: {e}")
    
    return []

def get_ingredients_from_openfda(medicine_name: str) -> list:
    """Get active ingredients from OpenFDA API"""
    try:
        import requests
        
        # Search OpenFDA drug database
        url = "https://api.fda.gov/drug/label.json"
        params = {
            'search': f'openfda.brand_name:"{medicine_name}"',
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'results' in data and data['results']:
                result = data['results'][0]
                
                # Try to extract from active_ingredient field
                if 'active_ingredient' in result:
                    active_ingredients = result['active_ingredient']
                    if isinstance(active_ingredients, list) and active_ingredients:
                        # Parse the active ingredient text
                        ingredient_text = active_ingredients[0]
                        # Extract ingredient name (usually before dosage info)
                        import re
                        match = re.match(r'^([A-Za-z\s]+)', ingredient_text)
                        if match:
                            ingredient = match.group(1).strip().title()
                            print(f"[DEBUG] [get_ingredients_from_openfda] Found active ingredient: {ingredient}")
                            return [ingredient]
                
                # Try to extract from openfda.generic_name
                if 'openfda' in result and 'generic_name' in result['openfda']:
                    generic_names = result['openfda']['generic_name']
                    if isinstance(generic_names, list) and generic_names:
                        ingredient = generic_names[0].title()
                        print(f"[DEBUG] [get_ingredients_from_openfda] Found generic name: {ingredient}")
                        return [ingredient]
                        
    except Exception as e:
        print(f"[DEBUG] [get_ingredients_from_openfda] Error: {e}")
    
    return []

def extract_active_ingredient_from_drug_name(drug_name: str) -> str:
    """
    Extract active ingredient from structured drug name returned by RxNav API.
    Example: "cephalexin 500 MG Oral Capsule [Keflex]" → "Cephalexin"
    Example: "albuterol 0.09 MG/ACTUAT Metered Dose Inhaler [Ventolin]" → "Albuterol"
    Example: "{6 (azithromycin 250 MG Oral Tablet [Zithromax]) } Pack [Z-PAK]" → "Azithromycin"
    """
    if not drug_name:
        return ""
    
    print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Processing: '{drug_name}'")
    
    # FIXED: Handle complex pack formats first
    # Extract from patterns like "{6 (azithromycin 250 MG Oral Tablet [Zithromax]) } Pack"
    pack_pattern = r'\{\d+\s*\(\s*([a-zA-Z]+)\s+\d+.*?\)\s*\}'
    pack_match = re.search(pack_pattern, drug_name)
    if pack_match:
        ingredient = pack_match.group(1).strip()
        print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Extracted from pack format: '{ingredient}'")
        return ingredient.title()
    
    # Remove brand name in brackets [Brand]
    drug_name = re.sub(r'\[.*?\]', '', drug_name).strip()
    print(f"[DEBUG] [extract_active_ingredient_from_drug_name] After removing brand: '{drug_name}'")
    
    # Remove common prefixes that aren't ingredients
    prefixes_to_remove = [
        r'^NDA\d+\s+',  # Remove "NDA020983 60 ACTUAT"
        r'^\d+\s+ACTUAT\s+',  # Remove "60 ACTUAT"
        r'^\d+\s+',  # Remove leading numbers
    ]
    
    for prefix in prefixes_to_remove:
        drug_name = re.sub(prefix, '', drug_name).strip()
        print(f"[DEBUG] [extract_active_ingredient_from_drug_name] After removing prefix: '{drug_name}'")
    
    # Split by dosage patterns to get the active ingredient part
    # Common patterns: "0.05 MG", "50 MCG", "20 mg", etc.
    dosage_patterns = [
        r'\d+\.?\d*\s*(MG|MCG|mg|mcg|g|ml|IU|units?|%)',
        r'\d+\.?\d*\s*MG/ACTUAT',
        r'\d+\.?\d*\s*MCG/ACTUAT',
    ]
    
    for pattern in dosage_patterns:
        match = re.search(pattern, drug_name, re.IGNORECASE)
        if match:
            # Extract everything before the dosage
            ingredient_part = drug_name[:match.start()].strip()
            if ingredient_part:
                print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Found ingredient before dosage: '{ingredient_part}'")
                return ingredient_part.title()
    
    # If no dosage pattern found, try to extract first part before common keywords
    form_keywords = ['tablet', 'capsule', 'injection', 'spray', 'cream', 'gel', 'solution', 'suspension', 'inhaler', 'metered', 'dose', 'oral']
    for keyword in form_keywords:
        if keyword.lower() in drug_name.lower():
            parts = drug_name.lower().split(keyword.lower())
            if parts[0].strip():
                ingredient = parts[0].strip().title()
                print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Found ingredient before '{keyword}': '{ingredient}'")
                return ingredient
    
    # If all else fails, return the first few words (likely the ingredient)
    words = drug_name.split()
    if len(words) >= 2:
        ingredient = ' '.join(words[:2]).title()
        print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Using first 2 words: '{ingredient}'")
        return ingredient
    elif len(words) == 1:
        ingredient = words[0].title()
        print(f"[DEBUG] [extract_active_ingredient_from_drug_name] Using single word: '{ingredient}'")
        return ingredient
    
    print(f"[DEBUG] [extract_active_ingredient_from_drug_name] No ingredient found")
    return ""

def get_ingredients_from_rxcui(rxcui: str) -> list:
    """Get detailed ingredient information using RxCUI"""
    try:
        # This could be enhanced to make additional API calls to get more detailed info
        # For now, return empty list but this is where you could add more API calls
        return []
    except Exception as e:
        print(f"[DEBUG] [get_ingredients_from_rxcui] Error: {e}")
        return []

def get_ingredients_from_egyptian_api(medicine_name: str) -> list:
    """Extract active ingredients from Egyptian Medicine API response"""
    try:
        success, products, error = medicine_api.search_and_get_details(medicine_name)
        if success and products:
            ingredients = []
            for product in products:
                # Check if product has components field
                if product.get('components'):
                    components = product['components']
                    if isinstance(components, list):
                        ingredients.extend(components)
                    elif isinstance(components, str):
                        ingredients.append(components)
                
                # Try to extract from description or other fields
                description = product.get('desc', '') or product.get('description', '') or product.get('msg', '')
                if description:
                    print(f"[DEBUG] [get_ingredients_from_egyptian_api] Processing description: '{description}'")
                    # Try to parse ingredient from Arabic text
                    ingredient = extract_ingredient_from_arabic_text(description)
                    if ingredient and ingredient not in ingredients:
                        ingredients.append(ingredient)
                        print(f"[DEBUG] [get_ingredients_from_egyptian_api] Extracted ingredient: '{ingredient}'")
            
            # Remove duplicates and filter out invalid ingredients
            unique_ingredients = []
            for ingredient in ingredients:
                if ingredient and ingredient not in unique_ingredients and ingredient.lower() != medicine_name.lower():
                    unique_ingredients.append(ingredient)
            
            return unique_ingredients
        
        return []
    except Exception as e:
        print(f"[DEBUG] [get_ingredients_from_egyptian_api] Error: {e}")
        return []

def extract_ingredient_from_arabic_text(text: str) -> str:
    """Extract active ingredient from Arabic description text"""
    try:
        print(f"[DEBUG] [extract_ingredient_from_arabic_text] Processing: '{text}'")
        
        # Enhanced Arabic-to-English mappings based on actual API responses
        arabic_mappings = {
            'سيفاليكسين': 'Cephalexin',
            'سالبوتامول': 'Albuterol', 
            'أموكسيسيلين': 'Amoxicillin',
            'فلوتيكاسون': 'Fluticasone propionate',
            'لوراتادين': 'Loratadine',
            'سيتريزين': 'Cetirizine',
            'ايبوبروفين': 'Ibuprofen',
            'ديكلوفيناك': 'Diclofenac',
            'باراسيتامول': 'Paracetamol',
            'أسيتامينوفين': 'Acetaminophen',
            'أتورفاستاتين': 'Atorvastatin',
            'سيمفاستاتين': 'Simvastatin',
            'أوميبرازول': 'Omeprazole',
            'رانيتيدين': 'Ranitidine',
            'مونتيلوكاست': 'Montelukast',
            'ليفوثيروكسين': 'Levothyroxine',
            'ميتفورمين': 'Metformin',
            'أملوديبين': 'Amlodipine',
            'ليسينوبريل': 'Lisinopril',
            'هيدروكلوروثيازيد': 'Hydrochlorothiazide'
        }
        
        # Check for direct matches in the text
        for arabic_name, english_name in arabic_mappings.items():
            if arabic_name in text:
                print(f"[DEBUG] [extract_ingredient_from_arabic_text] Found ingredient: '{arabic_name}' → '{english_name}'")
                return english_name
        
        # Try to extract ingredient after common Arabic phrases
        # "تحتوي على" means "contains"
        # "يحتوي على" means "contains" (masculine form)
        contains_patterns = [
            r'تحتوي على\s+([^\s،.]+)',
            r'يحتوي على\s+([^\s،.]+)',
            r'تحتوى على\s+([^\s،.]+)',
            r'يحتوى على\s+([^\s،.]+)',
        ]
        
        for pattern in contains_patterns:
            match = re.search(pattern, text)
            if match:
                potential_ingredient = match.group(1).strip()
                print(f"[DEBUG] [extract_ingredient_from_arabic_text] Found potential ingredient after 'contains': '{potential_ingredient}'")
                # Check if this matches any of our known mappings
                for arabic_name, english_name in arabic_mappings.items():
                    if arabic_name in potential_ingredient:
                        print(f"[DEBUG] [extract_ingredient_from_arabic_text] Matched to: '{english_name}'")
                        return english_name
        
        print(f"[DEBUG] [extract_ingredient_from_arabic_text] No ingredient found")
        return ""
    except Exception as e:
        print(f"[DEBUG] [extract_ingredient_from_arabic_text] Error: {e}")
        return ""

def clean_ingredient_name(ingredient: str) -> str:
    """Clean and standardize ingredient name"""
    if not ingredient:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', ingredient.strip())
    
    # Capitalize properly
    cleaned = cleaned.title()
    
    # Handle special cases
    if cleaned.lower() == 'acetaminophen':
        return 'Acetaminophen'
    elif cleaned.lower() == 'paracetamol':
        return 'Paracetamol'
    elif 'fluticasone' in cleaned.lower():
        return 'Fluticasone propionate'
    
    return cleaned

def get_active_ingredients_from_database(medicine_name: str) -> list:
    """Get active ingredients for a medicine from the actual database tables."""
    try:
        # Import here to avoid circular imports
        from src.models.medicine import db
        
        # Clean the medicine name for search
        clean_name = medicine_name.lower().strip()
        
        # Query the database tables that contain our extracted data
        query = """
        SELECT DISTINCT active_ingredients, trade_name, generic_name 
        FROM medicine_dailymed_complete_all 
        WHERE LOWER(trade_name) LIKE ? 
           OR LOWER(generic_name) LIKE ? 
           OR LOWER(trade_name) LIKE ? 
           OR LOWER(generic_name) LIKE ?
        LIMIT 10
        """
        
        # Create search patterns
        exact_match = f"%{clean_name}%"
        partial_match = f"%{clean_name}%"
        
        # Execute query
        result = db.session.execute(query, (exact_match, exact_match, partial_match, partial_match))
        rows = result.fetchall()
        
        ingredients = []
        for row in rows:
            if row[0] and row[0] != 'None':  # active_ingredients
                ingredients.append(row[0])
            if row[2] and row[2] != 'None' and row[2] not in ingredients:  # generic_name
                ingredients.append(row[2])
        
        # Remove duplicates and clean
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient and ingredient.strip() and ingredient.strip() != 'None':
                clean_ingredient = ingredient.strip()
                if clean_ingredient not in unique_ingredients:
                    unique_ingredients.append(clean_ingredient)
        
        print(f"[DEBUG] [get_active_ingredients_from_database] Found {len(unique_ingredients)} ingredients for '{medicine_name}': {unique_ingredients}")
        return unique_ingredients
        
    except Exception as e:
        print(f"[DEBUG] [get_active_ingredients_from_database] Database query error: {e}")
        return []

def get_medicine_usage_from_database(medicine_name: str) -> str:
    """Get usage information for a medicine from the database."""
    try:
        from src.models.medicine import db
        
        clean_name = medicine_name.lower().strip()
        
        # Query for usage information
        query = """
        SELECT DISTINCT active_ingredients, trade_name, generic_name 
        FROM medicine_dailymed_complete_all 
        WHERE LOWER(trade_name) LIKE ? 
           OR LOWER(generic_name) LIKE ?
        LIMIT 5
        """
        
        result = db.session.execute(query, (f"%{clean_name}%", f"%{clean_name}%"))
        rows = result.fetchall()
        
        if rows:
            # Build usage information from available data
            usage_info = []
            for row in rows:
                if row[0] and row[0] != 'None':  # active_ingredients
                    usage_info.append(f"Active ingredient: {row[0]}")
                if row[2] and row[2] != 'None':  # generic_name
                    usage_info.append(f"Generic name: {row[2]}")
            
            if usage_info:
                return ". ".join(usage_info)
            
                    # If no detailed info but medicine exists in database, provide basic confirmation
        if rows and rows[0][1]:  # trade_name exists
            # Try to provide basic info for known medicines
            basic_info = {
                'renese': 'RENESE is a diuretic medication used to treat high blood pressure and fluid retention.',
                'mykrox': 'Mykrox is a diuretic medication used to treat high blood pressure and edema.',
                'tolinase': 'Tolinase is an oral diabetes medication used to control blood sugar levels.',
                'halotestin': 'Halotestin is an anabolic steroid medication.',
                'dantrium': 'Dantrium is a muscle relaxant used to treat muscle spasticity.',
                'lithane': 'LITHANE is a mood stabilizer used to treat bipolar disorder.'
            }
            
            medicine_lower = medicine_name.lower()
            if medicine_lower in basic_info:
                return basic_info[medicine_lower]
            else:
                return f"{medicine_name.title()} is found in our medicine database. For detailed usage information, please consult your doctor or pharmacist."
        
        return ""
        
    except Exception as e:
        print(f"[DEBUG] [get_medicine_usage_from_database] Database query error: {e}")
        return ""

# Add other necessary routes and functions here... 