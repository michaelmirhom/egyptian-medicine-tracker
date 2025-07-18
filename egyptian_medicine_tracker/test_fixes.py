#!/usr/bin/env python3
"""
Test script to verify fixes for medicine name extraction issues
"""
import sys
sys.path.append('.')

from src.routes.medicine import extract_medicine_name_from_question, extract_multiple_medicines_from_question

def test_medicine_extraction():
    """Test the medicine name extraction fixes"""
    print("=== TESTING MEDICINE NAME EXTRACTION FIXES ===\n")
    
    test_cases = [
        # Single medicine active ingredient questions
        ("what is the active ingredint in ProAir HFA", "ProAir HFA"),
        ("what is the active ingredint in Singulair", "Singulair"),
        ("what is the active ingredint in Zithromax", "Zithromax"),
        ("what is the active ingredint in Neurontin", "Neurontin"),
        ("what is the active ingredint in Plavix", "Plavix"),
        
        # Comparison questions
        ("compare between palvix and panadol", ["plavix", "panadol"]),
    ]
    
    print("🧪 Testing single medicine extraction:")
    for question, expected in test_cases[:-1]:  # All except the last one
        print(f"\nInput: '{question}'")
        result = extract_medicine_name_from_question(question.lower())
        print(f"Expected: '{expected}'")
        print(f"Got: '{result}'")
        if result and expected.lower() in result.lower():
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    print("\n🧪 Testing comparison extraction:")
    question, expected = test_cases[-1]
    print(f"\nInput: '{question}'")
    result = extract_multiple_medicines_from_question(question.lower())
    print(f"Expected: {expected}")
    print(f"Got: {result}")
    if len(result) >= 2 and all(exp in [r.lower() for r in result] for exp in expected):
        print("✅ PASS")
    else:
        print("❌ FAIL")

if __name__ == "__main__":
    test_medicine_extraction() 