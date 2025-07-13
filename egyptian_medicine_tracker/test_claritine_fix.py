#!/usr/bin/env python3
"""
Test script to verify that Claritine usage lookup now works with the improved generic name mapping.
"""

import requests
import json
import time

def test_claritine_usage():
    """Test if Claritine usage lookup now works"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is claritine used for",
            "expected": "Should return loratadine usage information"
        },
        {
            "question": "usage of claritine",
            "expected": "Should return loratadine usage information"
        },
        {
            "question": "what is the price and usage of claritine",
            "expected": "Should return both price and loratadine usage information"
        }
    ]
    
    print("🧪 Testing Claritine Usage with Improved Mapping")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['question']}")
        print(f"Expected: {test_case['expected']}")
        
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
                
                # Check if reply contains usage information
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose', 'allergies', 'hay fever'])
                has_loratadine = 'loratadine' in reply.lower()
                
                if has_usage:
                    print("✅ SUCCESS: Reply contains usage information!")
                    if has_loratadine:
                        print("✅ BONUS: Reply correctly mentions loratadine!")
                    else:
                        print("⚠️  Note: Reply doesn't mention loratadine specifically")
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

def test_api_search_claritine():
    """Test API search for Claritine with usage information"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing API Search for Claritine")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/api/medicines/api-search",
            params={"q": "claritine"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success') and result.get('products'):
                products = result['products']
                print(f"✅ Found {len(products)} products")
                
                # Check if any product has usage info
                products_with_usage = 0
                for product in products:
                    usage = product.get('usage', '')
                    if usage and usage != 'Usage information not available':
                        products_with_usage += 1
                        print(f"✅ Product '{product.get('trade_name', 'Unknown')}' has usage info")
                        print(f"   Usage: {usage[:200]}...")
                        break
                
                if products_with_usage > 0:
                    print(f"✅ SUCCESS: {products_with_usage} products have usage information!")
                else:
                    print("⚠️  WARNING: No products have usage information")
                    
            else:
                print("❌ No products found")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_other_medicines():
    """Test other medicines to ensure the mapping works broadly"""
    
    base_url = "http://localhost:5000"
    
    test_medicines = [
        "claritin",
        "allegra", 
        "zyrtec",
        "benadryl"
    ]
    
    print("\n🧪 Testing Other Antihistamines")
    print("=" * 60)
    
    for medicine in test_medicines:
        print(f"\n📝 Testing: {medicine}")
        
        try:
            response = requests.post(
                f"{base_url}/api/medicines/chat",
                json={"question": f"what is {medicine} used for"},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                reply = result.get('reply', 'No reply found')
                
                # Check if reply contains usage information
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose'])
                
                if has_usage:
                    print(f"✅ SUCCESS: {medicine} has usage information!")
                else:
                    print(f"❌ FAILED: {medicine} has no usage information")
                    
            else:
                print(f"❌ Error for {medicine}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception for {medicine}: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("🏥 Testing Improved Generic Name Mapping")
    print("=" * 60)
    
    # Test Claritine usage
    test_claritine_usage()
    
    # Test API search
    test_api_search_claritine()
    
    # Test other antihistamines
    test_other_medicines()
    
    print("\n🎯 Test Summary:")
    print("• Claritine should now map to loratadine")
    print("• Usage information should be found from openFDA")
    print("• Other antihistamines should also work")
    print("• API search should return products with usage info")
    print("\n✅ Testing complete!") 