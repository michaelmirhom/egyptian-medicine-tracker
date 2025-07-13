#!/usr/bin/env python3
"""
Debug script to check API response structure.
"""

import requests
import json

def debug_api_response():
    """Debug the API response structure"""
    
    base_url = "http://localhost:5000"
    
    test_question = "what is the price of lipitor"
    
    print(f"🔍 Debugging API Response for: '{test_question}'")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{base_url}/api/medicines/chat",
            json={"question": test_question},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"Response JSON: {json.dumps(result, indent=2)}")
                
                # Check all possible keys
                print(f"\nAvailable keys: {list(result.keys())}")
                
                if 'answer' in result:
                    print(f"Answer field: {result['answer']}")
                elif 'response' in result:
                    print(f"Response field: {result['response']}")
                elif 'message' in result:
                    print(f"Message field: {result['message']}")
                else:
                    print("No standard answer field found")
                    
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                print(f"Raw response: {response.text}")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_api_response() 