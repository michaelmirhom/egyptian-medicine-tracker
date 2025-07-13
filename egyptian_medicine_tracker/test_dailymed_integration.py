#!/usr/bin/env python3
"""
Test script for DailyMed integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import app, db
from models.dailymed import DailyMedLabel
from services.usage_fallback import local_dailymed_usage, get_usage_generic

def test_dailymed_integration():
    """Test the DailyMed integration"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        print("Testing DailyMed integration...")
        
        # Test 1: Check if we can query the database
        count = DailyMedLabel.query.count()
        print(f"Current DailyMed records in database: {count}")
        
        if count == 0:
            print("No DailyMed records found. Please run the ingestion script first:")
            print("python scripts/ingest_dailymed.py")
            return
        
        # Test 2: Try to find a common medicine
        test_medicines = ["loratadine", "acetaminophen", "ibuprofen", "metformin"]
        
        for medicine in test_medicines:
            print(f"\nTesting medicine: {medicine}")
            
            # Test local DailyMed usage
            usage = local_dailymed_usage(medicine)
            if usage:
                print(f"✓ Found usage for {medicine}: {usage[:100]}...")
            else:
                print(f"✗ No usage found for {medicine}")
            
            # Test full fallback chain
            full_usage = get_usage_generic(medicine)
            if full_usage:
                print(f"✓ Full fallback chain found usage for {medicine}: {full_usage[:100]}...")
            else:
                print(f"✗ Full fallback chain found no usage for {medicine}")
        
        # Test 3: Test Arabic medicine name
        print(f"\nTesting Arabic medicine name: كلاريتين")
        arabic_usage = get_usage_generic("كلاريتين")
        if arabic_usage:
            print(f"✓ Found usage for Arabic name: {arabic_usage[:100]}...")
        else:
            print(f"✗ No usage found for Arabic name")

if __name__ == '__main__':
    test_dailymed_integration() 