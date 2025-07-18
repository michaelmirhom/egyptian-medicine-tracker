#!/usr/bin/env python3
"""
Comprehensive Test Script for Egyptian Medicine Tracker Chat System

This script tests various types of questions that the chat system can handle:
- Usage and indications questions
- Price questions  
- Active ingredient questions
- Comparison questions
- General medicine information
- Arabic language support
- Context maintenance
- Misspelling tolerance
- Greetings and help requests
"""

import requests
import json
import time
from typing import List, Dict

# Configuration
BASE_URL = "http://localhost:5000"
CHAT_ENDPOINT = f"{BASE_URL}/api/medicines/chat"

def send_chat_message(question: str, user_id: str = "test_user") -> Dict:
    """Send a chat message and return the response."""
    payload = {
        "question": question,
        "user_id": user_id
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def print_test_result(test_name: str, question: str, response: Dict):
    """Print test result in a formatted way."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"QUESTION: {question}")
    print(f"{'='*60}")
    
    if "error" in response:
        print(f"❌ ERROR: {response['error']}")
    else:
        print(f"✅ RESPONSE: {response.get('reply', 'No reply field')}")
    
    print(f"{'='*60}")

def test_greetings_and_help():
    """Test greeting and help functionality."""
    print("\n🧪 TESTING GREETINGS AND HELP")
    
    greetings = [
        "Hello",
        "Hi there",
        "مرحبا",
        "أهلا وسهلا",
        "السلام عليكم"
    ]
    
    help_questions = [
        "What can you do?",
        "Help",
        "How can you help me?"
    ]
    
    for greeting in greetings:
        response = send_chat_message(greeting)
        print_test_result("Greeting", greeting, response)
        time.sleep(1)
    
    for help_q in help_questions:
        response = send_chat_message(help_q)
        print_test_result("Help Request", help_q, response)
        time.sleep(1)

def test_usage_questions():
    """Test usage and indication questions."""
    print("\n🧪 TESTING USAGE QUESTIONS")
    
    usage_questions = [
        # English questions
        "What is Panadol used for?",
        "What are the indications for Lipitor?",
        "What does Claritine treat?",
        "Usage of Zyrtec",
        "What is Prozac used for?",
        "Tell me about Augmentin usage",
        
        # Arabic questions
        "ما هو استخدام البانادول؟",
        "ماذا يعالج الليبيتور؟",
        "استخدام الكلاريتين",
        "ما هي مؤشرات الزيرتك؟",
        
        # Short questions (should use context)
        "usage",
        "what is it used for",
        "indications"
    ]
    
    for question in usage_questions:
        response = send_chat_message(question)
        print_test_result("Usage Question", question, response)
        time.sleep(1)

def test_price_questions():
    """Test price-related questions."""
    print("\n🧪 TESTING PRICE QUESTIONS")
    
    price_questions = [
        # English questions
        "What is the price of Panadol?",
        "How much does Lipitor cost?",
        "Price of Zyrtec",
        "What's the cost of Prozac?",
        "Tell me the price of Augmentin",
        
        # Arabic questions
        "ما هو سعر البانادول؟",
        "كم تكلفة الليبيتور؟",
        "سعر الزيرتك",
        "بكام البروزاك؟",
        
        # Short questions (should use context)
        "price",
        "how much",
        "cost"
    ]
    
    for question in price_questions:
        response = send_chat_message(question)
        print_test_result("Price Question", question, response)
        time.sleep(1)

def test_active_ingredient_questions():
    """Test active ingredient questions."""
    print("\n🧪 TESTING ACTIVE INGREDIENT QUESTIONS")
    
    ingredient_questions = [
        # English questions
        "What is the active ingredient of Panadol?",
        "What are the ingredients in Lipitor?",
        "Active ingredient of Zyrtec",
        "What's in Claritine?",
        "Tell me about Prozac ingredients",
        
        # Arabic questions
        "ما هي المادة الفعالة في البانادول؟",
        "المكونات في الليبيتور",
        "المادة الفعالة للزيرتك",
        "ماذا يحتوي الكلاريتين؟",
        
        # Common misspellings
        "active ingredint",
        "ingerin",
        "what is in",
        
        # Short questions (should use context)
        "active ingredient",
        "ingredients",
        "what's in it"
    ]
    
    for question in ingredient_questions:
        response = send_chat_message(question)
        print_test_result("Active Ingredient Question", question, response)
        time.sleep(1)

def test_comparison_questions():
    """Test medicine comparison questions."""
    print("\n🧪 TESTING COMPARISON QUESTIONS")
    
    comparison_questions = [
        # English comparisons
        "What is the difference between Panadol and Advil?",
        "Compare Lipitor and Crestor",
        "Panadol versus Tylenol",
        "What's the difference between Zyrtec and Claritine?",
        "Compare Prozac and Zoloft",
        
        # Arabic comparisons
        "ما هو الفرق بين البانادول والأدفيل؟",
        "قارن الليبيتور والكريستور",
        "الفرق بين الزيرتك والكلاريتين",
        "بانادول مقابل تايلينول",
        
        # Different comparison formats
        "difference between metformin and glucophage",
        "augmentin vs amoxicillin",
        "voltaren and diclofenac comparison"
    ]
    
    for question in comparison_questions:
        response = send_chat_message(question)
        print_test_result("Comparison Question", question, response)
        time.sleep(1)

def test_context_maintenance():
    """Test that the system maintains context for follow-up questions."""
    print("\n🧪 TESTING CONTEXT MAINTENANCE")
    
    # Test conversation flow
    conversation_flow = [
        "What is Zyrtec used for?",
        "active ingredient",
        "price",
        "What about Lipitor?",
        "usage",
        "active ingredient",
        "price"
    ]
    
    user_id = "context_test_user"
    
    for i, question in enumerate(conversation_flow, 1):
        response = send_chat_message(question, user_id)
        print_test_result(f"Context Test {i}", question, response)
        time.sleep(1)

def test_misspelling_tolerance():
    """Test tolerance for common misspellings."""
    print("\n🧪 TESTING MISSPELLING TOLERANCE")
    
    misspelled_questions = [
        "What is zertic used for?",  # zertic -> zyrtec
        "Price of pndol",  # pndol -> panadol
        "Active ingredient of claritine",  # claritine -> claritin
        "Usage of prozac",  # prozac -> prozac (correct)
        "What does lipitor treat?",  # lipitor -> lipitor (correct)
    ]
    
    for question in misspelled_questions:
        response = send_chat_message(question)
        print_test_result("Misspelling Test", question, response)
        time.sleep(1)

def test_general_medicine_questions():
    """Test general medicine information questions."""
    print("\n🧪 TESTING GENERAL MEDICINE QUESTIONS")
    
    general_questions = [
        "Tell me about Panadol",
        "What is Lipitor?",
        "Information about Zyrtec",
        "Tell me more about Prozac",
        "What is Augmentin?",
        "Tell me about metformin",
        "What is rivo?",
        "Information about ozempic"
    ]
    
    for question in general_questions:
        response = send_chat_message(question)
        print_test_result("General Medicine Question", question, response)
        time.sleep(1)

def test_arabic_medicine_names():
    """Test Arabic medicine names and questions."""
    print("\n🧪 TESTING ARABIC MEDICINE NAMES")
    
    arabic_questions = [
        "ما هو استخدام البانادول؟",
        "سعر الليبيتور",
        "المادة الفعالة في الزيرتك",
        "ما هو الفرق بين البانادول والأدفيل؟",
        "استخدام الكلاريتين",
        "ما هي مؤشرات البروزاك؟",
        "تكلفة الأوجمنت",
        "ماذا يعالج الميتفورمين؟"
    ]
    
    for question in arabic_questions:
        response = send_chat_message(question)
        print_test_result("Arabic Medicine Question", question, response)
        time.sleep(1)

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🧪 TESTING EDGE CASES")
    
    edge_cases = [
        "",  # Empty question
        "   ",  # Whitespace only
        "xyz123",  # Non-medicine text
        "What is the price of nonexistentmedicine?",  # Non-existent medicine
        "Compare medicine1 and medicine2",  # Non-existent medicines
        "What is the active ingredient of fake_medicine?",  # Fake medicine
        "Thank you",  # Thanks
        "Goodbye",  # Goodbye
        "Bye"  # Short goodbye
    ]
    
    for question in edge_cases:
        response = send_chat_message(question)
        print_test_result("Edge Case", f"'{question}'", response)
        time.sleep(1)

def test_complex_questions():
    """Test complex and multi-part questions."""
    print("\n🧪 TESTING COMPLEX QUESTIONS")
    
    complex_questions = [
        "What is the price and usage of Panadol?",
        "Tell me about Lipitor - its usage, price, and active ingredient",
        "Compare Zyrtec and Claritine - their usage and prices",
        "What is the difference between Prozac and Zoloft in terms of usage and side effects?",
        "Give me information about Augmentin including price, usage, and ingredients"
    ]
    
    for question in complex_questions:
        response = send_chat_message(question)
        print_test_result("Complex Question", question, response)
        time.sleep(1)

def main():
    """Run all test categories."""
    print("🏥 EGYPTIAN MEDICINE TRACKER - CHAT SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/medicines", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly. Please make sure the server is running.")
            return
    except:
        print("❌ Cannot connect to server. Please make sure the server is running on localhost:5000")
        return
    
    print("✅ Server is running. Starting tests...")
    
    # Run all test categories
    test_greetings_and_help()
    test_usage_questions()
    test_price_questions()
    test_active_ingredient_questions()
    test_comparison_questions()
    test_context_maintenance()
    test_misspelling_tolerance()
    test_general_medicine_questions()
    test_arabic_medicine_names()
    test_edge_cases()
    test_complex_questions()
    
    print("\n🎉 ALL TESTS COMPLETED!")
    print("=" * 60)
    print("This test suite covers:")
    print("• Greetings and help requests")
    print("• Usage and indication questions")
    print("• Price questions")
    print("• Active ingredient questions")
    print("• Medicine comparisons")
    print("• Context maintenance")
    print("• Misspelling tolerance")
    print("• Arabic language support")
    print("• General medicine information")
    print("• Edge cases and error handling")
    print("• Complex multi-part questions")

if __name__ == "__main__":
    main()