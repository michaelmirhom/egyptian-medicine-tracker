#!/usr/bin/env python3
"""
Test the specific case mentioned in the requirements.
"""

import requests
import json

def test_specific_arabic_case():
    """Test the specific case: POST /api/medicines/chat with Arabic question"""
    
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Specific Arabic Case")
    print("=" * 60)
    
    # The specific case from requirements
    test_data = {
        "message": "ما هو استخدام كلاريتين؟"
    }
    
    print(f"📝 Testing: POST /api/medicines/chat")
    print(f"Body: {json.dumps(test_data, ensure_ascii=False)}")
    print(f"Expected: Returns usage text (hay-fever / allergy) pulled via fallback chain")
    
    try:
        response = requests.post(
            f"{base_url}/api/medicines/chat",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get('reply', 'No reply found')
            
            print(f"Reply: {reply}")
            
            # Check if it contains the expected usage information
            has_allergies = any(word in reply.lower() for word in ['allergies', 'hay fever', 'allergic'])
            has_symptoms = any(word in reply.lower() for word in ['runny nose', 'sneezing', 'itching'])
            has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication'])
            
            print(f"\n✅ Analysis:")
            print(f"Contains allergies/hay fever: {has_allergies}")
            print(f"Contains symptoms: {has_symptoms}")
            print(f"Contains usage info: {has_usage}")
            
            if has_usage and (has_allergies or has_symptoms):
                print("🎉 SUCCESS: Reply contains expected usage information for hay fever/allergies!")
            elif has_usage:
                print("✅ SUCCESS: Reply contains usage information!")
            else:
                print("❌ FAILED: Reply doesn't contain expected usage information")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_alternative_question_format():
    """Test alternative question format"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Alternative Question Format")
    print("=" * 60)
    
    # Test with "question" instead of "message"
    test_data = {
        "question": "ما هو استخدام كلاريتين؟"
    }
    
    print(f"📝 Testing: POST /api/medicines/chat with 'question' field")
    print(f"Body: {json.dumps(test_data, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/medicines/chat",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📊 Response:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get('reply', 'No reply found')
            
            print(f"Reply: {reply}")
            
            # Check if it contains the expected usage information
            has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication'])
            
            if has_usage:
                print("✅ SUCCESS: Reply contains usage information!")
            else:
                print("❌ FAILED: Reply doesn't contain usage information")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🏥 Testing Specific Arabic Case from Requirements")
    print("=" * 60)
    
    # Test the specific case
    test_specific_arabic_case()
    
    # Test alternative format
    test_alternative_question_format()
    
    print("\n🎯 Test Summary:")
    print("• Should handle Arabic question: 'ما هو استخدام كلاريتين؟'")
    print("• Should return usage information for hay fever/allergies")
    print("• Should work with both 'message' and 'question' fields")
    print("\n✅ Testing complete!") 