#!/usr/bin/env python3
"""
Direct API testing for openFDA and DailyMed to check if they have information about Claritine and loratidine.
"""

import requests
import json
import time

def test_openfda_api():
    """Test openFDA API directly"""
    
    test_medicines = [
        "claritine",
        "loratidine", 
        "loratadine",  # Correct spelling
        "claritin",    # Alternative spelling
        "paracetamol",
        "aspirin"
    ]
    
    print("🧪 Testing openFDA API Directly")
    print("=" * 50)
    
    for medicine in test_medicines:
        print(f"\n📝 Testing: '{medicine}'")
        
        try:
            # Test with generic name search
            url = "https://api.fda.gov/drug/label.json"
            params = {
                'search': f'openfda.generic_name:{medicine}',
                'limit': 1
            }
            
            print(f"Requesting: {url}")
            print(f"Params: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    result = data['results'][0]
                    print(f"✅ Found result for '{medicine}'")
                    
                    # Check available fields
                    available_fields = []
                    for field in ['indications_and_usage', 'indications', 'clinical_pharmacology', 'description']:
                        if field in result:
                            available_fields.append(field)
                    
                    print(f"Available fields: {available_fields}")
                    
                    # Show first field content
                    if available_fields:
                        first_field = available_fields[0]
                        content = result[first_field]
                        if isinstance(content, list) and len(content) > 0:
                            content = content[0]
                        print(f"Content from '{first_field}': {content[:200]}...")
                else:
                    print(f"❌ No results found for '{medicine}'")
                    
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(1)

def test_dailymed_api():
    """Test DailyMed API directly"""
    
    test_medicines = [
        "claritine",
        "loratidine",
        "loratadine",  # Correct spelling
        "claritin",    # Alternative spelling
        "paracetamol",
        "aspirin"
    ]
    
    print("\n🧪 Testing DailyMed API Directly")
    print("=" * 50)
    
    for medicine in test_medicines:
        print(f"\n📝 Testing: '{medicine}'")
        
        try:
            # Step 1: Search for drug names
            url1 = "https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json"
            params1 = {'drug_name': medicine}
            
            print(f"Step 1 - Requesting: {url1}")
            print(f"Params: {params1}")
            
            response1 = requests.get(url1, params=params1, timeout=10)
            
            print(f"Status: {response1.status_code}")
            
            if response1.status_code == 200:
                data1 = response1.json()
                
                if data1.get('data') and len(data1['data']) > 0:
                    setid = data1['data'][0].get('setid')
                    print(f"✅ Found setid: {setid}")
                    
                    # Step 2: Get detailed information
                    url2 = f"https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.json"
                    
                    print(f"Step 2 - Requesting: {url2}")
                    
                    response2 = requests.get(url2, timeout=10)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        
                        if data2.get('data') and len(data2['data']) > 0:
                            result = data2['data'][0]
                            print(f"✅ Found detailed data for '{medicine}'")
                            
                            # Check available fields
                            available_fields = []
                            for field in ['indications_and_usage', 'clinical_pharmacology', 'description', 'drug_interactions']:
                                if field in result:
                                    available_fields.append(field)
                            
                            print(f"Available fields: {available_fields}")
                            
                            # Show first field content
                            if available_fields:
                                first_field = available_fields[0]
                                content = result[first_field]
                                print(f"Content from '{first_field}': {content[:200]}...")
                        else:
                            print(f"❌ No detailed data found")
                    else:
                        print(f"❌ Step 2 API error: {response2.status_code}")
                else:
                    print(f"❌ No drug names found for '{medicine}'")
            else:
                print(f"❌ Step 1 API error: {response1.status_code}")
                print(f"Response: {response1.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print("-" * 50)
        time.sleep(1)

def test_alternative_spellings():
    """Test alternative spellings and variations"""
    
    print("\n🧪 Testing Alternative Spellings")
    print("=" * 50)
    
    # Test different variations of loratadine
    variations = [
        "loratadine",
        "loratidine", 
        "claritin",
        "claritine",
        "claratyne",
        "loratadine hydrochloride",
        "loratadine hcl"
    ]
    
    for variation in variations:
        print(f"\n📝 Testing variation: '{variation}'")
        
        try:
            # Test openFDA
            url = "https://api.fda.gov/drug/label.json"
            params = {
                'search': f'openfda.generic_name:{variation}',
                'limit': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    print(f"✅ openFDA found: '{variation}'")
                else:
                    print(f"❌ openFDA not found: '{variation}'")
            else:
                print(f"❌ openFDA error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    print("🏥 Direct API Testing for Claritine/Loratadine")
    print("=" * 60)
    
    # Test openFDA API
    test_openfda_api()
    
    # Test DailyMed API
    test_dailymed_api()
    
    # Test alternative spellings
    test_alternative_spellings()
    
    print("\n🎯 Test Summary:")
    print("• Testing if APIs have information about Claritine/loratadine")
    print("• Checking different spellings and variations")
    print("• Verifying API responses and available data")
    print("\n✅ Testing complete!") 