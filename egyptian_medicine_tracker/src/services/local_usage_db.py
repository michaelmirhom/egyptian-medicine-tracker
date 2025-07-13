"""
Local database of common medicine uses as fallback
"""

COMMON_MEDICINE_USES = {
    # Pain relievers
    "panadol": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "paracetamol": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "aspirin": "Used to reduce fever and relieve mild to moderate pain from conditions such as muscle aches, toothaches, common cold, and headaches. Also used to prevent heart attacks and strokes.",
    "ibuprofen": "Used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    
    # Antibiotics
    "augmentin": "Used to treat bacterial infections including sinusitis, pneumonia, ear infections, bronchitis, urinary tract infections, and skin infections.",
    "amoxicillin": "Used to treat a wide variety of bacterial infections including bronchitis, pneumonia, and infections of the ear, nose, throat, skin, or urinary tract.",
    "azithromycin": "Used to treat many different types of infections caused by bacteria, including infections of the lungs, skin, ears, and reproductive organs.",
    
    # Anti-inflammatory
    "voltaren": "Used to reduce pain, swelling, and joint stiffness caused by arthritis. Also used for acute pain, muscle pain, and inflammation.",
    "diclofenac": "Used to reduce pain, swelling, and joint stiffness caused by arthritis. Also used for acute pain, muscle pain, and inflammation.",
    
    # Heart medications
    "concor": "Used to treat high blood pressure and heart failure. Helps reduce the risk of heart attacks and strokes.",
    "bisoprolol": "Used to treat high blood pressure and heart failure. Helps reduce the risk of heart attacks and strokes.",
    "lipitor": "Used to lower cholesterol and triglycerides in the blood. Helps prevent heart disease, heart attacks, and strokes.",
    "atorvastatin": "Used to lower cholesterol and triglycerides in the blood. Helps prevent heart disease, heart attacks, and strokes.",
    
    # Allergy medications
    "cetirizine": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "loratadine": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "claritine": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "claritin": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    
    # Stomach medications
    "omeprazole": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "pantoprazole": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    
    # Diabetes medications
    "metformin": "Used to control high blood sugar in people with type 2 diabetes. It works by helping to restore your body's proper response to insulin.",
    
    # Common Egyptian brands
    "rivo": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "cataflam": "Used to reduce pain, swelling, and joint stiffness caused by arthritis. Also used for acute pain, muscle pain, and inflammation.",
    "augmentin": "Used to treat bacterial infections including sinusitis, pneumonia, ear infections, bronchitis, urinary tract infections, and skin infections.",
    
    # Additional trade names
    "tylenol": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "advil": "Used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "brufen": "Used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "motrin": "Used to reduce fever and treat pain or inflammation caused by many conditions such as headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "zantac": "Used to treat stomach ulcers, gastroesophageal reflux disease (GERD), and conditions where the stomach produces too much acid.",
    "rantag": "Used to treat stomach ulcers, gastroesophageal reflux disease (GERD), and conditions where the stomach produces too much acid.",
    "ranitin": "Used to treat stomach ulcers, gastroesophageal reflux disease (GERD), and conditions where the stomach produces too much acid.",
    "prilosec": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "losec": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "glucophage": "Used to control high blood sugar in people with type 2 diabetes. It works by helping to restore your body's proper response to insulin.",
    "cidophage": "Used to control high blood sugar in people with type 2 diabetes. It works by helping to restore your body's proper response to insulin.",
    "norvasc": "Used to treat high blood pressure and chest pain (angina). It works by relaxing blood vessels.",
    "amlor": "Used to treat high blood pressure and chest pain (angina). It works by relaxing blood vessels.",
    "zyrtec": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "alerid": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "doxycycline": "Used to treat bacterial infections including pneumonia, acne, urinary tract infections, and sexually transmitted infections.",
    "azithromycin": "Used to treat many different types of infections caused by bacteria, including infections of the lungs, skin, ears, and reproductive organs.",
    "ciprofloxacin": "Used to treat bacterial infections including urinary tract infections, pneumonia, and skin infections.",
}

def get_local_usage(drug_name: str) -> str:
    """
    Get usage information from local database
    
    Args:
        drug_name (str): Drug name to search for
        
    Returns:
        str: Usage information or empty string if not found
    """
    # Convert to lowercase for case-insensitive search
    drug_lower = drug_name.lower()
    print(f"[DEBUG] [get_local_usage] Looking up usage for '{drug_lower}'")
    
    # Direct match
    if drug_lower in COMMON_MEDICINE_USES:
        print(f"[DEBUG] [get_local_usage] Direct match found for '{drug_lower}'")
        return COMMON_MEDICINE_USES[drug_lower]
    
    # Partial match (check if drug name contains any key)
    for key, usage in COMMON_MEDICINE_USES.items():
        if key in drug_lower or drug_lower in key:
            print(f"[DEBUG] [get_local_usage] Partial match: '{drug_lower}' matches '{key}'")
            return usage
    
    print(f"[DEBUG] [get_local_usage] No match found for '{drug_lower}'")
    return ""

def get_local_usage_exact(drug_name: str) -> str:
    """
    Get usage information from local database - exact matches only
    
    Args:
        drug_name (str): Drug name to search for
        
    Returns:
        str: Usage information or empty string if not found
    """
    # Convert to lowercase for case-insensitive search
    drug_lower = drug_name.lower()
    print(f"[DEBUG] [get_local_usage_exact] Looking up usage for '{drug_lower}'")
    
    # Direct match only
    if drug_lower in COMMON_MEDICINE_USES:
        print(f"[DEBUG] [get_local_usage_exact] Exact match found for '{drug_lower}'")
        return COMMON_MEDICINE_USES[drug_lower]
    
    print(f"[DEBUG] [get_local_usage_exact] No exact match found for '{drug_lower}'")
    return "" 