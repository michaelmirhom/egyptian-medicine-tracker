#!/usr/bin/env python3
"""
Test script to verify the fix for oxymetazoline brand questions.
"""

import requests
import json
import time

def test_oxymetazoline_questions():
    """Test questions about oxymetazoline brands"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is the brands of oxymetazoline",
            "expected_medicine": "oxymetazoline",
            "description": "Brands question"
        },
        {
            "question": "what is the brand name contain oxymetazoline",
            "expected_medicine": "oxymetazoline", 
            "description": "Brand name question"
        },
        {
            "question": "what are the brands of oxymetazoline",
            "expected_medicine": "oxymetazoline",
            "description": "Alternative brands question"
        },
        {
            "question": "usage of oxymetazoline",
            "expected_medicine": "oxymetazoline",
            "description": "Usage question"
        },
        {
            "question": "price of oxymetazoline",
            "expected_medicine": "oxymetazoline",
            "description": "Price question"
        }
    ]
    
    print("🧪 Testing Oxymetazoline Questions")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"Expected medicine: {test_case['expected_medicine']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/medicines/chat",
                json={"question": test_case['question']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get('reply', 'No reply found')
                
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Reply: {reply[:300]}...")
                
                # Check if the reply contains the correct medicine name
                has_correct_medicine = test_case['expected_medicine'].lower() in reply.lower()
                
                # Check if it's a proper response (not treating the whole question as medicine name)
                has_bad_extraction = any(bad_phrase in reply.lower() for bad_phrase in [
                    'brands of oxymetazoline', 'brand name contain oxymetazoline',
                    'brands of oxymetazoline is used for', 'brand name contain oxymetazoline is used for'
                ])
                
                if has_bad_extraction:
                    print("❌ FAILED: System extracted the whole question as medicine name")
                elif has_correct_medicine:
                    print("✅ SUCCESS: Correct medicine name found in reply")
                else:
                    print("⚠️  WARNING: Expected medicine name not found in reply")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 60)
        time.sleep(2)

def test_other_medicine_brand_questions():
    """Test brand questions for other medicines"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what are the brands of paracetamol",
            "expected_medicine": "paracetamol",
            "description": "Paracetamol brands"
        },
        {
            "question": "brand names of ibuprofen",
            "expected_medicine": "ibuprofen",
            "description": "Ibuprofen brand names"
        },
        {
            "question": "what is the brand name contain loratadine",
            "expected_medicine": "loratadine",
            "description": "Loratadine brand name"
        }
    ]
    
    print("\n🧪 Testing Other Medicine Brand Questions")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"Expected medicine: {test_case['expected_medicine']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/medicines/chat",
                json={"question": test_case['question']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get('reply', 'No reply found')
                
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Reply: {reply[:300]}...")
                
                # Check if the reply contains the correct medicine name
                has_correct_medicine = test_case['expected_medicine'].lower() in reply.lower()
                
                # Check if it's a proper response
                has_bad_extraction = any(bad_phrase in reply.lower() for bad_phrase in [
                    'brands of ', 'brand name contain ', 'brand names of '
                ])
                
                if has_bad_extraction:
                    print("❌ FAILED: System extracted the whole question as medicine name")
                elif has_correct_medicine:
                    print("✅ SUCCESS: Correct medicine name found in reply")
                else:
                    print("⚠️  WARNING: Expected medicine name not found in reply")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 60)
        time.sleep(2)

def test_clean_medicine_name_function():
    """Test the clean_medicine_name function directly"""
    
    print("\n🧪 Testing clean_medicine_name Function")
    print("=" * 60)
    
    try:
        from src.routes.medicine import clean_medicine_name
        
        test_cases = [
            ("brands of oxymetazoline", "oxymetazoline"),
            ("brand name contain oxymetazoline", "oxymetazoline"),
            ("what is the brands of paracetamol", "paracetamol"),
            ("usage of ibuprofen", "ibuprofen"),
            ("price of loratadine", "loratadine"),
            ("what is the brand name of aspirin", "aspirin")
        ]
        
        for input_name, expected_output in test_cases:
            result = clean_medicine_name(input_name)
            print(f"Input: '{input_name}'")
            print(f"Expected: '{expected_output}'")
            print(f"Result: '{result}'")
            
            if result == expected_output:
                print("✅ SUCCESS")
            else:
                print("❌ FAILED")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🏥 Testing Oxymetazoline Brand Question Fix")
    print("=" * 60)
    
    # Test the clean_medicine_name function
    test_clean_medicine_name_function()
    
    # Test oxymetazoline questions
    test_oxymetazoline_questions()
    
    # Test other medicine brand questions
    test_other_medicine_brand_questions()
    
    print("\n🎯 Test Summary:")
    print("• Should extract 'oxymetazoline' from 'brands of oxymetazoline'")
    print("• Should not treat the whole question as medicine name")
    print("• Should work for other medicine brand questions")
    print("\n✅ Testing complete!") 