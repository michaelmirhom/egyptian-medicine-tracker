#!/usr/bin/env python3
"""
Test script to check API response
"""

import requests
import json

def test_api_response():
    """Test the API response for usage information"""
    print("🔍 Testing API Response")
    print("=" * 40)
    
    # Test the API search endpoint
    url = "http://localhost:5000/api/medicines/api-search"
    params = {"q": "Panadol"}
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Count: {data.get('count')}")
            
            if data.get('products'):
                product = data['products'][0]
                print(f"\nProduct Details:")
                print(f"  Name: {product.get('trade_name')}")
                print(f"  Price: {product.get('price')}")
                print(f"  Usage: {product.get('usage')}")
                print(f"  All keys: {list(product.keys())}")
                
                # Check if usage exists
                if product.get('usage'):
                    print(f"✅ Usage found: {product['usage'][:100]}...")
                else:
                    print("❌ No usage information in response")
            else:
                print("❌ No products in response")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_response() 