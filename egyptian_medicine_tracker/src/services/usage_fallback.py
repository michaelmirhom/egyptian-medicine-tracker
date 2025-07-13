#!/usr/bin/env python3
"""
Usage Fallback Service
Implements a chain of API calls to get medicine usage information:
1. Local database (most reliable)
2. Local DailyMed database (offline fallback)
3. RxNav (primary)
4. openFDA (fallback)
5. DailyMed (final fallback)
"""

import requests
import json
import time
import re
from typing import Optional, Dict, Any
from src.services.rxnav_api import rxnav_api
from .name_resolver import arabic_to_english, is_arabic_text
from src.models.dailymed import DailyMedLabel

# Local database of accurate medicine usage information
LOCAL_USAGE_DATABASE = {
    # Diabetes medications
    "ozempic": "Ozempic (semaglutide) is used to improve blood sugar control in adults with type 2 diabetes mellitus. It is also used for chronic weight management in certain adults, in combination with diet and exercise.",
    "semaglutide": "Semaglutide is used to improve blood sugar control in adults with type 2 diabetes mellitus. It is also used for chronic weight management in certain adults, in combination with diet and exercise.",
    "humalog": "Humalog (insulin lispro) is a rapid-acting insulin used to control high blood sugar in people with diabetes. It works by helping glucose get into cells to be used for energy.",
    "insulin lispro": "Insulin lispro is a rapid-acting insulin used to control high blood sugar in people with diabetes. It works by helping glucose get into cells to be used for energy.",
    "lantus": "Lantus (insulin glargine) is a long-acting insulin used to control high blood sugar in people with diabetes. It provides a steady level of insulin throughout the day.",
    "insulin glargine": "Insulin glargine is a long-acting insulin used to control high blood sugar in people with diabetes. It provides a steady level of insulin throughout the day.",
    "metformin": "Metformin is used to treat type 2 diabetes. It works by improving the body's response to insulin and reducing the amount of glucose produced by the liver.",
    
    # Antidepressants
    "prozac": "Prozac (fluoxetine) is used to treat depression, obsessive-compulsive disorder, panic disorder, and bulimia nervosa. It belongs to a class of medications called selective serotonin reuptake inhibitors (SSRIs).",
    "fluoxetine": "Fluoxetine is used to treat depression, obsessive-compulsive disorder, panic disorder, and bulimia nervosa. It belongs to a class of medications called selective serotonin reuptake inhibitors (SSRIs).",
    "zoloft": "Zoloft (sertraline) is used to treat depression, obsessive-compulsive disorder, panic disorder, post-traumatic stress disorder, and social anxiety disorder. It belongs to a class of medications called selective serotonin reuptake inhibitors (SSRIs).",
    "sertraline": "Sertraline is used to treat depression, obsessive-compulsive disorder, panic disorder, post-traumatic stress disorder, and social anxiety disorder. It belongs to a class of medications called selective serotonin reuptake inhibitors (SSRIs).",
    
    # Pain relievers
    "panadol": "Panadol (paracetamol/acetaminophen) is used to reduce fever and treat pain such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "paracetamol": "Paracetamol (acetaminophen) is used to reduce fever and treat pain such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "acetaminophen": "Acetaminophen (paracetamol) is used to reduce fever and treat pain such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "ibuprofen": "Ibuprofen is used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "aspirin": "Aspirin is used to reduce fever and relieve mild to moderate pain from conditions such as muscle aches, toothaches, common cold, and headaches. It is also used to prevent heart attacks and strokes.",
    
    # Antihistamines
    "claritine": "Claritine (loratadine) is used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. It is an antihistamine that works by blocking histamine, a substance in the body that causes allergic symptoms.",
    "loratadine": "Loratadine is used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. It is an antihistamine that works by blocking histamine, a substance in the body that causes allergic symptoms.",
    "allegra": "Allegra (fexofenadine) is used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. It is an antihistamine that works by blocking histamine, a substance in the body that causes allergic symptoms.",
    "fexofenadine": "Fexofenadine is used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. It is an antihistamine that works by blocking histamine, a substance in the body that causes allergic symptoms.",
    
    # Blood thinners
    "rivo": "Rivo (rivaroxaban) is used to prevent blood clots and stroke in people with atrial fibrillation. It is also used to treat and prevent deep vein thrombosis and pulmonary embolism.",
    "rivaroxaban": "Rivaroxaban is used to prevent blood clots and stroke in people with atrial fibrillation. It is also used to treat and prevent deep vein thrombosis and pulmonary embolism.",
    "xarelto": "Xarelto (rivaroxaban) is used to prevent blood clots and stroke in people with atrial fibrillation. It is also used to treat and prevent deep vein thrombosis and pulmonary embolism.",
    
    # Cholesterol medications
    "lipitor": "Lipitor (atorvastatin) is used to lower cholesterol and triglycerides in the blood. It is also used to prevent heart disease and stroke in certain people.",
    "atorvastatin": "Atorvastatin is used to lower cholesterol and triglycerides in the blood. It is also used to prevent heart disease and stroke in certain people.",
    
    # Anti-inflammatory
    "voltaren": "Voltaren (diclofenac) is used to reduce pain, swelling, and joint stiffness caused by arthritis. It is a nonsteroidal anti-inflammatory drug (NSAID) that works by blocking the production of certain natural substances that cause inflammation.",
    "diclofenac": "Diclofenac is used to reduce pain, swelling, and joint stiffness caused by arthritis. It is a nonsteroidal anti-inflammatory drug (NSAID) that works by blocking the production of certain natural substances that cause inflammation.",
    
    # Antibiotics
    "augmentin": "Augmentin (amoxicillin/clavulanate) is used to treat bacterial infections such as sinusitis, pneumonia, ear infections, bronchitis, urinary tract infections, and skin infections.",
    "amoxicillin": "Amoxicillin is used to treat bacterial infections such as sinusitis, pneumonia, ear infections, bronchitis, urinary tract infections, and skin infections.",
    "azithromycin": "Azithromycin is used to treat bacterial infections such as respiratory infections, skin infections, ear infections, and sexually transmitted diseases.",
}

def is_wrong_usage_info(usage_text: str) -> bool:
    """
    Check if the usage information is clearly wrong or irrelevant.
    
    Args:
        usage_text (str): Usage information to validate
        
    Returns:
        bool: True if the information is wrong/irrelevant, False if it seems correct
    """
    if not usage_text:
        return True
    
    usage_lower = usage_text.lower()
    
    # Check for generic/placeholder text that indicates no real information
    wrong_indicators = [
        "condition listed above or as directed by the physician",
        "relief of naturally occurring simple nervous tension",
        "use for relief of",
        "indications condition listed above",
        "as directed by the physician",
        "see package insert",
        "refer to package insert",
        "consult your doctor",
        "ask your doctor",
        "talk to your doctor",
        "follow your doctor's instructions",
        "use as prescribed",
        "use as directed",
        "use according to",
        "use under medical supervision",
        "use under doctor's supervision",
        "use under physician's supervision",
        "use under healthcare provider's supervision",
        "use under medical advice",
        "use under doctor's advice",
        "use under physician's advice",
        "use under healthcare provider's advice",
        "use under medical guidance",
        "use under doctor's guidance",
        "use under physician's guidance",
        "use under healthcare provider's guidance",
        "use under medical direction",
        "use under doctor's direction",
        "use under physician's direction",
        "use under healthcare provider's direction",
        "use under medical care",
        "use under doctor's care",
        "use under physician's care",
        "use under healthcare provider's care",
        "use under medical treatment",
        "use under doctor's treatment",
        "use under physician's treatment",
        "use under healthcare provider's treatment",
        "use under medical management",
        "use under doctor's management",
        "use under physician's management",
        "use under healthcare provider's management",
        "use under medical supervision",
        "use under doctor's supervision",
        "use under physician's supervision",
        "use under healthcare provider's supervision",
    ]
    
    for indicator in wrong_indicators:
        if indicator in usage_lower:
            print(f"[DEBUG] [is_wrong_usage_info] Detected wrong indicator: '{indicator}' in usage text")
            return True
    
    # Check if the text is too short to be meaningful
    if len(usage_text.strip()) < 50:
        print(f"[DEBUG] [is_wrong_usage_info] Usage text too short: {len(usage_text.strip())} characters")
        return True
    
    # Check if the text contains mostly generic words
    generic_words = ['use', 'for', 'relief', 'of', 'naturally', 'occurring', 'simple', 'nervous', 'tension', 'condition', 'listed', 'above', 'directed', 'physician', 'doctor', 'medical', 'supervision', 'advice', 'guidance', 'care', 'treatment', 'management']
    words = usage_lower.split()
    generic_word_count = sum(1 for word in words if word in generic_words)
    if len(words) > 0 and generic_word_count / len(words) > 0.7:
        print(f"[DEBUG] [is_wrong_usage_info] Too many generic words: {generic_word_count}/{len(words)}")
        return True
    
    return False

def get_local_usage(medicine_name: str) -> Optional[str]:
    """
    Get usage information from local database.
    
    Args:
        medicine_name (str): Medicine name (trade name or generic name)
        
    Returns:
        Optional[str]: Usage information if found, None otherwise
    """
    clean_name = medicine_name.lower().strip()
    
    # Check exact match first
    if clean_name in LOCAL_USAGE_DATABASE:
        print(f"[DEBUG] [get_local_usage] Found exact match for '{clean_name}'")
        return LOCAL_USAGE_DATABASE[clean_name]
    
    # Check partial matches
    for key, value in LOCAL_USAGE_DATABASE.items():
        if clean_name in key or key in clean_name:
            print(f"[DEBUG] [get_local_usage] Found partial match: '{clean_name}' matches '{key}'")
            return value
    
    print(f"[DEBUG] [get_local_usage] No match found for '{clean_name}'")
    return None

def local_dailymed_usage(name: str) -> Optional[str]:
    """
    Get usage information from local DailyMed database.
    
    Args:
        name (str): Medicine name (trade name or generic name)
        
    Returns:
        Optional[str]: Usage information if found, None otherwise
    """
    try:
        en = arabic_to_english(name) or name
        row = DailyMedLabel.query.filter(
            (DailyMedLabel.generic == en.lower()) |
            (DailyMedLabel.brand.ilike(f"%{en}%"))
        ).first()
        
        if row and row.indications:
            print(f"[DEBUG] [local_dailymed_usage] Found in local DailyMed: {row.indications[:100]}...")
            return row.indications
        
        print(f"[DEBUG] [local_dailymed_usage] No match found for '{name}'")
        return None
        
    except Exception as e:
        print(f"[DEBUG] [local_dailymed_usage] Exception: {e}")
        return None

def openfda_usage(generic_name: str) -> Optional[str]:
    """
    Get usage information from openFDA API.
    
    Args:
        generic_name (str): Generic name of the medicine
        
    Returns:
        Optional[str]: Usage information or None if not found
    """
    try:
        print(f"[DEBUG] [openfda_usage] Searching for: '{generic_name}'")
        
        # Clean the generic name
        clean_name = generic_name.lower().strip()
        
        # Make API call to openFDA
        url = "https://api.fda.gov/drug/label.json"
        params = {
            'search': f'openfda.generic_name:{clean_name}',
            'limit': 1
        }
        
        print(f"[DEBUG] [openfda_usage] Requesting: {url} with params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                
                # Try to get indications_and_usage
                usage = result.get('indications_and_usage')
                if usage and len(usage) > 0:
                    usage_text = usage[0]
                    print(f"[DEBUG] [openfda_usage] Found usage: {usage_text[:100]}...")
                    
                    # Validate the usage information
                    if is_wrong_usage_info(usage_text):
                        print(f"[DEBUG] [openfda_usage] Rejected wrong usage info from openFDA")
                        return None
                    
                    return usage_text
                
                # Fallback to other fields
                for field in ['indications', 'clinical_pharmacology', 'description']:
                    if field in result and result[field]:
                        field_data = result[field]
                        if isinstance(field_data, list) and len(field_data) > 0:
                            field_text = field_data[0]
                            print(f"[DEBUG] [openfda_usage] Found {field}: {field_text[:100]}...")
                            
                            # Validate the usage information
                            if is_wrong_usage_info(field_text):
                                print(f"[DEBUG] [openfda_usage] Rejected wrong usage info from {field}")
                                continue
                            
                            return field_text
                        elif isinstance(field_data, str):
                            print(f"[DEBUG] [openfda_usage] Found {field}: {field_data[:100]}...")
                            
                            # Validate the usage information
                            if is_wrong_usage_info(field_data):
                                print(f"[DEBUG] [openfda_usage] Rejected wrong usage info from {field}")
                                continue
                            
                            return field_data
            
            print(f"[DEBUG] [openfda_usage] No results found for '{generic_name}'")
        else:
            print(f"[DEBUG] [openfda_usage] API error: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] [openfda_usage] Exception: {e}")
    
    return None

def dailymed_usage(generic_name: str) -> Optional[str]:
    """
    Get usage information from DailyMed API (two-step process).
    
    Args:
        generic_name (str): Generic name of the medicine
        
    Returns:
        Optional[str]: Usage information or None if not found
    """
    try:
        print(f"[DEBUG] [dailymed_usage] Searching for: '{generic_name}'")
        
        # Clean the generic name
        clean_name = generic_name.lower().strip()
        
        # Step 1: Get drug names to find setid
        url1 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json"
        params1 = {'drug_name': clean_name}
        
        print(f"[DEBUG] [dailymed_usage] Step 1 - Requesting: {url1} with params: {params1}")
        
        response1 = requests.get(url1, params=params1, timeout=10)
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            if data1.get('data') and len(data1['data']) > 0:
                setid = data1['data'][0].get('setid')
                
                if setid:
                    print(f"[DEBUG] [dailymed_usage] Found setid: {setid}")
                    
                    # Step 2: Get detailed information using setid
                    url2 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.json"
                    
                    print(f"[DEBUG] [dailymed_usage] Step 2 - Requesting: {url2}")
                    
                    response2 = requests.get(url2, timeout=10)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        
                        if data2.get('data') and len(data2['data']) > 0:
                            result = data2['data'][0]
                            
                            # Try to get indications_and_usage
                            usage = result.get('indications_and_usage')
                            if usage:
                                print(f"[DEBUG] [dailymed_usage] Found usage: {usage[:100]}...")
                                
                                # Validate the usage information
                                if is_wrong_usage_info(usage):
                                    print(f"[DEBUG] [dailymed_usage] Rejected wrong usage info from DailyMed")
                                    return None
                                
                                return usage
                            
                            # Fallback to other fields
                            for field in ['clinical_pharmacology', 'description', 'drug_interactions']:
                                if field in result and result[field]:
                                    field_text = result[field]
                                    print(f"[DEBUG] [dailymed_usage] Found {field}: {field_text[:100]}...")
                                    
                                    # Validate the usage information
                                    if is_wrong_usage_info(field_text):
                                        print(f"[DEBUG] [dailymed_usage] Rejected wrong usage info from {field}")
                                        continue
                                    
                                    return field_text
                        else:
                            print(f"[DEBUG] [dailymed_usage] No detailed data found for setid: {setid}")
                    else:
                        print(f"[DEBUG] [dailymed_usage] Step 2 API error: {response2.status_code}")
                else:
                    print(f"[DEBUG] [dailymed_usage] No setid found in response")
            else:
                print(f"[DEBUG] [dailymed_usage] No drug names found for '{generic_name}'")
        else:
            print(f"[DEBUG] [dailymed_usage] Step 1 API error: {response1.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] [dailymed_usage] Exception: {e}")
    
    return None

def get_usage_generic(trade_name: str, generic_name: str = "") -> str:
    print(f"[DEBUG] [get_usage_generic] Looking up usage for trade_name='{trade_name}', generic_name='{generic_name}'")
    
    # Resolve Arabic names to English
    en_name = trade_name
    if is_arabic_text(trade_name):
        print(f"[DEBUG] [get_usage_generic] Arabic text detected: '{trade_name}'")
        resolved_name = arabic_to_english(trade_name)
        if resolved_name:
            en_name = resolved_name
            print(f"[DEBUG] [get_usage_generic] Resolved to English: '{trade_name}' -> '{en_name}'")
        else:
            print(f"[DEBUG] [get_usage_generic] Could not resolve Arabic name: '{trade_name}'")

    # Step 0: Try local database first (most reliable)
    local_usage = get_local_usage(en_name)
    if local_usage:
        print(f"[DEBUG] [get_usage_generic] Found in local database: {local_usage[:100]}...")
        return local_usage
    
    # Also try with generic name if provided
    if generic_name:
        local_usage = get_local_usage(generic_name)
        if local_usage:
            print(f"[DEBUG] [get_usage_generic] Found generic name in local database: {local_usage[:100]}...")
            return local_usage

    # Step 1: Try local DailyMed database (offline fallback)
    local_dm_usage = local_dailymed_usage(en_name)
    if local_dm_usage:
        print(f"[DEBUG] [get_usage_generic] Found in local DailyMed database: {local_dm_usage[:100]}...")
        return local_dm_usage
    
    # Also try with generic name if provided
    if generic_name:
        local_dm_usage = local_dailymed_usage(generic_name)
        if local_dm_usage:
            print(f"[DEBUG] [get_usage_generic] Found generic name in local DailyMed database: {local_dm_usage[:100]}...")
            return local_dm_usage

    # Special case: Prozac and its variants should always use fluoxetine and skip RxNav
    prozac_variants = {"prozac", "protasi", "groza", "promax", "grozax"}
    if en_name.lower() in prozac_variants or (generic_name and generic_name.lower() == "fluoxetine"):
        print(f"[DEBUG] [get_usage_generic] Special case: Skipping RxNav for Prozac/variants, using openFDA/DailyMed for 'fluoxetine'")
        usage_text = openfda_usage("fluoxetine")
        if usage_text:
            print(f"[DEBUG] [get_usage_generic] openFDA success: {usage_text[:100]}...")
            return usage_text
        usage_text = dailymed_usage("fluoxetine")
        if usage_text:
            print(f"[DEBUG] [get_usage_generic] DailyMed success: {usage_text[:100]}...")
            return usage_text
        print(f"[DEBUG] [get_usage_generic] All APIs failed for fluoxetine, returning empty string")
        return ""

    # Special case: Ozempic and its variants should always use semaglutide and skip RxNav
    ozempic_variants = {"ozempic", "اوزيمبيك", "اوزيمبك"}
    if en_name.lower() in ozempic_variants or (generic_name and generic_name.lower() == "semaglutide"):
        print(f"[DEBUG] [get_usage_generic] Special case: Skipping RxNav for Ozempic/variants, using openFDA/DailyMed for 'semaglutide'")
        usage_text = openfda_usage("semaglutide")
        if usage_text:
            print(f"[DEBUG] [get_usage_generic] openFDA success: {usage_text[:100]}...")
            return usage_text
        usage_text = dailymed_usage("semaglutide")
        if usage_text:
            print(f"[DEBUG] [get_usage_generic] DailyMed success: {usage_text[:100]}...")
            return usage_text
        # Local override if all APIs fail
        local_ozempic_usage = (
            "Ozempic (semaglutide) is used to improve blood sugar control in adults with type 2 diabetes mellitus. "
            "It is also used for chronic weight management in certain adults, in combination with diet and exercise."
        )
        print(f"[DEBUG] [get_usage_generic] All APIs failed for semaglutide, returning local override usage.")
        return local_ozempic_usage

    # Step 2: Try RxNav API
    try:
        print(f"[DEBUG] [get_usage_generic] Step 2: Trying RxNav API")
        success, drug_info, error = rxnav_api.get_drug_info(en_name)
        
        if success and drug_info and drug_info.get('usage_text'):
            usage_text = drug_info['usage_text']
            if usage_text and usage_text != 'Usage information not available':
                # Validate the usage information
                if is_wrong_usage_info(usage_text):
                    print(f"[DEBUG] [get_usage_generic] Rejected wrong usage info from RxNav")
                else:
                    print(f"[DEBUG] [get_usage_generic] RxNav success: {usage_text[:100]}...")
                    return usage_text
    except Exception as e:
        print(f"[DEBUG] [get_usage_generic] RxNav exception: {e}")
    
    # Step 3: Try openFDA API (if we have a generic name)
    if generic_name:
        try:
            print(f"[DEBUG] [get_usage_generic] Step 3: Trying openFDA API")
            usage_text = openfda_usage(generic_name)
            if usage_text:
                print(f"[DEBUG] [get_usage_generic] openFDA success: {usage_text[:100]}...")
                return usage_text
        except Exception as e:
            print(f"[DEBUG] [get_usage_generic] openFDA exception: {e}")
    
    # Step 4: Try DailyMed API (if we have a generic name)
    if generic_name:
        try:
            print(f"[DEBUG] [get_usage_generic] Step 4: Trying DailyMed API")
            usage_text = dailymed_usage(generic_name)
            if usage_text:
                print(f"[DEBUG] [get_usage_generic] DailyMed success: {usage_text[:100]}...")
                return usage_text
        except Exception as e:
            print(f"[DEBUG] [get_usage_generic] DailyMed exception: {e}")
    
    # Step 5: Try openFDA with trade name (if not already tried)
    if not generic_name:
        try:
            print(f"[DEBUG] [get_usage_generic] Step 5: Trying openFDA with trade name")
            usage_text = openfda_usage(en_name)
            if usage_text:
                print(f"[DEBUG] [get_usage_generic] openFDA success: {usage_text[:100]}...")
                return usage_text
        except Exception as e:
            print(f"[DEBUG] [get_usage_generic] openFDA exception: {e}")
    
    # Step 6: Try DailyMed with trade name (if not already tried)
    if not generic_name:
        try:
            print(f"[DEBUG] [get_usage_generic] Step 6: Trying DailyMed with trade name")
            usage_text = dailymed_usage(en_name)
            if usage_text:
                print(f"[DEBUG] [get_usage_generic] DailyMed success: {usage_text[:100]}...")
                return usage_text
        except Exception as e:
            print(f"[DEBUG] [get_usage_generic] DailyMed exception: {e}")
    
    print(f"[DEBUG] [get_usage_generic] All APIs failed, returning empty string")
    return ""

def extract_generic_name_from_trade_name(trade_name: str) -> str:
    """
    Extract generic name from trade name using common patterns.
    This is a simple heuristic and may not work for all cases.
    
    Args:
        trade_name (str): Trade name of the medicine
        
    Returns:
        str: Extracted generic name or empty string
    """
    # Common medicine mappings
    medicine_mappings = {
        # Pain relievers
        'panadol': 'paracetamol',
        'tylenol': 'paracetamol',
        'acetaminophen': 'paracetamol',
        'advil': 'ibuprofen',
        'motrin': 'ibuprofen',
        'aspirin': 'acetylsalicylic acid',
        
        # Cholesterol medications
        'lipitor': 'atorvastatin',
        'zocor': 'simvastatin',
        'crestor': 'rosuvastatin',
        
        # Blood thinners
        'plavix': 'clopidogrel',
        
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
        
        # Antidepressants
        'prozac': 'fluoxetine',
        'protasi': 'fluoxetine',
        'groza': 'fluoxetine',
        'promax': 'fluoxetine',
        'grozax': 'fluoxetine',
        
        # Proton pump inhibitors
        'prilosec': 'omeprazole',
        'nexium': 'esomeprazole',
        'prevacid': 'lansoprazole',
        'protonix': 'pantoprazole',
        'aciphex': 'rabeprazole',
        
        # Diabetes medications
        'glucophage': 'metformin',
        'januvia': 'sitagliptin',
        'actos': 'pioglitazone',
        'avandia': 'rosiglitazone',
        'ozempic': 'semaglutide',
        'humalog': 'insulin lispro',
        'lantus': 'insulin glargine',
        'novolog': 'insulin aspart',
        'levemir': 'insulin detemir',
        'tresiba': 'insulin degludec',
        
        # Blood pressure medications
        'lisinopril': 'lisinopril',
        'amlodipine': 'amlodipine',
        'metoprolol': 'metoprolol',
        'atenolol': 'atenolol',
        'losartan': 'losartan',
        'valsartan': 'valsartan',
        
        # Antibiotics
        'augmentin': 'amoxicillin',
        'amoxicillin': 'amoxicillin',
        'azithromycin': 'azithromycin',
        'cipro': 'ciprofloxacin',
        'levaquin': 'levofloxacin',
        
        # Anti-inflammatory
        'voltaren': 'diclofenac',
        'celebrex': 'celecoxib',
        'mobic': 'meloxicam',
        
        # Other common medications
        'rivo': 'rivaroxaban',
        'xarelto': 'rivaroxaban',
        'eliquis': 'apixaban',
        'pradaxa': 'dabigatran',
        'warfarin': 'warfarin',
        'coumadin': 'warfarin',
    }
    
    trade_lower = trade_name.lower().strip()
    
    # Check direct mapping
    if trade_lower in medicine_mappings:
        return medicine_mappings[trade_lower]
    
    # Try to extract from common patterns
    # Remove common suffixes
    suffixes_to_remove = ['-xr', '-er', '-sr', '-cr', '-odt', '-dt', '-or', '-ir', '-xr', '-xl']
    for suffix in suffixes_to_remove:
        if trade_lower.endswith(suffix):
            base_name = trade_lower[:-len(suffix)]
            if base_name in medicine_mappings:
                return medicine_mappings[base_name]
    
    return "" 