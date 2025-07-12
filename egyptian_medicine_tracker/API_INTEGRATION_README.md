# Egyptian Medicine Price API Integration

This project now integrates with the Egyptian Medicine Price API to provide real-time medicine pricing and information.

## API Endpoints

### 1. Real-time Medicine Search
**GET** `/api/medicines/api-search?q=<medicine_name>`

Search for medicines using the external API for real-time data.

**Example:**
```bash
curl "http://localhost:5000/api/medicines/api-search?q=paramol"
```

**Response:**
```json
{
  "success": true,
  "products": [
    {
      "id": "paramol-plus-20-tab-b-1750858203",
      "trade_name": "بارامول بلس 20 قرص",
      "price": 16,
      "currency": "EGP",
      "image": "https://...",
      "description": "مسكن للألم وخافض للحرارة...",
      "components": ["Paracetamol 500 mg"],
      "company": "شركة الحكمة",
      "source": "External API",
      "last_updated": 1703123456.789
    }
  ],
  "count": 1
}
```

### 2. Sync Medicine from API
**POST** `/api/medicines/api-sync`

Sync a medicine from the external API to your local database.

**Request Body:**
```json
{
  "name": "paramol"
}
```

**Response:**
```json
{
  "message": "Medicine added successfully",
  "medicine": {
    "id": 1,
    "trade_name": "بارامول بلس 20 قرص",
    "price": 16,
    "api_id": "paramol-plus-20-tab-b-1750858203",
    "api_image": "https://...",
    "api_description": "مسكن للألم وخافض للحرارة...",
    "api_components": "[\"Paracetamol 500 mg\"]",
    "api_company": "شركة الحكمة",
    "source": "External API"
  }
}
```

### 3. Get Medicine Details from API
**GET** `/api/medicines/api-details/<medicine_id>`

Get detailed information about a specific medicine from the external API.

**Example:**
```bash
curl "http://localhost:5000/api/medicines/api-details/paramol-plus-20-tab-b-1750858203"
```

### 4. Refresh Prices
**POST** `/api/medicines/refresh-prices`

Update prices for all medicines in your database that have API IDs.

**Response:**
```json
{
  "message": "Refreshed prices for 5 medicines",
  "updated_count": 5,
  "errors": []
}
```

## Database Schema Updates

The Medicine model has been extended with new fields for API integration:

- `api_id`: Medicine ID from external API
- `api_image`: Medicine image URL
- `api_description`: Medicine description
- `api_components`: Medicine components (JSON string)
- `api_company`: Manufacturing company

## Testing the Integration

Run the test script to verify the API integration:

```bash
python test_api.py
```

This will test:
- Medicine search functionality
- Getting detailed medicine information
- Combined search and details functionality

## Usage Examples

### 1. Search for medicines in real-time
```python
import requests

# Search for paramol
response = requests.get("http://localhost:5000/api/medicines/api-search?q=paramol")
medicines = response.json()["products"]

for medicine in medicines:
    print(f"{medicine['trade_name']}: {medicine['price']} EGP")
```

### 2. Sync a medicine to your database
```python
import requests

# Sync paramol to database
response = requests.post("http://localhost:5000/api/medicines/api-sync", 
                        json={"name": "paramol"})
result = response.json()
print(f"Medicine synced: {result['medicine']['trade_name']}")
```

### 3. Refresh all prices
```python
import requests

# Refresh prices for all medicines
response = requests.post("http://localhost:5000/api/medicines/refresh-prices")
result = response.json()
print(f"Updated {result['updated_count']} medicines")
```

## Error Handling

The API integration includes comprehensive error handling:

- Network timeouts (10 seconds)
- JSON parsing errors
- API error responses
- Rate limiting (0.2-0.3 second delays between requests)

## Rate Limiting

To be respectful to the external API:
- Search requests are limited to 5 results per search
- 0.2 second delay between detail requests
- 0.3 second delay during price refresh operations

## Notes

- The API supports both Arabic and English medicine names
- All prices are in Egyptian Pounds (EGP)
- Images are provided as URLs
- Medicine descriptions are in Arabic
- Components are provided as arrays of active ingredients 