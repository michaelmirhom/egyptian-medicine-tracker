from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.medicine import Medicine
from src.services.medicine_api import medicine_api
import json
import time
import random

medicine_bp = Blueprint('medicine', __name__)

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
    search_type = request.args.get('type', 'name')  # 'name' or 'uses'
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    # Get real-time data from external API
    success, products, error = medicine_api.search_and_get_details(query)
    
    if not success:
        return jsonify({'error': error}), 500
    
    # Format the response
    formatted_products = []
    for product in products:
        formatted_product = {
            'id': product.get('id'),
            'trade_name': product.get('name', ''),
            'price': product.get('price'),
            'currency': 'EGP',
            'image': product.get('image'),
            'description': product.get('desc', ''),
            'components': product.get('components', []),
            'company': product.get('company', ''),
            'uses': product.get('uses', ''),  # Add uses information
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
        existing_medicine.last_updated = db.func.now()
        existing_medicine.source = 'External API'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Medicine updated successfully',
            'medicine': existing_medicine.to_dict()
        })
    else:
        # Create new medicine
        new_medicine = Medicine(
            trade_name=product.get('name', ''),
            price=product.get('price'),
            api_id=product.get('id'),
            api_image=product.get('image'),
            api_description=product.get('desc'),
            api_components=json.dumps(product.get('components', [])),
            api_company=product.get('company'),
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

