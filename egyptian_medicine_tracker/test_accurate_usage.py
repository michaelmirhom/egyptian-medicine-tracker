#!/usr/bin/env python3
"""
Test script to verify accurate medicine usage information.
"""

import requests
import json
import time

def test_accurate_usage():
    """Test that the system returns accurate usage information"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Accurate Medicine Usage Information")
    print("=" * 60)
    
    test_cases = [
        {
            "question": "what is the usage of Ozempic",
            "expected_keywords": ["diabetes", "blood sugar", "weight management", "semaglutide"],
            "wrong_keywords": ["nervous tension", "relief of", "condition listed above"],
            "description": "Ozempic usage"
        },
        {
            "question": "what is the usage of semaglutide",
            "expected_keywords": ["diabetes", "blood sugar", "weight management"],
            "wrong_keywords": ["nervous tension", "relief of", "condition listed above"],
            "description": "Semaglutide usage"
        },
        {
            "question": "what is the usage of Humalog",
            "expected_keywords": ["diabetes", "insulin", "blood sugar", "glucose"],
            "wrong_keywords": ["nervous tension", "relief of", "condition listed above"],
            "description": "Humalog usage"
        },
        {
            "question": "what is the usage of Prozac",
            "expected_keywords": ["depression", "fluoxetine", "antidepressant", "SSRI"],
            "wrong_keywords": ["olanzapine", "schizophrenia", "bipolar"],
            "description": "Prozac usage"
        },
        {
            "question": "what is the usage of Panadol",
            "expected_keywords": ["pain", "fever", "paracetamol", "acetaminophen"],
            "wrong_keywords": ["diabetes", "insulin", "depression"],
            "description": "Panadol usage"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        
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
                
                # Check for expected keywords
                has_expected = any(keyword.lower() in reply.lower() for keyword in test_case['expected_keywords'])
                
                # Check for wrong keywords
                has_wrong = any(keyword.lower() in reply.lower() for keyword in test_case['wrong_keywords'])
                
                # Check if it contains usage information
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose'])
                
                if has_wrong:
                    print("❌ FAILED: Reply contains wrong/irrelevant information")
                elif has_expected and has_usage:
                    print("✅ SUCCESS: Reply contains accurate usage information!")
                elif has_usage:
                    print("✅ SUCCESS: Reply contains usage information (partial validation)")
                else:
                    print("❌ FAILED: Reply doesn't contain expected usage information")
                    
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

def test_local_database():
    """Test the local usage database directly"""
    
    print("\n🧪 Testing Local Usage Database")
    print("=" * 60)
    
    try:
        from src.services.usage_fallback import get_local_usage, LOCAL_USAGE_DATABASE
        
        test_medicines = [
            "ozempic",
            "semaglutide", 
            "humalog",
            "prozac",
            "panadol"
        ]
        
        for medicine in test_medicines:
            print(f"\n📝 Testing: {medicine}")
            usage = get_local_usage(medicine)
            if usage:
                print(f"✅ Found: {usage[:100]}...")
            else:
                print(f"❌ Not found in local database")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_wrong_info_detection():
    """Test the wrong information detection function"""
    
    print("\n🧪 Testing Wrong Information Detection")
    print("=" * 60)
    
    try:
        from src.services.usage_fallback import is_wrong_usage_info
        
        test_cases = [
            {
                "text": "Use For relief of naturally occurring simple nervous tension",
                "expected": True,
                "description": "Wrong nervous tension text"
            },
            {
                "text": "INDICATIONS Condition listed above or as directed by the physician",
                "expected": True,
                "description": "Generic placeholder text"
            },
            {
                "text": "Ozempic (semaglutide) is used to improve blood sugar control in adults with type 2 diabetes mellitus.",
                "expected": False,
                "description": "Correct Ozempic usage"
            },
            {
                "text": "Prozac (fluoxetine) is used to treat depression, obsessive-compulsive disorder, panic disorder, and bulimia nervosa.",
                "expected": False,
                "description": "Correct Prozac usage"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['description']}")
            print(f"Text: {test_case['text']}")
            
            result = is_wrong_usage_info(test_case['text'])
            print(f"Result: {result}")
            
            if result == test_case['expected']:
                print("✅ SUCCESS: Detection correct!")
            else:
                print(f"❌ FAILED: Expected {test_case['expected']}, got {result}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🏥 Testing Accurate Medicine Usage Information")
    print("=" * 60)
    
    # Test local database
    test_local_database()
    
    # Test wrong info detection
    test_wrong_info_detection()
    
    # Test accurate usage
    test_accurate_usage()
    
    print("\n🎯 Test Summary:")
    print("• Local database should contain accurate usage for common medicines")
    print("• Wrong information should be detected and rejected")
    print("• API responses should be validated before being returned")
    print("• Special cases (Prozac, Ozempic) should always return correct info")
    print("\n✅ Testing complete!") 