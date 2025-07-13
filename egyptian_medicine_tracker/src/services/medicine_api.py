import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

# Suppress InsecureRequestWarning for unverified HTTPS requests to the external API
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# This is safe here because we are intentionally disabling SSL verification for a trusted API in development.

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicinePriceAPI:
    """Service class to interact with the Egyptian Medicine Price API"""
    
    def __init__(self):
        self.base_url = "https://moelshafey.xyz/API/MD"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_medicines(self, name: str) -> Tuple[bool, List[Dict], str]:
        """
        Search for medicines by name
        
        Args:
            name (str): Medicine name to search for (Arabic or English)
            
        Returns:
            Tuple[bool, List[Dict], str]: (success, products, error_message)
        """
        try:
            # URL encode the medicine name
            encoded_name = quote(name)
            url = f"{self.base_url}/search.php"
            print(f"[DEBUG] [search_medicines] Requesting: {url} with name='{name}' (encoded='{encoded_name}')")
            
            # NOTE: verify=False disables SSL verification due to invalid certificate on the API
            response = self.session.get(url, params={"name": name}, timeout=10, verify=False)
            print(f"[DEBUG] [search_medicines] Response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] [search_medicines] Response JSON: {data}")
            
            if data.get("error", True):
                print(f"[DEBUG] [search_medicines] API Error: {data.get('message', 'Unknown error')}")
                return False, [], f"API Error: {data.get('message', 'Unknown error')}"
            
            if data.get("code") != 200:
                print(f"[DEBUG] [search_medicines] API returned code: {data.get('code')}")
                return False, [], f"API returned code: {data.get('code')}"
            
            products = data.get("products", [])
            print(f"[DEBUG] [search_medicines] Found {len(products)} products.")
            return True, products, ""
            
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] [search_medicines] Request error: {str(e)}")
            return False, [], f"Network error: {str(e)}"
        except ValueError as e:
            print(f"[DEBUG] [search_medicines] JSON parsing error: {str(e)}")
            return False, [], f"Invalid response format: {str(e)}"
        except Exception as e:
            print(f"[DEBUG] [search_medicines] Unexpected error: {str(e)}")
            return False, [], f"Unexpected error: {str(e)}"
    
    def get_medicine_details(self, medicine_id: str) -> Tuple[bool, Dict, str]:
        """
        Get detailed information about a specific medicine
        
        Args:
            medicine_id (str): Medicine ID from search results
            
        Returns:
            Tuple[bool, Dict, str]: (success, product_details, error_message)
        """
        try:
            url = f"{self.base_url}/info.php"
            print(f"[DEBUG] [get_medicine_details] Requesting: {url} with id='{medicine_id}'")
            
            # NOTE: verify=False disables SSL verification due to invalid certificate on the API
            response = self.session.get(url, params={"id": medicine_id}, timeout=10, verify=False)
            print(f"[DEBUG] [get_medicine_details] Response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] [get_medicine_details] Response JSON: {data}")
            
            if data.get("error", True):
                print(f"[DEBUG] [get_medicine_details] API Error: {data.get('message', 'Unknown error')}")
                return False, {}, f"API Error: {data.get('message', 'Unknown error')}"
            
            if data.get("code") != 200:
                print(f"[DEBUG] [get_medicine_details] API returned code: {data.get('code')}")
                return False, {}, f"API returned code: {data.get('code')}"
            
            product = data.get("product", {})
            print(f"[DEBUG] [get_medicine_details] Product: {product}")
            return True, product, ""
            
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] [get_medicine_details] Request error: {str(e)}")
            return False, {}, f"Network error: {str(e)}"
        except ValueError as e:
            print(f"[DEBUG] [get_medicine_details] JSON parsing error: {str(e)}")
            return False, {}, f"Invalid response format: {str(e)}"
        except Exception as e:
            print(f"[DEBUG] [get_medicine_details] Unexpected error: {str(e)}")
            return False, {}, f"Unexpected error: {str(e)}"
    
    def search_and_get_details(self, name: str) -> Tuple[bool, List[Dict], str]:
        """
        Search for medicines and get detailed information for each result
        
        Args:
            name (str): Medicine name to search for
            
        Returns:
            Tuple[bool, List[Dict], str]: (success, detailed_products, error_message)
        """
        print(f"[DEBUG] [search_and_get_details] Called with name='{name}'")
        success, products, error = self.search_medicines(name)
        print(f"[DEBUG] [search_and_get_details] search_medicines: success={success}, products_count={len(products)}, error={error}")
        
        if not success:
            return False, [], error
        
        detailed_products = []
        
        for product in products[:5]:  # Limit to first 5 results to avoid rate limiting
            medicine_id = product.get("id")
            print(f"[DEBUG] [search_and_get_details] Getting details for product id='{medicine_id}'")
            if medicine_id:
                success, details, error = self.get_medicine_details(medicine_id)
                print(f"[DEBUG] [search_and_get_details] get_medicine_details: success={success}, error={error}")
                if success:
                    # Merge search result with detailed information
                    detailed_product = {**product, **details}
                    detailed_products.append(detailed_product)
                else:
                    print(f"[DEBUG] [search_and_get_details] Failed to get details for {medicine_id}: {error}")
                    # Add the basic product info if details failed
                    detailed_products.append(product)
                
                # Add small delay to be respectful to the API
                time.sleep(0.2)
        print(f"[DEBUG] [search_and_get_details] Returning {len(detailed_products)} detailed products.")
        return True, detailed_products, ""

# Global instance
medicine_api = MedicinePriceAPI() 