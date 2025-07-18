#!/usr/bin/env python3
"""
Quick Reference: Types of Questions Your Chat System Can Handle

This script provides examples of different question types that your Egyptian Medicine Tracker
chat system can answer. You can use these examples to test the system or as a reference.

Run this script to see all the question types, or use individual functions to test specific categories.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
CHAT_ENDPOINT = f"{BASE_URL}/api/medicines/chat"

def send_chat_message(question: str, user_id: str = "example_user") -> dict:
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
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

def print_example(question: str, response: dict):
    """Print a question example and its response."""
    print(f"\n❓ QUESTION: {question}")
    if "error" in response:
        print(f"❌ ERROR: {response['error']}")
    else:
        print(f"✅ RESPONSE: {response.get('reply', 'No reply')}")
    print("-" * 50)

def show_usage_questions():
    """Show examples of usage/indication questions."""
    print("\n🏥 USAGE & INDICATION QUESTIONS")
    print("=" * 50)
    
    questions = [
        "What is Panadol used for?",
        "What are the indications for Lipitor?",
        "What does Zyrtec treat?",
        "Usage of Prozac",
        "ما هو استخدام البانادول؟",
        "ماذا يعالج الليبيتور؟",
        "usage",  # Short question using context
        "what is it used for"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_price_questions():
    """Show examples of price questions."""
    print("\n💰 PRICE QUESTIONS")
    print("=" * 50)
    
    questions = [
        "What is the price of Panadol?",
        "How much does Lipitor cost?",
        "Price of Zyrtec",
        "ما هو سعر البانادول؟",
        "كم تكلفة الليبيتور؟",
        "price",  # Short question using context
        "how much"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_active_ingredient_questions():
    """Show examples of active ingredient questions."""
    print("\n🧪 ACTIVE INGREDIENT QUESTIONS")
    print("=" * 50)
    
    questions = [
        "What is the active ingredient of Panadol?",
        "What are the ingredients in Lipitor?",
        "Active ingredient of Zyrtec",
        "ما هي المادة الفعالة في البانادول؟",
        "المكونات في الليبيتور",
        "active ingredient",  # Short question using context
        "active ingredint",  # Misspelling
        "what's in it"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_comparison_questions():
    """Show examples of comparison questions."""
    print("\n⚖️ COMPARISON QUESTIONS")
    print("=" * 50)
    
    questions = [
        "What is the difference between Panadol and Advil?",
        "Compare Lipitor and Crestor",
        "Panadol versus Tylenol",
        "ما هو الفرق بين البانادول والأدفيل؟",
        "قارن الليبيتور والكريستور",
        "difference between metformin and glucophage",
        "augmentin vs amoxicillin"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_context_examples():
    """Show examples of context maintenance."""
    print("\n🔄 CONTEXT MAINTENANCE EXAMPLES")
    print("=" * 50)
    
    # Test conversation flow
    conversation = [
        "What is Zyrtec used for?",
        "active ingredient",
        "price",
        "What about Lipitor?",
        "usage",
        "active ingredient"
    ]
    
    user_id = "context_demo"
    
    for i, question in enumerate(conversation, 1):
        print(f"\n--- Conversation Step {i} ---")
        response = send_chat_message(question, user_id)
        print_example(question, response)

def show_misspelling_examples():
    """Show examples of misspelling tolerance."""
    print("\n🔤 MISSPELLING TOLERANCE")
    print("=" * 50)
    
    questions = [
        "What is zertic used for?",  # zertic -> zyrtec
        "Price of pndol",  # pndol -> panadol
        "Active ingredient of claritine",  # claritine -> claritin
        "Usage of prozac",  # prozac -> prozac (correct)
        "What does lipitor treat?"  # lipitor -> lipitor (correct)
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_general_questions():
    """Show examples of general medicine questions."""
    print("\n💊 GENERAL MEDICINE QUESTIONS")
    print("=" * 50)
    
    questions = [
        "Tell me about Panadol",
        "What is Lipitor?",
        "Information about Zyrtec",
        "Tell me more about Prozac",
        "What is Augmentin?",
        "Tell me about metformin",
        "What is rivo?",
        "Information about ozempic"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_arabic_examples():
    """Show examples of Arabic language support."""
    print("\n🌍 ARABIC LANGUAGE SUPPORT")
    print("=" * 50)
    
    questions = [
        "ما هو استخدام البانادول؟",
        "سعر الليبيتور",
        "المادة الفعالة في الزيرتك",
        "ما هو الفرق بين البانادول والأدفيل؟",
        "استخدام الكلاريتين",
        "ما هي مؤشرات البروزاك؟",
        "تكلفة الأوجمنت",
        "ماذا يعالج الميتفورمين؟"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_greeting_examples():
    """Show examples of greetings and help."""
    print("\n👋 GREETINGS & HELP")
    print("=" * 50)
    
    questions = [
        "Hello",
        "Hi there",
        "مرحبا",
        "أهلا وسهلا",
        "What can you do?",
        "Help",
        "How can you help me?",
        "Thank you",
        "Goodbye"
    ]
    
    for question in questions:
        response = send_chat_message(question)
        print_example(question, response)

def show_all_examples():
    """Show all question examples."""
    print("🏥 EGYPTIAN MEDICINE TRACKER - CHAT EXAMPLES")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/medicines", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding. Please make sure the server is running.")
            return
    except:
        print("❌ Cannot connect to server. Please make sure the server is running on localhost:5000")
        return
    
    print("✅ Server is running. Showing examples...")
    
    show_greeting_examples()
    show_usage_questions()
    show_price_questions()
    show_active_ingredient_questions()
    show_comparison_questions()
    show_context_examples()
    show_misspelling_examples()
    show_general_questions()
    show_arabic_examples()
    
    print("\n🎉 ALL EXAMPLES COMPLETED!")
    print("=" * 60)

def show_question_categories():
    """Show a summary of all question categories."""
    print("\n📋 QUESTION CATEGORIES SUMMARY")
    print("=" * 60)
    
    categories = {
        "Usage & Indications": [
            "What is [medicine] used for?",
            "What are the indications for [medicine]?",
            "What does [medicine] treat?",
            "Usage of [medicine]",
            "ما هو استخدام [medicine]؟"
        ],
        "Price Questions": [
            "What is the price of [medicine]?",
            "How much does [medicine] cost?",
            "Price of [medicine]",
            "ما هو سعر [medicine]؟"
        ],
        "Active Ingredients": [
            "What is the active ingredient of [medicine]?",
            "What are the ingredients in [medicine]?",
            "Active ingredient of [medicine]",
            "ما هي المادة الفعالة في [medicine]؟"
        ],
        "Comparisons": [
            "What is the difference between [medicine1] and [medicine2]?",
            "Compare [medicine1] and [medicine2]",
            "ما هو الفرق بين [medicine1] و [medicine2]؟"
        ],
        "General Information": [
            "Tell me about [medicine]",
            "What is [medicine]?",
            "Information about [medicine]"
        ],
        "Context Questions": [
            "usage",  # Uses previous medicine context
            "price",  # Uses previous medicine context
            "active ingredient"  # Uses previous medicine context
        ],
        "Arabic Support": [
            "ما هو استخدام [medicine]؟",
            "سعر [medicine]",
            "المادة الفعالة في [medicine]"
        ],
        "Misspelling Tolerance": [
            "zertic -> zyrtec",
            "pndol -> panadol",
            "claritine -> claritin"
        ],
        "Greetings & Help": [
            "Hello", "Hi", "مرحبا",
            "What can you do?", "Help",
            "Thank you", "Goodbye"
        ]
    }
    
    for category, examples in categories.items():
        print(f"\n🔹 {category}:")
        for example in examples:
            print(f"   • {example}")
    
    print(f"\n{'='*60}")
    print("💡 TIP: You can ask questions in both English and Arabic!")
    print("💡 TIP: Short questions like 'price' or 'usage' will use context from previous questions.")
    print("💡 TIP: The system can handle common misspellings.")
    print("💡 TIP: You can compare medicines using 'difference between' or 'compare'.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        
        if category == "usage":
            show_usage_questions()
        elif category == "price":
            show_price_questions()
        elif category == "ingredients":
            show_active_ingredient_questions()
        elif category == "comparison":
            show_comparison_questions()
        elif category == "context":
            show_context_examples()
        elif category == "misspelling":
            show_misspelling_examples()
        elif category == "general":
            show_general_questions()
        elif category == "arabic":
            show_arabic_examples()
        elif category == "greetings":
            show_greeting_examples()
        elif category == "categories":
            show_question_categories()
        else:
            print("Available categories: usage, price, ingredients, comparison, context, misspelling, general, arabic, greetings, categories")
            print("Or run without arguments to see all examples.")
    else:
        show_all_examples() 