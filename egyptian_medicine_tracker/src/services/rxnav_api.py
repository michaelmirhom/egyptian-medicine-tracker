import requests
import logging
from typing import Optional, List, Dict, Tuple
from .local_usage_db import get_local_usage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RxNavAPI:
    """Service class to interact with RxNav API for drug information"""
    
    def __init__(self):
        self.base_url = "https://rxnav.nlm.nih.gov/REST"
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "HarbyPharmacy/1.0"
        })
    
    def get_rxcui(self, drug_name: str) -> Optional[str]:
        """
        Get RxCUI (drug identifier) from drug name
        
        Args:
            drug_name (str): Drug name to search for
            
        Returns:
            Optional[str]: RxCUI if found, None otherwise
        """
        try:
            url = f"{self.base_url}/drugs"
            print(f"[DEBUG] [get_rxcui] Requesting: {url} with name='{drug_name}'")
            response = self.session.get(url, params={"name": drug_name}, timeout=10)
            print(f"[DEBUG] [get_rxcui] Response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] [get_rxcui] Response JSON: {data}")
            
            # Check if drug group exists and has concepts
            if 'drugGroup' in data and 'conceptGroup' in data['drugGroup']:
                for concept_group in data['drugGroup']['conceptGroup']:
                    if 'conceptProperties' in concept_group:
                        for concept in concept_group['conceptProperties']:
                            if 'rxcui' in concept:
                                print(f"[DEBUG] [get_rxcui] Found rxcui: {concept['rxcui']}")
                                return concept['rxcui']
            
            print(f"[DEBUG] [get_rxcui] No rxcui found for '{drug_name}'")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] [get_rxcui] Request error: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            print(f"[DEBUG] [get_rxcui] Data parsing error: {str(e)}")
            return None
        except Exception as e:
            print(f"[DEBUG] [get_rxcui] Unexpected error: {str(e)}")
            return None
    
    def get_usage_info(self, rxcui: str) -> Tuple[bool, List[str], str]:
        """
        Get usage information for a drug by RxCUI
        
        Args:
            rxcui (str): Drug RxCUI identifier
            
        Returns:
            Tuple[bool, List[str], str]: (success, usage_list, error_message)
        """
        try:
            url = f"{self.base_url}/rxcui/{rxcui}/allProperties.json"
            print(f"[DEBUG] [get_usage_info] Requesting: {url} with prop='all'")
            response = self.session.get(url, params={"prop": "all"}, timeout=10)
            print(f"[DEBUG] [get_usage_info] Response status: {response.status_code}")
            response.raise_for_status()
            
            data = response.json()
            print(f"[DEBUG] [get_usage_info] Response JSON: {data}")
            usage_info = []
            
            # Extract indication information
            if 'propConceptGroup' in data and 'propConcept' in data['propConceptGroup']:
                for prop in data['propConceptGroup']['propConcept']:
                    prop_name = prop.get('propName', '').lower()
                    prop_value = prop.get('propValue', '')
                    
                    # Look for various types of usage information
                    if any(keyword in prop_name for keyword in ['indication', 'use', 'purpose', 'treatment', 'therapy']):
                        if prop_value and prop_value not in usage_info:
                            usage_info.append(prop_value)
            
            # If still no usage info, try alternative endpoints
            if not usage_info:
                # Try to get drug information from alternative endpoint
                alt_url = f"{self.base_url}/rxcui/{rxcui}/property.json?propName=INDICATION"
                print(f"[DEBUG] [get_usage_info] Trying alternative endpoint: {alt_url}")
                try:
                    alt_response = self.session.get(alt_url, timeout=10)
                    print(f"[DEBUG] [get_usage_info] Alt response status: {alt_response.status_code}")
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        print(f"[DEBUG] [get_usage_info] Alt response JSON: {alt_data}")
                        if 'propValue' in alt_data:
                            usage_info.append(alt_data['propValue'])
                    else:
                        print(f"[DEBUG] [get_usage_info] Alt endpoint returned status: {alt_response.status_code}")
                except Exception as e:
                    print(f"[DEBUG] [get_usage_info] Alt endpoint error: {str(e)}")
            
            print(f"[DEBUG] [get_usage_info] Returning usage_info: {usage_info}")
            return True, usage_info, ""
            
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] [get_usage_info] Request error: {str(e)}")
            return False, [], f"Network error: {str(e)}"
        except (KeyError, IndexError) as e:
            print(f"[DEBUG] [get_usage_info] Data parsing error: {str(e)}")
            return False, [], f"Data parsing error: {str(e)}"
        except Exception as e:
            print(f"[DEBUG] [get_usage_info] Unexpected error: {str(e)}")
            return False, [], f"Unexpected error: {str(e)}"
    
    def get_drug_info(self, drug_name: str) -> Tuple[bool, Dict, str]:
        """
        Get comprehensive drug information including usage
        
        Args:
            drug_name (str): Drug name to search for
            
        Returns:
            Tuple[bool, Dict, str]: (success, drug_info, error_message)
        """
        print(f"[DEBUG] [get_drug_info] Called with drug_name='{drug_name}'")
        # Get RxCUI first
        rxcui = self.get_rxcui(drug_name)
        print(f"[DEBUG] [get_drug_info] get_rxcui returned: {rxcui}")
        
        if not rxcui:
            print(f"[DEBUG] [get_drug_info] Drug '{drug_name}' not found in RxNav database")
            return False, {}, f"Drug '{drug_name}' not found in RxNav database"
        
        # Get usage information
        success, usage_list, error = self.get_usage_info(rxcui)
        print(f"[DEBUG] [get_drug_info] get_usage_info: success={success}, usage_list={usage_list}, error={error}")
        
        if not success:
            print(f"[DEBUG] [get_drug_info] Usage info not found for rxcui={rxcui}")
            return False, {}, error
        
        # Format the response
        usage_text = '; '.join(usage_list) if usage_list else ''
        
        # If RxNav doesn't provide usage, try local database
        if not usage_text:
            print(f"[DEBUG] [get_drug_info] No usage_text from RxNav, trying local DB for '{drug_name}'")
            local_usage = get_local_usage(drug_name)
            if local_usage:
                usage_text = local_usage
            else:
                usage_text = 'Usage information not available'
        
        drug_info = {
            'rxcui': rxcui,
            'drug_name': drug_name,
            'usage': usage_list,
            'usage_text': usage_text
        }
        print(f"[DEBUG] [get_drug_info] Returning drug_info: {drug_info}")
        return True, drug_info, ""

# Global instance
rxnav_api = RxNavAPI() 