#!/usr/bin/env python3
"""
Test script for compound question handling in the medicine chatbot.
"""

import requests
import json
import time

def test_compound_questions():
    """Test compound questions like 'price and usage of medicine'"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is the price and usage of lipitor",
            "expected_behavior": "Should return both price variants and usage info for lipitor"
        },
        {
            "question": "what is the price and usage of panadol",
            "expected_behavior": "Should return both price variants and usage info for panadol"
        },
        {
            "question": "how much does rivo cost and what is it used for",
            "expected_behavior": "Should return both price and usage info for rivo"
        }
    ]
    
    print("🧪 Testing Compound Question Handling")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['question']}")
        print(f"Expected: {test_case['expected_behavior']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/medicines/chat",
                json={"question": test_case['question']},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('reply', 'No reply found')  # Fixed: use 'reply' instead of 'answer'
                
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Reply: {answer[:200]}...")
                
                # Check if both price and usage info are present
                has_price = any(word in answer.lower() for word in ['egp', 'price', 'cost', 'variants'])
                has_usage = any(word in answer.lower() for word in ['used for', 'usage', 'treat', 'indication'])
                
                if has_price and has_usage:
                    print("✅ SUCCESS: Both price and usage information found!")
                elif has_price:
                    print("⚠️  PARTIAL: Only price information found")
                elif has_usage:
                    print("⚠️  PARTIAL: Only usage information found")
                else:
                    print("❌ FAILED: Neither price nor usage information found")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(1)  # Small delay between tests

def test_simple_questions():
    """Test simple questions to ensure basic functionality still works"""
    
    base_url = "http://localhost:5000"
    
    test_cases = [
        {
            "question": "what is the price of lipitor",
            "expected": "Should return price variants for lipitor"
        },
        {
            "question": "what is lipitor used for",
            "expected": "Should return usage info for lipitor"
        }
    ]
    
    print("\n🧪 Testing Simple Questions (Baseline)")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['question']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            response = requests.post(
                f"{base_url}/api/medicines/chat",
                json={"question": test_case['question']},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('reply', 'No reply found')  # Fixed: use 'reply' instead of 'answer'
                
                print(f"✅ Status: {response.status_code}")
                print(f"📄 Reply: {answer[:150]}...")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on localhost:5000")
            break
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(1)

if __name__ == "__main__":
    print("🏥 Medicine Chatbot Compound Question Test")
    print("=" * 60)
    
    # Test simple questions first
    test_simple_questions()
    
    # Test compound questions
    test_compound_questions()
    
    print("\n🎯 Test Summary:")
    print("• Simple questions should work as before")
    print("• Compound questions should return both price and usage info")
    print("• Medicine names should be correctly extracted from both parts")
    print("\n✅ Testing complete!") 