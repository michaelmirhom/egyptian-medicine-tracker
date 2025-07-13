#!/usr/bin/env python3
"""
Test script for improved medicine chat functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import app
from routes.medicine import answer_medicine_question

def test_improved_chat():
    """Test the improved chat functionality"""
    with app.app_context():
        print("Testing Improved Medicine Chat Functionality")
        print("=" * 50)
        
        # Test cases
        test_cases = [
            # Comparison questions
            {
                "question": "What's the difference between Tylenol and Advil?",
                "expected_type": "comparison",
                "description": "Comparison between two medicines"
            },
            {
                "question": "Compare aspirin and ibuprofen",
                "expected_type": "comparison", 
                "description": "Compare medicines"
            },
            
            # Administration questions
            {
                "question": "How should I take metformin?",
                "expected_type": "administration",
                "description": "Administration question"
            },
            {
                "question": "How to take aspirin?",
                "expected_type": "administration",
                "description": "How to take question"
            },
            
            # Usage questions
            {
                "question": "What is loratadine used for?",
                "expected_type": "usage",
                "description": "Usage question"
            },
            {
                "question": "What are the indications for panadol?",
                "expected_type": "usage",
                "description": "Indications question"
            },
            
            # Price questions
            {
                "question": "What's the price of voltaren?",
                "expected_type": "price",
                "description": "Price question"
            },
            {
                "question": "How much does concor cost?",
                "expected_type": "price",
                "description": "Cost question"
            },
            
            # Category questions
            {
                "question": "What are antihistamines used for?",
                "expected_type": "category",
                "description": "Category question"
            },
            
            # Arabic questions
            {
                "question": "ما هو استخدام كلاريتين؟",
                "expected_type": "usage",
                "description": "Arabic usage question"
            },
            {
                "question": "ما هو سعر بانادول؟",
                "expected_type": "price",
                "description": "Arabic price question"
            },
            
            # Generic questions (should use context)
            {
                "question": "What is the usage?",
                "expected_type": "usage",
                "description": "Generic usage question (should use context)"
            },
            {
                "question": "What is the price?",
                "expected_type": "price", 
                "description": "Generic price question (should use context)"
            }
        ]
        
        # Run tests
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['description']}")
            print(f"Question: {test_case['question']}")
            print(f"Expected type: {test_case['expected_type']}")
            
            try:
                response = answer_medicine_question(test_case['question'])
                print(f"Response: {response[:200]}...")
                print("✓ Test completed")
            except Exception as e:
                print(f"✗ Error: {e}")
            
            print("-" * 30)
        
        print("\n" + "=" * 50)
        print("Testing completed!")

if __name__ == '__main__':
    test_improved_chat() 