#!/usr/bin/env python3
"""
Test script for the Egyptian Medicine Price API integration
"""

import sys
import os
sys.path.append('.')

from src.routes.medicine import get_active_ingredients_api_first
from src.services.rxnav_api import rxnav_api

def test_specific_medicines():
    """Test the specific medicines the user mentioned"""
    medicines = ['keflex', 'ventolin', 'amoxil']
    
    print("=== TESTING API-FIRST APPROACH FOR USER'S MEDICINES ===\n")
    
    for medicine in medicines:
        print(f"🧪 Testing: {medicine.upper()}")
        print("-" * 40)
        
        # Test RxNav API directly first
        print(f"1. Testing RxNav API directly...")
        try:
            success, drug_info, error = rxnav_api.get_drug_info(medicine)
            if success and drug_info:
                print(f"   ✅ RxNav SUCCESS: {drug_info}")
            else:
                print(f"   ❌ RxNav FAILED: {error}")
        except Exception as e:
            print(f"   ❌ RxNav ERROR: {e}")
        
        # Test API-first function
        print(f"2. Testing get_active_ingredients_api_first...")
        try:
            ingredients = get_active_ingredients_api_first(medicine)
            if ingredients:
                print(f"   ✅ RESULT: {ingredients}")
            else:
                print(f"   ❌ NO INGREDIENTS FOUND")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("\n")

if __name__ == "__main__":
    test_specific_medicines() 