#!/usr/bin/env python3
"""
Test script for the specific issues reported by the user
Tests: ProAir HFA, Singulair, Zithromax, Neurontin, Plavix, and comparisons
"""
import sys
import json
sys.path.append('.')

from src.routes.medicine import answer_medicine_question

def test_user_reported_issues():
    """Test all the specific issues the user reported"""
    print("=== TESTING USER REPORTED ISSUES ===\n")
    
    # Test cases - the exact questions the user asked
    test_cases = [
        "what is the active ingredint of ProAir HFA",
        "what is the active ingredint of Singulair", 
        "what is the active ingredint of Zithromax",
        "what is the active ingredint of Neurontin",
        "what is the active ingredint of Plavix",
        "compare between palvix and panadol"
    ]
    
    user_id = "test_user"
    
    for i, question in enumerate(test_cases, 1):
        print(f"🧪 TEST {i}: {question}")
        print("-" * 50)
        
        try:
            # Call the main chat function
            response = answer_medicine_question(question, user_id)
            print(f"✅ RESPONSE: {response}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("\n")

if __name__ == "__main__":
    test_user_reported_issues() 