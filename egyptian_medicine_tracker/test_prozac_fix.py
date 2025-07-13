#!/usr/bin/env python3
"""
Test script to verify the Prozac Arabic name mapping and usage lookup fix.
"""

import requests
import json
import time

def test_prozac_arabic_mapping():
    """Test Prozac Arabic name mapping"""
    
    print("🧪 Testing Prozac Arabic Name Mapping")
    print("=" * 60)
    
    try:
        from src.services.name_resolver import arabic_to_english, is_arabic_text
        
        test_cases = [
            {
                "arabic": "بروزاك",
                "expected_english": "prozac",
                "description": "Prozac in Arabic"
            },
            {
                "arabic": "بروتاسي",
                "expected_english": "protasi",
                "description": "Protasi in Arabic"
            },
            {
                "arabic": "جروزا",
                "expected_english": "groza",
                "description": "Groza in Arabic"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print(f"Arabic: {test_case['arabic']}")
            print(f"Expected English: {test_case['expected_english']}")
            
            # Test Arabic text detection
            is_arabic = is_arabic_text(test_case['arabic'])
            print(f"✅ Arabic text detection: {is_arabic}")
            
            if is_arabic:
                # Test name resolution
                english_name = arabic_to_english(test_case['arabic'])
                print(f"✅ Resolved English name: {english_name}")
                
                if english_name == test_case['expected_english']:
                    print("✅ SUCCESS: Name resolution correct!")
                else:
                    print(f"❌ FAILED: Expected '{test_case['expected_english']}', got '{english_name}'")
            else:
                print("❌ FAILED: Arabic text not detected")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_prozac_usage_lookup():
    """Test Prozac usage lookup"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Prozac Usage Lookup")
    print("=" * 60)
    
    test_cases = [
        {
            "question": "what is the usage of Prozac",
            "expected_medicine": "prozac",
            "expected_generic": "fluoxetine",
            "description": "Prozac usage question"
        },
        {
            "question": "usage of بروزاك",
            "expected_medicine": "بروزاك",
            "expected_generic": "fluoxetine",
            "description": "Prozac Arabic usage question"
        },
        {
            "question": "what is Prozac used for",
            "expected_medicine": "prozac",
            "expected_generic": "fluoxetine",
            "description": "Prozac used for question"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"Expected medicine: {test_case['expected_medicine']}")
        print(f"Expected generic: {test_case['expected_generic']}")
        
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
                has_generic_name = test_case['expected_generic'].lower() in reply.lower()
                
                # Check if it contains usage information
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose', 'depression', 'antidepressant'])
                
                # Check if it's the wrong medicine (olanzapine instead of fluoxetine)
                has_wrong_medicine = 'olanzapine' in reply.lower()
                
                if has_wrong_medicine:
                    print("❌ FAILED: Reply contains wrong medicine (olanzapine instead of fluoxetine)")
                elif has_usage and (has_correct_medicine or has_generic_name):
                    print("✅ SUCCESS: Reply contains correct usage information!")
                elif has_usage:
                    print("✅ SUCCESS: Reply contains usage information!")
                else:
                    print("❌ FAILED: Reply doesn't contain usage information")
                    
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

def test_prozac_variant_selection():
    """Test Prozac variant selection and usage"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Prozac Variant Selection and Usage")
    print("=" * 60)
    
    # Step 1: Ask for price of Prozac to get variants
    print("\n📝 Step 1: Asking for price of Prozac")
    try:
        response1 = requests.post(
            f"{base_url}/api/medicines/chat",
            json={"question": "price of Prozac"},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            reply1 = result1.get('reply', '')
            print(f"✅ Price query response: {reply1[:200]}...")
            
            # Check if variants were returned
            if "variants" in reply1.lower() or "1." in reply1:
                print("✅ SUCCESS: Variants found, proceeding to selection")
                
                # Step 2: Select variant 1 (بروزاك)
                print("\n📝 Step 2: Selecting variant 1 (بروزاك)")
                response2 = requests.post(
                    f"{base_url}/api/medicines/chat",
                    json={"question": "1"},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    reply2 = result2.get('reply', '')
                    print(f"✅ Selection response: {reply2[:200]}...")
                    
                    # Step 3: Ask for usage
                    print("\n📝 Step 3: Asking for usage")
                    response3 = requests.post(
                        f"{base_url}/api/medicines/chat",
                        json={"question": "what is the usage"},
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response3.status_code == 200:
                        result3 = response3.json()
                        reply3 = result3.get('reply', '')
                        print(f"✅ Usage response: {reply3[:300]}...")
                        
                        # Check if usage information is found
                        has_usage = any(word in reply3.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose', 'depression', 'antidepressant'])
                        has_wrong_medicine = 'olanzapine' in reply3.lower()
                        
                        if has_wrong_medicine:
                            print("❌ FAILED: Reply contains wrong medicine (olanzapine instead of fluoxetine)")
                        elif has_usage:
                            print("✅ SUCCESS: Usage information found after variant selection!")
                        else:
                            print("❌ FAILED: No usage information found after variant selection")
                    else:
                        print(f"❌ Usage query error: {response3.status_code}")
                else:
                    print(f"❌ Selection error: {response2.status_code}")
            else:
                print("❌ No variants found in price response")
        else:
            print(f"❌ Price query error: {response1.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🏥 Testing Prozac Arabic Name Mapping and Usage Fix")
    print("=" * 60)
    
    # Test Arabic name mapping
    test_prozac_arabic_mapping()
    
    # Test usage lookup
    test_prozac_usage_lookup()
    
    # Test variant selection
    test_prozac_variant_selection()
    
    print("\n🎯 Test Summary:")
    print("• Arabic 'بروزاك' should map to 'prozac'")
    print("• Prozac should map to generic 'fluoxetine'")
    print("• Usage should be for depression/antidepressant, not olanzapine")
    print("• Variant selection should work with Arabic names")
    print("\n✅ Testing complete!") 