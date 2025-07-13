#!/usr/bin/env python3
"""
Test script to verify Arabic medicine name mapping and usage lookup.
"""

import requests
import json
import time

def test_arabic_medicine_names():
    """Test Arabic medicine names to ensure they map correctly and find usage"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "usage of كلاريتين",
            "expected": "Should return loratadine usage information",
            "arabic_name": "كلاريتين",
            "english_name": "claritine"
        },
        {
            "question": "what is كلاريتين used for",
            "expected": "Should return loratadine usage information",
            "arabic_name": "كلاريتين",
            "english_name": "claritine"
        },
        {
            "question": "price of كلاريتين",
            "expected": "Should return price information",
            "arabic_name": "كلاريتين",
            "english_name": "claritine"
        },
        {
            "question": "usage of بانادول",
            "expected": "Should return paracetamol usage information",
            "arabic_name": "بانادول",
            "english_name": "panadol"
        },
        {
            "question": "usage of ريفو",
            "expected": "Should return rivaroxaban usage information",
            "arabic_name": "ريفو",
            "english_name": "rivo"
        }
    ]
    
    print("🧪 Testing Arabic Medicine Name Mapping")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['question']}")
        print(f"Arabic: {test_case['arabic_name']} -> English: {test_case['english_name']}")
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
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose', 'allergies', 'hay fever', 'pain', 'fever'])
                has_price = any(word in reply.lower() for word in ['egp', 'price', 'cost', 'variants'])
                
                if 'usage' in test_case['question'].lower():
                    if has_usage:
                        print("✅ SUCCESS: Reply contains usage information!")
                    else:
                        print("❌ FAILED: Reply doesn't contain usage information")
                elif 'price' in test_case['question'].lower():
                    if has_price:
                        print("✅ SUCCESS: Reply contains price information!")
                    else:
                        print("❌ FAILED: Reply doesn't contain price information")
                else:
                    if has_usage or has_price:
                        print("✅ SUCCESS: Reply contains relevant information!")
                    else:
                        print("❌ FAILED: Reply doesn't contain relevant information")
                    
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

def test_arabic_variant_selection():
    """Test selecting Arabic medicine variants and then asking for usage"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Arabic Variant Selection and Usage")
    print("=" * 60)
    
    # Step 1: Ask for price of كلاريتين to get variants
    print("\n📝 Step 1: Asking for price of كلاريتين")
    try:
        response1 = requests.post(
            f"{base_url}/api/medicines/chat",
            json={"question": "price of كلاريتين"},
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
                
                # Step 2: Select variant 1
                print("\n📝 Step 2: Selecting variant 1")
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
                        has_usage = any(word in reply3.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose', 'allergies', 'hay fever'])
                        
                        if has_usage:
                            print("✅ SUCCESS: Usage information found after Arabic variant selection!")
                        else:
                            print("❌ FAILED: No usage information found after Arabic variant selection")
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

def test_arabic_api_search():
    """Test API search with Arabic medicine names"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing API Search with Arabic Names")
    print("=" * 60)
    
    arabic_medicines = ["كلاريتين", "بانادول", "ريفو"]
    
    for medicine in arabic_medicines:
        print(f"\n📝 Testing API search for: {medicine}")
        
        try:
            response = requests.get(
                f"{base_url}/api/medicines/api-search",
                params={"q": medicine},
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
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    print("🏥 Testing Arabic Medicine Name Mapping")
    print("=" * 60)
    
    # Test Arabic medicine names
    test_arabic_medicine_names()
    
    # Test Arabic variant selection
    test_arabic_variant_selection()
    
    # Test Arabic API search
    test_arabic_api_search()
    
    print("\n🎯 Test Summary:")
    print("• Arabic medicine names should map to English equivalents")
    print("• Usage information should be found for Arabic names")
    print("• Variant selection should work with Arabic names")
    print("• API search should work with Arabic names")
    print("\n✅ Testing complete!") 