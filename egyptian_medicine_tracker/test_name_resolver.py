#!/usr/bin/env python3
"""
Test script for the new name resolver service.
"""

import requests
import json
import time

def test_name_resolver_direct():
    """Test the name resolver service directly"""
    
    print("🧪 Testing Name Resolver Service Directly")
    print("=" * 60)
    
    # Test cases for Arabic medicine names
    test_cases = [
        {
            "arabic": "كلاريتين",
            "expected_english": "claritin",
            "description": "Claritine in Arabic"
        },
        {
            "arabic": "بانادول",
            "expected_english": "panadol", 
            "description": "Panadol in Arabic"
        },
        {
            "arabic": "ريفو",
            "expected_english": "rivo",
            "description": "Rivo in Arabic"
        },
        {
            "arabic": "أموكسيسيلين",
            "expected_english": "amoxicillin",
            "description": "Amoxicillin in Arabic"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Arabic: {test_case['arabic']}")
        print(f"Expected English: {test_case['expected_english']}")
        
        try:
            # Import and test the name resolver
            from src.services.name_resolver import arabic_to_english, is_arabic_text
            
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
        
        print("-" * 60)

def test_chat_with_arabic():
    """Test the chat endpoint with Arabic medicine names"""
    
    base_url = "http://localhost:5000"
    
    print("\n🧪 Testing Chat with Arabic Medicine Names")
    print("=" * 60)
    
    test_cases = [
        {
            "question": "ما هو استخدام كلاريتين؟",
            "expected": "Should return loratadine usage information",
            "description": "Usage question in Arabic"
        },
        {
            "question": "سعر كلاريتين",
            "expected": "Should return price information",
            "description": "Price question in Arabic"
        },
        {
            "question": "استخدام بانادول",
            "expected": "Should return paracetamol usage information",
            "description": "Usage question for Panadol in Arabic"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
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
                
                if 'استخدام' in test_case['question'] or 'usage' in test_case['question'].lower():
                    if has_usage:
                        print("✅ SUCCESS: Reply contains usage information!")
                    else:
                        print("❌ FAILED: Reply doesn't contain usage information")
                elif 'سعر' in test_case['question'] or 'price' in test_case['question'].lower():
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

def test_api_search_with_arabic():
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

def test_wikidata_lookup():
    """Test Wikidata lookup functionality"""
    
    print("\n🧪 Testing Wikidata Lookup")
    print("=" * 60)
    
    try:
        from src.services.name_resolver import wikidata_lookup
        
        # Test with a known medicine
        test_name = "كلاريتين"
        print(f"📝 Testing Wikidata lookup for: {test_name}")
        
        result = wikidata_lookup(test_name)
        if result:
            print(f"✅ Wikidata found: {result}")
        else:
            print("⚠️  Wikidata returned no results (this is normal for some medicines)")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🏥 Testing New Name Resolver Service")
    print("=" * 60)
    
    # Test name resolver directly
    test_name_resolver_direct()
    
    # Test Wikidata lookup
    test_wikidata_lookup()
    
    # Test chat with Arabic
    test_chat_with_arabic()
    
    # Test API search with Arabic
    test_api_search_with_arabic()
    
    print("\n🎯 Test Summary:")
    print("• Name resolver should handle Arabic medicine names")
    print("• Wikidata lookup should work for known medicines")
    print("• Chat should work with Arabic questions")
    print("• API search should work with Arabic names")
    print("\n✅ Testing complete!") 