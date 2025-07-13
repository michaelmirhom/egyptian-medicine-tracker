#!/usr/bin/env python3
"""
Test script for the new usage fallback system.
Tests the chain: RxNav -> openFDA -> DailyMed
"""

import requests
import json
import time

def test_usage_fallback():
    """Test the usage fallback system with various medicines"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "medicine": "lipitor",
            "expected": "Should return usage info from any of the APIs"
        },
        {
            "medicine": "panadol", 
            "expected": "Should return usage info from any of the APIs"
        },
        {
            "medicine": "aspirin",
            "expected": "Should return usage info from any of the APIs"
        },
        {
            "medicine": "ibuprofen",
            "expected": "Should return usage info from any of the APIs"
        }
    ]
    
    print("🧪 Testing Usage Fallback System")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['medicine']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            # Test API search endpoint
            response = requests.get(
                f"{base_url}/api/medicines/api-search",
                params={"q": test_case['medicine']},
                timeout=30  # Longer timeout for multiple API calls
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
                            print(f"   Usage: {usage[:150]}...")
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
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(2)  # Delay between tests

def test_chat_usage():
    """Test usage queries in the chat system"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is lipitor used for",
            "expected": "Should return usage info from fallback APIs"
        },
        {
            "question": "what is the usage of panadol",
            "expected": "Should return usage info from fallback APIs"
        }
    ]
    
    print("\n🧪 Testing Chat Usage Queries")
    print("=" * 50)
    
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
                print(f"📄 Reply: {reply[:200]}...")
                
                # Check if reply contains usage information
                if any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication', 'purpose']):
                    print("✅ SUCCESS: Reply contains usage information!")
                else:
                    print("⚠️  WARNING: Reply doesn't seem to contain usage information")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(2)

def test_compound_questions():
    """Test compound questions with usage"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is the price and usage of lipitor",
            "expected": "Should return both price and usage info"
        }
    ]
    
    print("\n🧪 Testing Compound Questions with Usage")
    print("=" * 50)
    
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
                
                # Check if reply contains both price and usage
                has_price = any(word in reply.lower() for word in ['egp', 'price', 'cost', 'variants'])
                has_usage = any(word in reply.lower() for word in ['used for', 'usage', 'treat', 'indication'])
                
                if has_price and has_usage:
                    print("✅ SUCCESS: Reply contains both price and usage information!")
                elif has_price:
                    print("⚠️  PARTIAL: Reply contains price but not usage")
                elif has_usage:
                    print("⚠️  PARTIAL: Reply contains usage but not price")
                else:
                    print("❌ FAILED: Reply contains neither price nor usage")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(2)

if __name__ == "__main__":
    print("🏥 Medicine Usage Fallback System Test")
    print("=" * 60)
    
    # Test API search with usage fallback
    test_usage_fallback()
    
    # Test chat usage queries
    test_chat_usage()
    
    # Test compound questions
    test_compound_questions()
    
    print("\n🎯 Test Summary:")
    print("• API search should return products with usage information")
    print("• Chat queries should return usage information from fallback APIs")
    print("• Compound questions should return both price and usage")
    print("• Fallback chain: RxNav -> openFDA -> DailyMed")
    print("\n✅ Testing complete!") 