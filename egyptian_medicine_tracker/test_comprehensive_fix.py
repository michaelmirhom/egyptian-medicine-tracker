#!/usr/bin/env python3
"""
Comprehensive test script to verify all the fixes work correctly.
"""

import requests
import json

def test_comprehensive_fixes():
    """Test all the issues mentioned by the user"""
    base_url = "http://localhost:5000"
    
    # Test conversation flows
    test_cases = [
        {
            "name": "Multiple questions in one - should handle first question only",
            "message": "what is the price of pandol what is the usage",
            "expected_contains": "variants",
            "user_id": "test_user_1"
        },
        {
            "name": "Price query with 'of' - should clean medicine name",
            "message": "what is the price of panadol",
            "expected_contains": "variants",
            "user_id": "test_user_2"
        },
        {
            "name": "Price query without 'of' - should work",
            "message": "what is the price panadol",
            "expected_contains": "variants",
            "user_id": "test_user_3"
        },
        {
            "name": "Select variant",
            "message": "3",
            "expected_contains": "costs",
            "user_id": "test_user_3"
        },
        {
            "name": "Usage query after variant selection - should work with Arabic name",
            "message": "what is the usage",
            "expected_contains": "used for",
            "user_id": "test_user_3"
        },
        {
            "name": "Direct usage query",
            "message": "what is the use of panadol",
            "expected_contains": "used for",
            "user_id": "test_user_4"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        print(f"Message: '{test_case['message']}'")
        
        payload = {
            "message": test_case["message"],
            "user_id": test_case["user_id"]
        }
        
        try:
            response = requests.post(f"{base_url}/api/medicines/chat", json=payload)
            response.raise_for_status()
            
            result = response.json()
            reply = result.get("reply", "")
            
            print(f"Response: {reply}")
            
            if test_case["expected_contains"] in reply.lower():
                print(f"✅ PASS: Response contains '{test_case['expected_contains']}'")
            else:
                print(f"❌ FAIL: Response does not contain '{test_case['expected_contains']}'")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: {e}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("Testing comprehensive fixes...")
    test_comprehensive_fixes() 