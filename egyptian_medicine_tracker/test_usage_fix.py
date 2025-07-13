#!/usr/bin/env python3
"""
Test script to verify the usage query fix works correctly.
This simulates the conversation flow that was failing.
"""

import requests
import json

def test_usage_query_fix():
    """Test the conversation flow that was failing"""
    base_url = "http://localhost:5000"
    
    # Test conversation flow
    test_cases = [
        {
            "message": "what is the cost of rivo",
            "expected_contains": "variants"
        },
        {
            "message": "2",
            "expected_contains": "costs"
        },
        {
            "message": "what is the usage",
            "expected_contains": "used for"
        }
    ]
    
    user_id = "test_user_123"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_case['message']}' ---")
        
        payload = {
            "message": test_case["message"],
            "user_id": user_id
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
    print("Testing usage query fix...")
    test_usage_query_fix() 