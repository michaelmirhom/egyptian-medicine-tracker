import re
from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.medicine import Medicine
from src.services.medicine_api import medicine_api
from src.services.rxnav_api import rxnav_api
from src.services.local_usage_db import get_local_usage
from src.services.usage_fallback import get_usage_generic, extract_generic_name_from_trade_name
from src.services.name_resolver import arabic_to_english, is_arabic_text
import json
import time
import random
import os
from langchain.agents import initialize_agent, Tool
from langchain_community.chat_models import ChatOpenAI
from langchain.tools import tool

medicine_bp = Blueprint('medicine', __name__)

def extract_base_medicine_name(full_name: str) -> str:
    """
    Extract the base medicine name from a full product name.
    This handles Arabic and English medicine names.
    
    Args:
        full_name (str): Full product name (e.g., "ريفو-ميكرو 320 مجم 30 قرص")
        
    Returns:
        str: Base medicine name (e.g., "rivo")
    """
    print(f"[DEBUG] [extract_base_medicine_name] Extracting from: '{full_name}'")
    
    # Common medicine name mappings for Arabic to English
    arabic_to_english = {
        'ريفو': 'rivo',
        'ريفو-ميكرو': 'rivo',
        'ريفو-مايكرو': 'rivo',
        'بانادول': 'panadol',
        'بنادول': 'panadol',  # Alternative Arabic spelling
        'باراسيتامول': 'paracetamol',
        'فولتارين': 'voltaren',
        'كونكور': 'concor',
        'ليبيتور': 'lipitor',
        'أوجمنتين': 'augmentin',
        'أموكسيسيلين': 'amoxicillin',
        'كلاريتين': 'claritine',  # Claritine in Arabic
        'كلاريتين': 'claritine',  # Alternative spelling
        'لوراتادين': 'loratadine',  # Generic name in Arabic
        'لوراتادين': 'loratadine',  # Alternative spelling
        'أليجرا': 'allegra',  # Allegra in Arabic
        'زيرتيك': 'zyrtec',  # Zyrtec in Arabic
        'بينادريل': 'benadryl',  # Benadryl in Arabic
        'أسبيرين': 'aspirin',  # Aspirin in Arabic
        'أيبوبروفين': 'ibuprofen',  # Ibuprofen in Arabic
        'أموكسيسيلين': 'amoxicillin',  # Amoxicillin in Arabic
        'أزيثروميسين': 'azithromycin',  # Azithromycin in Arabic
        'ديكلوفيناك': 'diclofenac',  # Diclofenac in Arabic
        'سيتريزين': 'cetirizine',  # Cetirizine in Arabic
        'أوميبرازول': 'omeprazole',  # Omeprazole in Arabic
        'ميتفورمين': 'metformin',  # Metformin in Arabic
    }
    
    # Convert to lowercase for matching
    name_lower = full_name.lower()
    
    # Check for Arabic medicine names first
    for arabic_name, english_name in arabic_to_english.items():
        if arabic_name.lower() in name_lower:
            print(f"[DEBUG] [extract_base_medicine_name] Found Arabic match: '{arabic_name}' -> '{english_name}'")
            return english_name
    
    # If no Arabic match, try to extract English medicine names
    # Common English medicine names to look for
    english_medicines = [
        'rivo', 'panadol', 'paracetamol', 'aspirin', 'ibuprofen',
        'augmentin', 'amoxicillin', 'azithromycin', 'voltaren', 'diclofenac',
        'concor', 'bisoprolol', 'lipitor', 'atorvastatin', 'cetirizine',
        'loratadine', 'omeprazole', 'pantoprazole', 'metformin', 'cataflam'
    ]
    
    for medicine in english_medicines:
        if medicine.lower() in name_lower:
            print(f"[DEBUG] [extract_base_medicine_name] Found English match: '{medicine}'")
            return medicine
    
    # If no specific medicine found, return the first word (common pattern)
    words = full_name.split()
    if words:
        first_word = words[0].lower()
        print(f"[DEBUG] [extract_base_medicine_name] Using first word: '{first_word}'")
        return first_word
    
    print(f"[DEBUG] [extract_base_medicine_name] No extraction possible, returning original: '{full_name}'")
    return full_name.lower()

def clean_medicine_name(medicine_name: str) -> str:
    """
    Clean medicine name by removing common prefixes and normalizing.
    
    Args:
        medicine_name (str): Raw medicine name
        
    Returns:
        str: Cleaned medicine name
    """
    print(f"[DEBUG] [clean_medicine_name] Cleaning: '{medicine_name}'")
    
    # Common prefixes to remove
    prefixes_to_remove = ['of ', 'the ', 'a ', 'an ', 'what is ', 'what\'s ', 'what are ', 'what is the ', 'what are the ']
    
    # Common phrases to remove that are not medicine names
    phrases_to_remove = [
        'brands of ', 'brand of ', 'brand name ', 'brand names of ',
        'what is the brands of ', 'what are the brands of ',
        'what is the brand name of ', 'what are the brand names of ',
        'usage of ', 'used for ', 'indication of ', 'purpose of ',
        'price of ', 'cost of ', 'how much is ', 'how much does '
    ]
    
    cleaned_name = medicine_name.lower().strip()
    
    # Remove phrases first
    for phrase in phrases_to_remove:
        if cleaned_name.startswith(phrase):
            cleaned_name = cleaned_name[len(phrase):].strip()
            print(f"[DEBUG] [clean_medicine_name] Removed phrase '{phrase}' -> '{cleaned_name}'")
    
    # Then remove prefixes
    for prefix in prefixes_to_remove:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix):].strip()
            print(f"[DEBUG] [clean_medicine_name] Removed prefix '{prefix}' -> '{cleaned_name}'")
    
    # Remove common words that are not medicine names
    common_words_to_remove = ['brands', 'brand', 'names', 'name', 'contain', 'contains', 'usage', 'used', 'indication', 'purpose', 'price', 'cost']
    words = cleaned_name.split()
    filtered_words = [word for word in words if word.lower() not in common_words_to_remove]
    cleaned_name = ' '.join(filtered_words).strip()
    
    print(f"[DEBUG] [clean_medicine_name] Final cleaned name: '{cleaned_name}'")
    return cleaned_name

@medicine_bp.route('/medicines', methods=['GET'])
def get_medicines():
    """Get all medicines from the database"""
    medicines = Medicine.query.all()
    return jsonify([medicine.to_dict() for medicine in medicines])

@medicine_bp.route('/medicines/search', methods=['GET'])
def search_medicines():
    """Search medicines by name in local database"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    medicines = Medicine.query.filter(
        Medicine.trade_name.contains(query) | 
        Medicine.generic_name.contains(query)
    ).all()
    
    return jsonify([medicine.to_dict() for medicine in medicines])

@medicine_bp.route('/medicines/api-search', methods=['GET'])
def api_search_medicines():
    """Search medicines using external API for real-time data"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    # Get real-time data from external API
    success, products, error = medicine_api.search_and_get_details(query)
    
    if not success:
        return jsonify({'error': error}), 500
    
    # Format the response
    formatted_products = []
    for product in products:
        # Get usage information using the fallback chain
        product_name = product.get('name', '')
        generic_name = extract_generic_name_from_trade_name(product_name)
        usage_info = get_usage_generic(product_name, generic_name)
        
        # If no usage found, try with the original search query
        if not usage_info:
            usage_info = get_usage_generic(query, generic_name)
        
        # If still no usage, fall back to local database
        if not usage_info:
            try:
                local_usage = get_local_usage(query)
                if local_usage:
                    usage_info = local_usage
            except Exception as e:
                pass
        
        # Final fallback
        if not usage_info:
            usage_info = "Usage information not available"
        
        formatted_product = {
            'id': product.get('id'),
            'trade_name': product.get('name', ''),
            'price': product.get('price'),
            'currency': 'EGP',
            'image': product.get('image'),
            'description': product.get('desc', ''),
            'components': product.get('components', []),
            'company': product.get('company', ''),
            'usage': usage_info,  # Add usage information
            'source': 'External API',
            'last_updated': time.time()
        }
        formatted_products.append(formatted_product)
    
    return jsonify({
        'success': True,
        'products': formatted_products,
        'count': len(formatted_products)
    })



@medicine_bp.route('/medicines/api-sync', methods=['POST'])
def sync_medicine_from_api():
    """Sync a medicine from external API to local database"""
    data = request.get_json()
    medicine_name = data.get('name', '')
    
    if not medicine_name:
        return jsonify({'error': 'Medicine name is required'}), 400
    
    # Search for medicine in external API
    success, products, error = medicine_api.search_and_get_details(medicine_name)
    
    if not success:
        return jsonify({'error': error}), 500
    
    if not products:
        return jsonify({'error': 'No medicines found with that name'}), 404
    
    # Use the first result
    product = products[0]
    
    # Check if medicine already exists in database
    existing_medicine = Medicine.query.filter_by(api_id=product.get('id')).first()
    
    if existing_medicine:
        # Update existing medicine
        existing_medicine.trade_name = product.get('name', existing_medicine.trade_name)
        existing_medicine.price = product.get('price', existing_medicine.price)
        existing_medicine.api_image = product.get('image', existing_medicine.api_image)
        existing_medicine.api_description = product.get('desc', existing_medicine.api_description)
        existing_medicine.api_components = json.dumps(product.get('components', []))
        existing_medicine.api_company = product.get('company', existing_medicine.api_company)
        
        # Get usage information from RxNav API
        try:
            success, drug_info, error = rxnav_api.get_drug_info(product.get('name', ''))
            if success and drug_info.get('usage_text'):
                existing_medicine.api_usage = drug_info['usage_text']
        except Exception as e:
            # If RxNav fails, keep existing usage info
            pass
        
        existing_medicine.last_updated = db.func.now()
        existing_medicine.source = 'External API'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Medicine updated successfully',
            'medicine': existing_medicine.to_dict()
        })
    else:
        # Create new medicine
        # Get usage information from RxNav API
        usage_info = None
        try:
            success, drug_info, error = rxnav_api.get_drug_info(product.get('name', ''))
            if success and drug_info.get('usage_text'):
                usage_info = drug_info['usage_text']
        except Exception as e:
            # If RxNav fails, continue without usage info
            pass
        
        new_medicine = Medicine(
            trade_name=product.get('name', ''),
            price=product.get('price'),
            api_id=product.get('id'),
            api_image=product.get('image'),
            api_description=product.get('desc'),
            api_components=json.dumps(product.get('components', [])),
            api_company=product.get('company'),
            api_usage=usage_info,
            source='External API'
        )
        
        db.session.add(new_medicine)
        db.session.commit()
        
        return jsonify({
            'message': 'Medicine added successfully',
            'medicine': new_medicine.to_dict()
        }), 201

@medicine_bp.route('/medicines', methods=['POST'])
def add_medicine():
    """Add a new medicine to the database"""
    data = request.get_json()
    
    if not data or 'trade_name' not in data:
        return jsonify({'error': 'trade_name is required'}), 400
    
    medicine = Medicine(
        trade_name=data['trade_name'],
        generic_name=data.get('generic_name'),
        reg_no=data.get('reg_no'),
        applicant=data.get('applicant'),
        price=data.get('price'),
        currency=data.get('currency', 'EGP'),
        source=data.get('source')
    )
    
    db.session.add(medicine)
    db.session.commit()
    
    return jsonify(medicine.to_dict()), 201

@medicine_bp.route('/medicines/<int:medicine_id>', methods=['PUT'])
def update_medicine(medicine_id):
    """Update medicine price and information"""
    medicine = Medicine.query.get_or_404(medicine_id)
    data = request.get_json()
    
    if 'trade_name' in data:
        medicine.trade_name = data['trade_name']
    if 'generic_name' in data:
        medicine.generic_name = data['generic_name']
    if 'reg_no' in data:
        medicine.reg_no = data['reg_no']
    if 'applicant' in data:
        medicine.applicant = data['applicant']
    if 'price' in data:
        medicine.price = data['price']
    if 'currency' in data:
        medicine.currency = data['currency']
    if 'source' in data:
        medicine.source = data['source']
    
    medicine.last_updated = db.func.now()
    db.session.commit()
    
    return jsonify(medicine.to_dict())

@medicine_bp.route('/medicines/<int:medicine_id>', methods=['DELETE'])
def delete_medicine(medicine_id):
    """Delete a medicine from the database"""
    medicine = Medicine.query.get_or_404(medicine_id)
    db.session.delete(medicine)
    db.session.commit()
    
    return jsonify({'message': 'Medicine deleted successfully'})

@medicine_bp.route('/medicines/refresh-prices', methods=['POST'])
def refresh_prices():
    """Refresh prices for medicines using external API"""
    medicines = Medicine.query.filter(Medicine.api_id.isnot(None)).all()
    updated_count = 0
    errors = []
    
    for medicine in medicines:
        try:
            # Get updated information from API
            success, details, error = medicine_api.get_medicine_details(medicine.api_id)
            
            if success and details:
                # Update medicine with new data
                medicine.trade_name = details.get('name', medicine.trade_name)
                medicine.price = details.get('price', medicine.price)
                medicine.api_image = details.get('image', medicine.api_image)
                medicine.api_description = details.get('desc', medicine.api_description)
                medicine.api_components = json.dumps(details.get('components', []))
                medicine.api_company = details.get('company', medicine.api_company)
                
                # Get usage information from RxNav API
                try:
                    success, drug_info, error = rxnav_api.get_drug_info(medicine.trade_name)
                    if success and drug_info.get('usage_text'):
                        medicine.api_usage = drug_info['usage_text']
                except Exception as e:
                    # If RxNav fails, keep existing usage info
                    pass
                
                medicine.last_updated = db.func.now()
                updated_count += 1
            else:
                errors.append(f"Failed to update {medicine.trade_name}: {error}")
            
            # Add delay to be respectful to the API
            time.sleep(0.3)
            
        except Exception as e:
            errors.append(f"Error updating {medicine.trade_name}: {str(e)}")
    
    db.session.commit()
    
    return jsonify({
        'message': f'Refreshed prices for {updated_count} medicines',
        'updated_count': updated_count,
        'errors': errors
    })

@medicine_bp.route('/medicines/api-details/<medicine_id>', methods=['GET'])
def get_medicine_api_details(medicine_id):
    """Get detailed information about a medicine from external API"""
    success, details, error = medicine_api.get_medicine_details(medicine_id)
    
    if not success:
        return jsonify({'error': error}), 500
    
    if not details:
        return jsonify({'error': 'Medicine not found'}), 404
    
    return jsonify({
        'success': True,
        'medicine': details
    })

@medicine_bp.route('/medicines/sample-data', methods=['POST'])
def add_sample_data():
    """Add sample Egyptian medicines data"""
    sample_medicines = [
        {
            'trade_name': 'Panadol',
            'generic_name': 'Paracetamol',
            'reg_no': 'EG-12345',
            'applicant': 'GSK Egypt',
            'price': 15.50,
            'source': 'Sample Data'
        },
        {
            'trade_name': 'Augmentin',
            'generic_name': 'Amoxicillin/Clavulanic Acid',
            'reg_no': 'EG-23456',
            'applicant': 'GSK Egypt',
            'price': 85.00,
            'source': 'Sample Data'
        },
        {
            'trade_name': 'Voltaren',
            'generic_name': 'Diclofenac',
            'reg_no': 'EG-34567',
            'applicant': 'Novartis Egypt',
            'price': 25.75,
            'source': 'Sample Data'
        },
        {
            'trade_name': 'Concor',
            'generic_name': 'Bisoprolol',
            'reg_no': 'EG-45678',
            'applicant': 'Merck Egypt',
            'price': 45.00,
            'source': 'Sample Data'
        },
        {
            'trade_name': 'Lipitor',
            'generic_name': 'Atorvastatin',
            'reg_no': 'EG-56789',
            'applicant': 'Pfizer Egypt',
            'price': 120.00,
            'source': 'Sample Data'
        }
    ]
    
    added_count = 0
    for med_data in sample_medicines:
        # Check if medicine already exists
        existing = Medicine.query.filter_by(trade_name=med_data['trade_name']).first()
        if not existing:
            medicine = Medicine(**med_data)
            db.session.add(medicine)
            added_count += 1
    
    db.session.commit()
    
    return jsonify({
        'message': f'Added {added_count} sample medicines',
        'added_count': added_count
    })

# Global conversation memory (in production, use Redis or database)
conversation_context = {}

@medicine_bp.route('/medicines/chat', methods=['POST'])
def crewai_chat():
    """
    CrewAI-powered chat endpoint with persistent memory.
    Accepts: {"message": "<user text>", "question": "<user text>", "user_id": "<id>"}
    Returns: {"reply": "<bot answer>"}
    """
    data = request.get_json()
    print(f"[DEBUG] Raw data: {data}")  # Debug print for raw POST data
    question = (data.get("message") or data.get("question") or "").strip() if data else ''
    user_id = data.get("user_id", "default") if data else 'default'
    print(f"[DEBUG] Received chat: {question} from {user_id}")  # Debug print
    if not question:
        print("[DEBUG] No question provided.")
        return jsonify({"reply": "Please enter a message."})
    reply = answer_medicine_question(question, user_id)
    print(f"[DEBUG] Final reply: {reply}")  # Debug print
    return jsonify({"reply": reply})


def get_medicine_usage(medicine_name):
    usage = get_local_usage(medicine_name)
    if usage:
        return f"{medicine_name.title()} is used for: {usage}"
    # Try RxNav
    success, drug_info, error = rxnav_api.get_drug_info(medicine_name)
    if success and drug_info.get('usage_text') and drug_info['usage_text'] != 'Usage information not available':
        return f"{medicine_name.title()} is used for: {drug_info['usage_text']}"
    return f"Sorry, I couldn't find usage information for {medicine_name.title()}."

def get_medicine_price(medicine_name):
    success, products, error = medicine_api.search_and_get_details(medicine_name)
    if success and products:
        product = products[0]
        name = product.get('name', medicine_name.title())
        price = product.get('price', None)
        currency = 'EGP'
        if price:
            return f"The price of {name} is {price} {currency}."
        else:
            return f"Sorry, I couldn't find the price for {name}."
    return f"Sorry, I couldn't find any information for {medicine_name.title()}."

# Define LangChain tools
usage_tool = Tool(
    name="GetMedicineUsage",
    func=get_medicine_usage,
    description="Get the usage/indications for a medicine. Input should be the medicine name."
)
price_tool = Tool(
    name="GetMedicinePrice",
    func=get_medicine_price,
    description="Get the price for a medicine. Input should be the medicine name."
)

def answer_medicine_question(question: str, user_id: str = 'default') -> str:
    """Intelligent medicine Q&A system that can handle various types of questions."""
    global conversation_context
    print(f"[DEBUG] answer_medicine_question called with question='{question}', user_id='{user_id}'")

    # Store original question
    original_question = question.strip()
    question_lower = question.lower().strip()
    print(f"[DEBUG] Normalized question: '{question_lower}'")
    
    # Get user's conversation context
    user_context = conversation_context.get(user_id, {})
    last_medicine = user_context.get('last_medicine', None)
    variants = user_context.get('variants', [])
    print(f"[DEBUG] User context: last_medicine={last_medicine}, variants_count={len(variants)}")
    
    # Handle variant selection by number
    if variants and question_lower.isdigit():
        variant_index = int(question_lower) - 1
        print(f"[DEBUG] User selected variant index: {variant_index}")
        if 0 <= variant_index < len(variants):
            selected_product = variants[variant_index]
            name = selected_product.get('name', 'Unknown')
            price = selected_product.get('price', 'N/A')
            currency = 'EGP'
            print(f"[DEBUG] Selected product: {selected_product}")
            
            # Extract base medicine name for usage lookup
            base_medicine_name = extract_base_medicine_name(name)
            print(f"[DEBUG] Extracted base medicine name: '{base_medicine_name}' from full name: '{name}'")
            
            # Update context
            conversation_context[user_id]['last_medicine'] = base_medicine_name
            conversation_context[user_id]['selected_variant'] = selected_product
            conversation_context[user_id]['full_variant_name'] = name
            print(f"[DEBUG] Updated context with selected variant: {name}, base name: {base_medicine_name}")
            return f"**{name}** costs **{price} {currency}**.\n\nYou can now ask:\n• 'What is the usage?' (for this variant)\n• 'Tell me more about it'\n• Or ask about another medicine"
    
    # Handle greetings and general conversation (English and Arabic)
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you']
    arabic_greetings = ['مرحبا', 'أهلا', 'السلام عليكم', 'صباح الخير', 'مساء الخير']
    
    if (any(greeting in question_lower for greeting in greetings) or 
        any(greeting in original_question for greeting in arabic_greetings)):
        print("[DEBUG] Greeting detected.")
        return "Hello! I'm your medicine assistant. I can help you with:\n• Medicine usage and indications\n• Medicine prices\n• General medicine information\n\nWhat would you like to know?"
    
    # Handle thanks and goodbyes
    thanks = ['thank', 'thanks', 'bye', 'goodbye', 'see you']
    if any(thank in question_lower for thank in thanks):
        print("[DEBUG] Thanks/goodbye detected.")
        return "You're welcome! Feel free to ask me anything about medicines anytime. Have a great day!"
    
    # Handle help requests
    if 'help' in question_lower or 'what can you do' in question_lower:
        print("[DEBUG] Help request detected.")
        return "I'm your medicine assistant! I can help you with:\n\n• **Usage Questions**: 'What is Panadol used for?' or 'What are the indications for Augmentin?'\n• **Price Questions**: 'What's the price of Voltaren?' or 'How much does Concor cost?'\n• **Comparison Questions**: 'What's the difference between Tylenol and Advil?'\n• **Administration Questions**: 'How should I take metformin?'\n• **General Info**: 'Tell me about Lipitor' or 'What is Rivo?'\n\nJust ask me anything about medicines!"
    
    # Classify question type and extract medicine names
    question_info = classify_question_and_extract_medicines(original_question, question_lower, last_medicine)
    
    if not question_info:
        print(f"[DEBUG] Could not classify question or extract medicine names.")
        return "I'm here to help with medicine questions! Please specify a medicine name.\n\n**Examples:**\n• **Usage**: 'What is Panadol used for?' or 'What are the indications for Augmentin?'\n• **Price**: 'What's the price of Voltaren?' or 'How much does Concor cost?'\n• **Comparison**: 'What's the difference between Tylenol and Advil?'\n• **Administration**: 'How should I take metformin?'\n\n**Popular medicines:** Panadol, Augmentin, Voltaren, Concor, Lipitor, Rivo"
    
    question_type = question_info['type']
    medicines = question_info['medicines']
    
    print(f"[DEBUG] Question type: {question_type}, Medicines: {medicines}")
    
    # Process based on question type
    if question_type == 'comparison':
        return handle_comparison_question(medicines)
    elif question_type == 'compound':
        return handle_compound_question(medicines[0], user_id)
    elif question_type == 'usage':
        return handle_usage_question(medicines[0], user_id)
    elif question_type == 'price':
        return handle_price_question(medicines[0], user_id)
    elif question_type == 'administration':
        return handle_administration_question(medicines[0])
    elif question_type == 'category':
        return handle_category_question(medicines[0])
    elif question_type == 'ingredients':
        return handle_ingredients_question(medicines[0])
    elif question_type == 'warnings':
        return handle_warnings_question(medicines[0])
    elif question_type == 'special_populations':
        return handle_special_populations_question(medicines[0])
    else:
        return handle_general_question(medicines[0], user_id)

def classify_question_and_extract_medicines(original_question: str, question_lower: str, last_medicine: str = None):
    """Classify question type and extract medicine names."""
    
    # Check for comparison questions first (English and Arabic)
    english_comparison_patterns = ['difference between', 'diiference between', 'compare', 'versus', 'vs']
    arabic_comparison_patterns = ['الفرق بين', 'فرق بين', 'مقارنة بين', 'مقارنة']
    
    # Check for "between X and Y" pattern
    has_between_and = 'between' in question_lower and ' and ' in question_lower
    
    is_comparison = (any(phrase in question_lower for phrase in english_comparison_patterns) or
                    any(phrase in original_question for phrase in arabic_comparison_patterns) or
                    has_between_and)
    
    if is_comparison:
        medicines = extract_medicines_from_comparison(original_question, question_lower)
        if len(medicines) >= 2:
            return {'type': 'comparison', 'medicines': medicines}
    
    # Check for administration questions
    if any(phrase in question_lower for phrase in ['how should i take', 'how to take', 'how do i take', 'dosage', 'administration']):
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'administration', 'medicines': [medicine]}
    
    # Check for active ingredient questions
    if any(phrase in question_lower for phrase in ['active ingredient', 'main ingredient', 'what ingredient', 'contains what']) or \
       any(phrase in original_question for phrase in ['المادة الفعالة', 'المكونات النشطة', 'يحتوي على']):
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'ingredients', 'medicines': [medicine]}
    
    # Check for contraindication/warning questions
    if any(phrase in question_lower for phrase in ['who should not', 'should not take', 'contraindication', 'warning', 'side effect', 'avoid']) or \
       any(phrase in original_question for phrase in ['من لا يجب', 'لا يجب أن', 'تحذيرات', 'آثار جانبية', 'تجنب']):
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'warnings', 'medicines': [medicine]}
    
    # Check for pregnancy/pediatric questions
    if any(phrase in question_lower for phrase in ['pregnant', 'pregnancy', 'children', 'pediatric', 'kids', 'child']) or \
       any(phrase in original_question for phrase in ['الحمل', 'الحامل', 'الأطفال', 'للأطفال', 'طفل']):
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'special_populations', 'medicines': [medicine]}
    
    # Check for category questions
    if any(phrase in question_lower for phrase in ['what are', 'used for']) and any(word in question_lower for word in ['antihistamines', 'antibiotics', 'painkillers', 'antidepressants']):
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'category', 'medicines': [medicine]}
    
    # Check for compound questions (usage and price) - English and Arabic
    # Must have explicit usage AND price keywords, not just "what is"
    has_explicit_usage_keywords = (any(word in question_lower for word in ['usage', 'used for', 'indication', 'purpose']) or
                                  any(word in original_question for word in ['استخدام', 'استعمال', 'يستخدم']))
    has_price_keywords = (any(word in question_lower for word in ['price', 'cost', 'how much']) or
                         any(word in original_question for word in ['سعر', 'ثمن', 'كم سعر', 'كم ثمن']))
    
    if has_explicit_usage_keywords and has_price_keywords:
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'compound', 'medicines': [medicine]}
    
    # Check for price questions
    if has_price_keywords:
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'price', 'medicines': [medicine]}
    
    # Check for usage questions
    has_usage_keywords = (any(word in question_lower for word in ['usage', 'used for', 'indication', 'purpose', 'what is', 'what\'s']) or
                         any(word in original_question for word in ['استخدام', 'استعمال', 'ما هو', 'يستخدم']))
    
    if has_usage_keywords:
        medicine = extract_single_medicine(original_question, question_lower, last_medicine)
        if medicine:
            return {'type': 'usage', 'medicines': [medicine]}
    
    # Default: try to extract any medicine name
    medicine = extract_single_medicine(original_question, question_lower, last_medicine)
    if medicine:
        return {'type': 'general', 'medicines': [medicine]}
    
    return None

def extract_medicines_from_comparison(original_question: str, question_lower: str):
    """Extract medicine names from comparison questions."""
    medicines = []
    
    # First, check for Arabic medicine names
    arabic_to_english = {
        'كلاريتين': 'claritine',
        'لوراتادين': 'loratadine',
        'بانادول': 'panadol',
        'ريفو': 'rivo',
        'فولتارين': 'voltaren',
        'كونكور': 'concor',
        'ليبيتور': 'lipitor',
        'أوجمنتين': 'augmentin',
        'أموكسيسيلين': 'amoxicillin',
        'ميتفورمين': 'metformin',
        'أسبيرين': 'aspirin',
        'أيبوبروفين': 'ibuprofen',
        'باراسيتامول': 'paracetamol',
        'أسيترامينوفين': 'acetaminophen',
        'تايلينول': 'tylenol',
        'أدفيل': 'advil',
        'بروفين': 'brufen',
        'موترين': 'motrin',
        'زانتاك': 'zantac',
        'رانتاج': 'rantag',
        'رانيتين': 'ranitin',
        'بريلوسيك': 'prilosec',
        'لوسيك': 'losec',
        'جلوكوفاج': 'glucophage',
        'سيدوفاج': 'cidophage',
        'نورفاسك': 'norvasc',
        'أملور': 'amlor',
        'زيرتيك': 'zyrtec',
        'أليريد': 'alerid',
        'كاتافلام': 'cataflam',
        'أوزيمبك': 'ozempic',
        'دوكسيسايكلين': 'doxycycline',
        'أموكسيسيلين': 'amoxicillin'
    }
    
    for arabic_name, english_name in arabic_to_english.items():
        if arabic_name in original_question:
            medicines.append(english_name)
    
    # Common English medicine names to look for
    common_medicines = [
        'tylenol', 'advil', 'panadol', 'aspirin', 'ibuprofen', 'acetaminophen',
        'paracetamol', 'voltaren', 'diclofenac', 'lipitor', 'atorvastatin',
        'concor', 'bisoprolol', 'augmentin', 'amoxicillin', 'claritine', 'claritin',
        'loratadine', 'metformin', 'prozac', 'fluoxetine', 'zoloft', 'sertraline',
        'brufen', 'motrin', 'zantac', 'rantag', 'ranitin', 'prilosec', 'losec',
        'glucophage', 'cidophage', 'norvasc', 'amlor', 'zyrtec', 'alerid', 'rivo', 'cataflam',
        'doxycycline', 'azithromycin', 'ciprofloxacin'
    ]
    
    # Look for medicines in the question
    for medicine in common_medicines:
        if medicine in question_lower:
            medicines.append(medicine)
    
    # Remove duplicates and return
    return list(set(medicines))

def extract_single_medicine(original_question: str, question_lower: str, last_medicine: str = None):
    """Extract a single medicine name from the question."""
    
    # First, check for Arabic medicine names
    arabic_to_english = {
        'كلاريتين': 'claritine',
        'لوراتادين': 'loratadine',
        'بانادول': 'panadol',
        'ريفو': 'rivo',
        'فولتارين': 'voltaren',
        'كونكور': 'concor',
        'ليبيتور': 'lipitor',
        'أوجمنتين': 'augmentin',
        'أموكسيسيلين': 'amoxicillin',
        'ميتفورمين': 'metformin',
        'أسبيرين': 'aspirin',
        'أيبوبروفين': 'ibuprofen',
        'باراسيتامول': 'paracetamol',
        'أسيترامينوفين': 'acetaminophen',
        'تايلينول': 'tylenol',
        'أدفيل': 'advil',
        'بروفين': 'brufen',
        'موترين': 'motrin',
        'زانتاك': 'zantac',
        'رانتاج': 'rantag',
        'رانيتين': 'ranitin',
        'بريلوسيك': 'prilosec',
        'لوسيك': 'losec',
        'جلوكوفاج': 'glucophage',
        'سيدوفاج': 'cidophage',
        'نورفاسك': 'norvasc',
        'أملور': 'amlor',
        'زيرتيك': 'zyrtec',
        'أليريد': 'alerid',
        'كاتافلام': 'cataflam',
        'أوزيمبك': 'ozempic',
        'دوكسيسايكلين': 'doxycycline',
        'أموكسيسيلين': 'amoxicillin'
    }
    
    for arabic_name, english_name in arabic_to_english.items():
        if arabic_name in original_question:
            print(f"[DEBUG] Found Arabic medicine: '{arabic_name}' -> '{english_name}'")
            return english_name
    
    # Look for common medicine names in the current question FIRST
    common_medicines = [
        'tylenol', 'advil', 'panadol', 'aspirin', 'ibuprofen', 'acetaminophen',
        'paracetamol', 'voltaren', 'diclofenac', 'lipitor', 'atorvastatin',
        'concor', 'bisoprolol', 'augmentin', 'amoxicillin', 'claritine', 'claritin',
        'loratadine', 'metformin', 'prozac', 'fluoxetine', 'zoloft', 'sertraline',
        'ozempic', 'semaglutide', 'humalog', 'lantus', 'zoloft', 'xarelto',
        'brufen', 'motrin', 'zantac', 'rantag', 'ranitin', 'prilosec', 'losec',
        'glucophage', 'cidophage', 'norvasc', 'amlor', 'zyrtec', 'alerid', 'rivo', 'cataflam',
        'doxycycline', 'azithromycin', 'ciprofloxacin'
    ]
    
    for medicine in common_medicines:
        if medicine in question_lower:
            print(f"[DEBUG] Found medicine in question: '{medicine}'")
            return medicine
    
    # Try to extract from words in the question - only exact matches
    words = question_lower.split()
    for word in words:
        # Clean the word
        clean_word = re.sub(r'[?.,!]', '', word.lower())
        if len(clean_word) >= 3:
            # Check if it's a known medicine - only exact matches, not partial
            from src.services.local_usage_db import get_local_usage_exact
            usage = get_local_usage_exact(clean_word)
            if usage:
                print(f"[DEBUG] Found medicine by exact local usage: '{clean_word}'")
                return clean_word
    
    # ONLY use context if no medicine found in current question AND it's a generic question
    if last_medicine and is_generic_question(question_lower):
        print(f"[DEBUG] Using last_medicine from context: '{last_medicine}'")
        return last_medicine
    
    return None

def is_generic_question(question_lower: str):
    """Check if this is a generic question that should use context."""
    # Simple patterns for generic questions
    generic_patterns = [
        'what is the usage',
        'what is the price', 
        'what is usage',
        'what is price',
        'the usage',
        'the price',
        'usage',
        'price'
    ]
    
    # Check if the question matches any generic pattern
    for pattern in generic_patterns:
        if pattern in question_lower:
            return True
    
    return False

def handle_comparison_question(medicines):
    """Handle comparison questions between medicines."""
    if len(medicines) < 2:
        return "I need at least two medicines to compare. Please specify which medicines you'd like to compare."
    
    responses = []
    for medicine in medicines[:2]:  # Limit to 2 medicines for comparison
        usage = get_usage_for_medicine(medicine)
        if usage:
            responses.append(f"**{medicine.title()}**: {usage}")
        else:
            responses.append(f"**{medicine.title()}**: Usage information not available")
    
    if len(responses) == 2:
        return f"Here's a comparison between **{medicines[0].title()}** and **{medicines[1].title()}**:\n\n{responses[0]}\n\n{responses[1]}"
    else:
        return "\n\n".join(responses)

def handle_usage_question(medicine, user_id):
    """Handle usage questions for a single medicine."""
    usage = get_usage_for_medicine(medicine)
    
    # Update context
    conversation_context[user_id] = {
        'last_medicine': medicine,
        'last_question_type': 'usage'
    }
    
    if usage:
        return f"**{medicine.title()}** is used for: {usage}"
    else:
        return f"Sorry, I couldn't find usage information for **{medicine.title()}**. You can try:\n• Asking about its price: 'What's the price of {medicine.title()}?'\n• Asking about a different medicine"

def handle_price_question(medicine, user_id):
    """Handle price questions for a single medicine."""
    print(f"[DEBUG] Querying external API for price of '{medicine}'")
    success, products, error = medicine_api.search_and_get_details(medicine)
    print(f"[DEBUG] External API result: success={success}, products_count={len(products) if products else 0}, error={error}")
    
    # Update context
    conversation_context[user_id] = {
        'last_medicine': medicine,
        'last_question_type': 'price'
    }
    
    if success and products:
        if len(products) > 1:
            variants_text = "\n".join([f"• **{i+1}.** {product.get('name', 'Unknown')} - {product.get('price', 'N/A')} EGP" for i, product in enumerate(products[:5])])
            conversation_context[user_id]['variants'] = products
            conversation_context[user_id]['medicine_name'] = medicine
            print(f"[DEBUG] Multiple variants found for '{medicine}': {len(products)} variants")
            return f"I found **{len(products)} variants** of **{medicine.title()}**:\n\n{variants_text}\n\n**Please specify which one you want:**\n• Say the number (1, 2, 3...)\n• Or ask about a specific variant by name"
        else:
            product = products[0]
            name = product.get('name', medicine.title())
            price = product.get('price', None)
            currency = 'EGP'
            print(f"[DEBUG] Single product found: {product}")
            if price:
                return f"The price of **{name}** is **{price} {currency}**."
            else:
                print(f"[DEBUG] No price found for '{name}' in product data.")
                return f"Sorry, I couldn't find the price for **{name}**. You can try:\n• Asking about its usage: 'What is {name} used for?'\n• Asking about a different medicine"
    
    print(f"[DEBUG] No products found for '{medicine}' in external API.")
    return f"Sorry, I couldn't find any information for **{medicine.title()}**. You can try:\n• Asking about its usage: 'What is {medicine.title()} used for?'\n• Asking about a different medicine\n\n**Popular medicines:** Panadol, Augmentin, Voltaren, Concor, Lipitor, Rivo"

def handle_compound_question(medicine, user_id):
    """Handle compound questions (usage and price)."""
    # Get usage information
    usage = get_usage_for_medicine(medicine)
    
    # Get price information
    print(f"[DEBUG] Querying external API for price of '{medicine}'")
    success, products, error = medicine_api.search_and_get_details(medicine)
    print(f"[DEBUG] External API result: success={success}, products_count={len(products) if products else 0}, error={error}")
    
    # Update context
    conversation_context[user_id] = {
        'last_medicine': medicine,
        'last_question_type': 'compound'
    }
    
    response = f"**{medicine.title()}** information:\n\n"
    
    # Add usage information
    if usage:
        response += f"**Usage**: {usage}\n\n"
    else:
        response += f"**Usage**: Usage information not available\n\n"
    
    # Add price information
    if success and products:
        if len(products) == 1:
            product = products[0]
            name = product.get('name', 'Unknown')
            price = product.get('price', 'N/A')
            currency = 'EGP'
            response += f"**Price**: {name} costs {price} {currency}"
        else:
            # Multiple variants found
            conversation_context[user_id]['variants'] = products
            response += f"**Price**: I found {len(products)} variants:\n"
            for i, product in enumerate(products[:3], 1):  # Show first 3 variants
                name = product.get('name', 'Unknown')
                price = product.get('price', 'N/A')
                currency = 'EGP'
                response += f"• **{i}.** {name} - {price} {currency}\n"
            
            if len(products) > 3:
                response += f"• ... and {len(products) - 3} more variants\n"
            
            response += f"\n**Please specify which variant you want for more details**"
    else:
        response += f"**Price**: Price information not available"
    
    return response

def handle_administration_question(medicine):
    """Handle administration questions."""
    usage = get_usage_for_medicine(medicine)
    if usage:
        return f"**{medicine.title()}** is used for: {usage}\n\n**Administration**: Please consult your healthcare provider for specific dosage instructions, as they depend on your condition and medical history."
    else:
        return f"Sorry, I couldn't find information for **{medicine.title()}**. Please consult your healthcare provider for administration instructions."

def handle_category_question(medicine):
    """Handle category questions."""
    usage = get_usage_for_medicine(medicine)
    if usage:
        return f"**{medicine.title()}** is used for: {usage}"
    else:
        return f"Sorry, I couldn't find information for **{medicine.title()}**."

def handle_general_question(medicine, user_id):
    """Handle general questions about a medicine."""
    usage = get_usage_for_medicine(medicine)
    
    # Update context
    conversation_context[user_id] = {
        'last_medicine': medicine,
        'last_question_type': 'general'
    }
    
    if usage:
        return f"**{medicine.title()}** is used for: {usage}"
    else:
        return f"Sorry, I couldn't find information for **{medicine.title()}**. You can try:\n• Asking about its price: 'What's the price of {medicine.title()}?'\n• Asking about a different medicine"

def get_usage_for_medicine(medicine):
    """Get usage information for a medicine using the fallback chain."""
    # Try local database first (fastest)
    usage = get_local_usage(medicine)
    print(f"[DEBUG] Local usage lookup for '{medicine}': '{usage[:100] if usage else 'None'}...'")
    
    if not usage:
        # Use the new fallback chain
        generic_name = extract_generic_name_from_trade_name(medicine)
        usage = get_usage_generic(medicine, generic_name)
        print(f"[DEBUG] Fallback usage lookup for '{medicine}': '{usage[:100] if usage else 'None'}...'")
    
    return usage

def handle_ingredients_question(medicine):
    """Handle active ingredient questions."""
    # Basic ingredient information for common medicines
    ingredients = {
        'tylenol': 'Acetaminophen (500mg)',
        'advil': 'Ibuprofen (200mg)',
        'panadol': 'Paracetamol (500mg)',
        'aspirin': 'Acetylsalicylic acid (325mg)',
        'brufen': 'Ibuprofen (400mg)',
        'motrin': 'Ibuprofen (200mg)',
        'zantac': 'Ranitidine (150mg)',
        'prilosec': 'Omeprazole (20mg)',
        'losec': 'Omeprazole (20mg)',
        'glucophage': 'Metformin (500mg)',
        'cidophage': 'Metformin (500mg)',
        'metformin': 'Metformin (500mg)',
        'norvasc': 'Amlodipine (5mg)',
        'amlor': 'Amlodipine (5mg)',
        'lipitor': 'Atorvastatin (20mg)',
        'atorvastatin': 'Atorvastatin (20mg)',
        'concor': 'Bisoprolol (5mg)',
        'bisoprolol': 'Bisoprolol (5mg)',
        'augmentin': 'Amoxicillin + Clavulanic acid (875mg + 125mg)',
        'amoxicillin': 'Amoxicillin (500mg)',
        'voltaren': 'Diclofenac (50mg)',
        'cataflam': 'Diclofenac (50mg)',
        'diclofenac': 'Diclofenac (50mg)',
        'claritin': 'Loratadine (10mg)',
        'claritine': 'Loratadine (10mg)',
        'loratadine': 'Loratadine (10mg)',
        'zyrtec': 'Cetirizine (10mg)',
        'alerid': 'Cetirizine (10mg)',
        'cetirizine': 'Cetirizine (10mg)',
        'ozempic': 'Semaglutide (0.5mg/1mg)',
        'semaglutide': 'Semaglutide (0.5mg/1mg)',
        'doxycycline': 'Doxycycline (100mg)',
        'azithromycin': 'Azithromycin (250mg)',
        'ciprofloxacin': 'Ciprofloxacin (500mg)'
    }
    
    ingredient = ingredients.get(medicine.lower())
    if ingredient:
        return f"**{medicine.title()}** contains: {ingredient}"
    else:
        return f"I don't have the active ingredient information for **{medicine.title()}** in my database. Please consult a healthcare professional or check the medicine packaging for detailed ingredient information."

def handle_warnings_question(medicine):
    """Handle warnings and contraindications questions."""
    warnings = {
        'metformin': 'Should not be used by people with kidney disease, liver disease, or heart failure. May cause lactic acidosis in rare cases.',
        'doxycycline': 'Should not be used during pregnancy, breastfeeding, or in children under 8 years old. Can cause tooth discoloration.',
        'aspirin': 'Should not be given to children under 16 due to Reye\'s syndrome risk. Avoid if you have stomach ulcers or bleeding disorders.',
        'ibuprofen': 'Should not be used by people with kidney disease, heart disease, or stomach ulcers. Avoid during pregnancy.',
        'advil': 'Should not be used by people with kidney disease, heart disease, or stomach ulcers. Avoid during pregnancy.',
        'brufen': 'Should not be used by people with kidney disease, heart disease, or stomach ulcers. Avoid during pregnancy.',
        'atorvastatin': 'Should not be used during pregnancy or breastfeeding. Can cause muscle problems and liver damage.',
        'lipitor': 'Should not be used during pregnancy or breastfeeding. Can cause muscle problems and liver damage.',
        'augmentin': 'Should not be used if allergic to penicillin. May cause diarrhea and stomach upset.',
        'amoxicillin': 'Should not be used if allergic to penicillin. May cause allergic reactions.',
        'ozempic': 'Should not be used by people with type 1 diabetes or diabetic ketoacidosis. May cause pancreatitis.',
        'semaglutide': 'Should not be used by people with type 1 diabetes or diabetic ketoacidosis. May cause pancreatitis.'
    }
    
    warning = warnings.get(medicine.lower())
    if warning:
        return f"**{medicine.title()}** warnings: {warning}\n\n**Important**: Always consult your healthcare provider before taking any medication."
    else:
        return f"I don't have specific warning information for **{medicine.title()}** in my database. Please consult a healthcare professional or pharmacist for detailed safety information."

def handle_special_populations_question(medicine):
    """Handle pregnancy, pediatric, and special population questions."""
    special_info = {
        'metformin': 'Generally safe during pregnancy (Category B). Can be used in children over 10 years old.',
        'doxycycline': 'NOT safe during pregnancy (Category D). NOT recommended for children under 8 years old.',
        'loratadine': 'Generally safe during pregnancy (Category B). Can be used in children over 2 years old.',
        'cetirizine': 'Generally safe during pregnancy (Category B). Can be used in children over 6 months old.',
        'claritin': 'Generally safe during pregnancy (Category B). Can be used in children over 2 years old.',
        'claritine': 'Generally safe during pregnancy (Category B). Can be used in children over 2 years old.',
        'zyrtec': 'Generally safe during pregnancy (Category B). Can be used in children over 6 months old.',
        'alerid': 'Generally safe during pregnancy (Category B). Can be used in children over 6 months old.',
        'paracetamol': 'Safe during pregnancy and breastfeeding. Can be used in children over 3 months old.',
        'panadol': 'Safe during pregnancy and breastfeeding. Can be used in children over 3 months old.',
        'tylenol': 'Safe during pregnancy and breastfeeding. Can be used in children over 3 months old.',
        'ibuprofen': 'Avoid during pregnancy, especially third trimester. Can be used in children over 6 months old.',
        'advil': 'Avoid during pregnancy, especially third trimester. Can be used in children over 6 months old.',
        'brufen': 'Avoid during pregnancy, especially third trimester. Can be used in children over 6 months old.',
        'augmentin': 'Generally safe during pregnancy (Category B). Pediatric dosing available.',
        'amoxicillin': 'Generally safe during pregnancy (Category B). Pediatric dosing available.'
    }
    
    info = special_info.get(medicine.lower())
    if info:
        return f"**{medicine.title()}** for special populations: {info}\n\n**Important**: Always consult your healthcare provider before taking any medication during pregnancy or giving to children."
    else:
        return f"I don't have specific information about **{medicine.title()}** use in special populations. Please consult a healthcare professional for guidance on use during pregnancy or in children."

