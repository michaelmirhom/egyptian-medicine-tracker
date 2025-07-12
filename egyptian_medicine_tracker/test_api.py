#!/usr/bin/env python3
"""
Test script for the Egyptian Medicine Price API integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.services.medicine_api import medicine_api

def test_api_search():
    """Test the medicine search functionality"""
    print("Testing Medicine Price API Search...")
    print("=" * 50)
    
    # Test search for a common medicine
    test_medicines = ["paramol", "panadol", "augmentin"]
    
    for medicine_name in test_medicines:
        print(f"\nSearching for: {medicine_name}")
        print("-" * 30)
        
        success, products, error = medicine_api.search_medicines(medicine_name)
        
        if success:
            print(f"✅ Found {len(products)} products")
            for i, product in enumerate(products[:3], 1):  # Show first 3 results
                print(f"  {i}. {product.get('name', 'N/A')} - {product.get('price', 'N/A')} EGP")
                print(f"     ID: {product.get('id', 'N/A')}")
                print(f"     Image: {product.get('image', 'N/A')[:50]}...")
        else:
            print(f"❌ Error: {error}")
    
    print("\n" + "=" * 50)

def test_api_details():
    """Test getting detailed information for a specific medicine"""
    print("\nTesting Medicine Details API...")
    print("=" * 50)
    
    # First search for a medicine to get an ID
    success, products, error = medicine_api.search_medicines("paramol")
    
    if success and products:
        medicine_id = products[0].get('id')
        print(f"Getting details for medicine ID: {medicine_id}")
        print("-" * 40)
        
        success, details, error = medicine_api.get_medicine_details(medicine_id)
        
        if success and details:
            print("✅ Successfully retrieved medicine details:")
            print(f"  Name: {details.get('name', 'N/A')}")
            print(f"  Price: {details.get('price', 'N/A')} EGP")
            print(f"  Company: {details.get('company', 'N/A')}")
            print(f"  Description: {details.get('desc', 'N/A')[:100]}...")
            print(f"  Components: {details.get('components', [])}")
            print(f"  Image: {details.get('image', 'N/A')[:50]}...")
        else:
            print(f"❌ Error getting details: {error}")
    else:
        print("❌ Could not find any medicines to test details")

def test_search_and_details():
    """Test the combined search and details functionality"""
    print("\nTesting Combined Search and Details...")
    print("=" * 50)
    
    success, products, error = medicine_api.search_and_get_details("paramol")
    
    if success:
        print(f"✅ Found {len(products)} detailed products")
        for i, product in enumerate(products[:2], 1):  # Show first 2 results
            print(f"\n{i}. {product.get('name', 'N/A')}")
            print(f"   Price: {product.get('price', 'N/A')} EGP")
            print(f"   Company: {product.get('company', 'N/A')}")
            print(f"   Description: {product.get('desc', 'N/A')[:80]}...")
    else:
        print(f"❌ Error: {error}")

if __name__ == "__main__":
    print("Egyptian Medicine Price API Test")
    print("=" * 50)
    
    try:
        test_api_search()
        test_api_details()
        test_search_and_details()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc() 