#!/usr/bin/env python3
"""
Arabic to English medicine name resolver with multiple fallback methods.
"""

import requests
import re
import json
from typing import Optional

# Hard-coded dictionary for fast lookups
DICTIONARY = {
    "كلاريتين": "claritin",
    "بانادول": "panadol", 
    "البانادول": "panadol",  # With definite article
    "ريفو": "rivo",
    "الريفو": "rivo",  # With definite article
    "فولتارين": "voltaren",
    "الفولتارين": "voltaren",  # With definite article
    "كونكور": "concor",
    "الكونكور": "concor",  # With definite article
    "ليبيتور": "lipitor",
    "الليبيتور": "lipitor",  # With definite article
    "أوجمنتين": "augmentin",
    "الأوجمنتين": "augmentin",  # With definite article
    "أموكسيسيلين": "amoxicillin",
    "الأموكسيسيلين": "amoxicillin",  # With definite article
    "لوراتادين": "loratadine",
    "اللوراتادين": "loratadine",  # With definite article
    "أليجرا": "allegra",
    "الأليجرا": "allegra",  # With definite article
    "زيرتيك": "zyrtec",
    "الزيرتيك": "zyrtec",  # With definite article
    "بينادريل": "benadryl",
    "البينادريل": "benadryl",  # With definite article
    "أسبيرين": "aspirin",
    "الأسبيرين": "aspirin",  # With definite article
    "أيبوبروفين": "ibuprofen",
    "الأيبوبروفين": "ibuprofen",  # With definite article
    "أزيثروميسين": "azithromycin",
    "الأزيثروميسين": "azithromycin",  # With definite article
    "ديكلوفيناك": "diclofenac",
    "الديكلوفيناك": "diclofenac",  # With definite article
    "سيتريزين": "cetirizine",
    "السيتريزين": "cetirizine",  # With definite article
    "أوميبرازول": "omeprazole",
    "الأوميبرازول": "omeprazole",  # With definite article
    "ميتفورمين": "metformin",
    "الميتفورمين": "metformin",  # With definite article
    "بروزاك": "prozac",  # Prozac in Arabic
    "البروزاك": "prozac",  # With definite article
    "بروتاسي": "protasi",  # Alternative spelling
    "جروزا": "groza",  # Alternative spelling
    "بروماكس": "promax",  # Alternative spelling
    "جروزاكس": "grozax",  # Alternative spelling
}

def wikidata_lookup(arabic_name: str) -> Optional[str]:
    """
    Look up Arabic medicine name in Wikidata to find English equivalent.
    
    Args:
        arabic_name (str): Arabic medicine name
        
    Returns:
        Optional[str]: English medicine name if found, None otherwise
    """
    try:
        # SPARQL query to find English label for Arabic medicine
        sparql_query = f"""
        SELECT ?enLabel WHERE {{
          ?d rdfs:label "{arabic_name}"@ar; rdfs:label ?enLabel.
          FILTER(lang(?enLabel)="en")
        }} LIMIT 1
        """
        
        url = "https://query.wikidata.org/sparql"
        headers = {
            "Accept": "application/json",
            "User-Agent": "MedicineTracker/1.0"
        }
        params = {
            "query": sparql_query,
            "format": "json"
        }
        
        print(f"[DEBUG] [wikidata_lookup] Querying Wikidata for: '{arabic_name}'")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', {}).get('bindings', [])
            
            if results:
                english_name = results[0].get('enLabel', {}).get('value')
                print(f"[DEBUG] [wikidata_lookup] Found English name: '{english_name}'")
                return english_name
            else:
                print(f"[DEBUG] [wikidata_lookup] No results found for '{arabic_name}'")
        else:
            print(f"[DEBUG] [wikidata_lookup] Wikidata API error: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] [wikidata_lookup] Exception: {e}")
    
    return None

def rxnav_approx(term: str) -> Optional[str]:
    """
    Use RxNav approximateTerm to find medicine name with misspellings.
    
    Args:
        term (str): Medicine name (possibly misspelled)
        
    Returns:
        Optional[str]: Corrected medicine name if found, None otherwise
    """
    try:
        url = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
        params = {
            "term": term,
            "maxEntries": 1
        }
        
        print(f"[DEBUG] [rxnav_approx] Querying RxNav for: '{term}'")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('approximateGroup', {}).get('candidate', [])
            
            if candidates:
                corrected_term = candidates[0].get('name')
                print(f"[DEBUG] [rxnav_approx] Found corrected term: '{corrected_term}'")
                return corrected_term
            else:
                print(f"[DEBUG] [rxnav_approx] No candidates found for '{term}'")
        else:
            print(f"[DEBUG] [rxnav_approx] RxNav API error: {response.status_code}")
            
    except Exception as e:
        print(f"[DEBUG] [rxnav_approx] Exception: {e}")
    
    return None

def libretranslate_stub(text: str) -> Optional[str]:
    """
    Stub for LibreTranslate integration.
    TODO: Implement self-hosted LibreTranslate API call
    
    Args:
        text (str): Arabic text to translate
        
    Returns:
        Optional[str]: Translated text if available, None otherwise
    """
    # TODO: Implement LibreTranslate API call
    # Example implementation:
    # url = "http://localhost:5000/translate"
    # data = {"q": text, "source": "ar", "target": "en"}
    # response = requests.post(url, json=data)
    # return response.json().get("translatedText")
    
    print(f"[DEBUG] [libretranslate_stub] Stub called for: '{text}'")
    return None

def normalize_arabic_name(name: str) -> str:
    """
    Normalize Arabic medicine name by removing extra spaces and diacritics.
    
    Args:
        name (str): Raw Arabic name
        
    Returns:
        str: Normalized Arabic name
    """
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', name.strip())
    
    # Remove Arabic diacritics (tashkeel)
    normalized = re.sub(r'[\u064B-\u065F\u0670]', '', normalized)
    
    return normalized

def arabic_to_english(name: str) -> Optional[str]:
    """
    Convert Arabic medicine name to English using multiple fallback methods.
    
    Args:
        name (str): Arabic medicine name
        
    Returns:
        Optional[str]: English medicine name if found, None otherwise
    """
    if not name:
        return None
    
    # Normalize the input
    normalized_name = normalize_arabic_name(name)
    print(f"[DEBUG] [arabic_to_english] Converting: '{name}' -> '{normalized_name}'")
    
    # Step 1: Check hard-coded dictionary (fastest)
    if normalized_name in DICTIONARY:
        english_name = DICTIONARY[normalized_name]
        print(f"[DEBUG] [arabic_to_english] Found in dictionary: '{normalized_name}' -> '{english_name}'")
        return english_name
    
    # Step 2: Try Wikidata lookup
    english_name = wikidata_lookup(normalized_name)
    if english_name:
        print(f"[DEBUG] [arabic_to_english] Found via Wikidata: '{normalized_name}' -> '{english_name}'")
        return english_name
    
    # Step 3: Try RxNav approximate term (for misspellings in Latin letters)
    # First, try to transliterate Arabic to Latin letters
    # This is a simple approach - in production you might want a proper transliteration library
    english_name = rxnav_approx(normalized_name)
    if english_name:
        print(f"[DEBUG] [arabic_to_english] Found via RxNav approx: '{normalized_name}' -> '{english_name}'")
        return english_name
    
    # Step 4: Try LibreTranslate (stub for now)
    english_name = libretranslate_stub(normalized_name)
    if english_name:
        print(f"[DEBUG] [arabic_to_english] Found via LibreTranslate: '{normalized_name}' -> '{english_name}'")
        return english_name
    
    print(f"[DEBUG] [arabic_to_english] No English equivalent found for '{normalized_name}'")
    return None

def is_arabic_text(text: str) -> bool:
    """
    Check if text contains Arabic characters.
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if text contains Arabic characters
    """
    return bool(re.search(r'[ء-ي]', text)) 