"""
Local database of common medicine uses as fallback
"""

COMMON_MEDICINE_USES = {
    "panadol": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "lipitor": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "claritine": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing.",
    "claritin": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing.",
    "claratyne": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing.",
    "concor": "Used to treat high blood pressure and reduce the risk of heart attacks and strokes.",
    "voltaren": "Used to relieve pain, swelling, and joint stiffness caused by arthritis.",
    "rivo": "Used to prevent blood clots and reduce the risk of stroke and heart attack.",
    "augmentin": "Used to treat bacterial infections including pneumonia, bronchitis, and infections of the ear, nose, throat, urinary tract, and skin.",
    "prozac": "Used to treat depression, panic attacks, obsessive-compulsive disorder, and bulimia.",
    "zoloft": "Used to treat depression, panic attacks, obsessive-compulsive disorder, post-traumatic stress disorder, and social anxiety disorder.",
    "tylenol": "Used to treat fever and mild to moderate pain including headache, muscle aches, arthritis, backache, toothaches, colds, and fevers.",
    "advil": "Used to reduce fever and treat pain or inflammation caused by headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "motrin": "Used to reduce fever and treat pain or inflammation caused by headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "ibuprofen": "Used to reduce fever and treat pain or inflammation caused by headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "brufen": "Used to reduce fever and treat pain or inflammation caused by headache, toothache, back pain, arthritis, menstrual cramps, or minor injury.",
    "aspirin": "Used to reduce fever and relieve mild to moderate pain from headaches, muscle aches, toothaches, and colds. Also used to prevent heart attacks and strokes.",
    "omeprazole": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "prilosec": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "losec": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "metformin": "Used to treat type 2 diabetes. It helps control blood sugar levels.",
    "glucophage": "Used to treat type 2 diabetes. It helps control blood sugar levels.",
    "cidophage": "Used to treat type 2 diabetes. It helps control blood sugar levels.",
    "lantus": "A long-acting insulin used to treat diabetes by helping to control blood sugar levels.",
    "ozempic": "Used to treat type 2 diabetes and may help with weight loss. It helps control blood sugar levels.",
    "zocor": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "crestor": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "norvasc": "Used to treat high blood pressure and chest pain (angina). Lowering high blood pressure helps prevent strokes, heart attacks, and kidney problems.",
    "plavix": "Used to prevent blood clots and reduce the risk of stroke and heart attack.",
    "xarelto": "Used to prevent blood clots and reduce the risk of stroke and heart attack.",
    "allegra": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing.",
    "zyrtec": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "alerid": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    "doxycycline": "Used to treat bacterial infections including pneumonia, acne, urinary tract infections, and sexually transmitted infections.",
    "azithromycin": "Used to treat many different types of infections caused by bacteria, including infections of the lungs, skin, ears, and reproductive organs.",
    "ciprofloxacin": "Used to treat bacterial infections including urinary tract infections, pneumonia, and skin infections.",
    
    # FIXED: Added missing medicines from the user's questions
    "protonix": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "pantoprazole": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "levothyroxine": "Used to replace thyroid hormone in people whose thyroid gland does not produce enough thyroid hormone. Treats hypothyroidism.",
    "synthroid": "Used to replace thyroid hormone in people whose thyroid gland does not produce enough thyroid hormone. Treats hypothyroidism.",
    "montelukast": "Used to prevent asthma attacks and to relieve symptoms of seasonal allergies. It works by blocking certain natural substances that cause allergic reactions.",
    "singulair": "Used to prevent asthma attacks and to relieve symptoms of seasonal allergies. It works by blocking certain natural substances that cause allergic reactions.",
    "nexium": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "esomeprazole": "Used to treat certain stomach and esophagus problems such as acid reflux and ulcers. It decreases the amount of acid your stomach makes.",
    "zantac": "Used to treat and prevent stomach and intestinal ulcers, and to treat conditions where the stomach produces too much acid.",
    "ranitidine": "Used to treat and prevent stomach and intestinal ulcers, and to treat conditions where the stomach produces too much acid.",
    "atorvastatin": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "simvastatin": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "rosuvastatin": "Used to lower cholesterol and reduce the risk of heart disease and stroke.",
    "amlodipine": "Used to treat high blood pressure and chest pain (angina). Lowering high blood pressure helps prevent strokes, heart attacks, and kidney problems.",
    "lisinopril": "Used to treat high blood pressure and heart failure. It belongs to a class of drugs known as ACE inhibitors.",
    "hydrochlorothiazide": "Used to treat high blood pressure and fluid retention (edema). It helps your kidneys remove excess water and salt from your body.",
    "metoprolol": "Used to treat high blood pressure, chest pain, and heart failure. It belongs to a class of drugs known as beta blockers.",
    "carvedilol": "Used to treat high blood pressure and heart failure. It belongs to a class of drugs known as beta blockers.",
    "warfarin": "Used to prevent blood clots from forming or growing larger in your blood and blood vessels.",
    "coumadin": "Used to prevent blood clots from forming or growing larger in your blood and blood vessels.",
    "digoxin": "Used to treat heart failure and irregular heartbeats (atrial fibrillation). It helps the heart beat stronger and with a more regular rhythm.",
    "furosemide": "Used to treat fluid retention (edema) and high blood pressure. It helps your kidneys remove excess water and salt from your body.",
    "lasix": "Used to treat fluid retention (edema) and high blood pressure. It helps your kidneys remove excess water and salt from your body.",
    "naproxen": "Used to relieve pain, swelling, and joint stiffness caused by arthritis, bursitis, and gout attacks.",
    "aleve": "Used to relieve pain, swelling, and joint stiffness caused by arthritis, bursitis, and gout attacks.",
    "cetirizine": "Used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. Also used to relieve itching and hives.",
    
    # Nasal sprays and allergy medications - FIXED: Added Flonase and related medicines
    "flonase": "Used to treat nasal symptoms such as congestion, sneezing, and runny nose caused by seasonal or year-round allergies. Also used to treat nasal polyps.",
    "fluticasone": "Used to treat nasal symptoms such as congestion, sneezing, and runny nose caused by seasonal or year-round allergies. Also used to treat nasal polyps.",
    "nasacort": "Used to treat nasal symptoms of allergies including congestion, sneezing, and runny nose. Provides 24-hour relief from allergy symptoms.",
    "triamcinolone": "Used to treat nasal symptoms of allergies including congestion, sneezing, and runny nose. Provides 24-hour relief from allergy symptoms.",
    "rhinocort": "Used to treat and prevent nasal symptoms caused by allergies including runny nose, stuffy nose, and sneezing.",
    "budesonide": "Used to treat and prevent nasal symptoms caused by allergies including runny nose, stuffy nose, and sneezing.",
    "nasonex": "Used to treat nasal symptoms of seasonal and year-round allergies. Also used to treat and prevent nasal polyps.",
    "mometasone": "Used to treat nasal symptoms of seasonal and year-round allergies. Also used to treat and prevent nasal polyps.",
    "afrin": "Used for temporary relief of nasal congestion due to colds, allergies, or sinus irritation. Should not be used for more than 3 days.",
    "oxymetazoline": "Used for temporary relief of nasal congestion due to colds, allergies, or sinus irritation. Should not be used for more than 3 days.",
    "sudafed": "Used to temporarily relieve nasal congestion due to the common cold, hay fever, or other upper respiratory allergies.",
    "pseudoephedrine": "Used to temporarily relieve nasal congestion due to the common cold, hay fever, or other upper respiratory allergies.",
    "mucinex": "Used to help loosen congestion in your chest and throat, making it easier to cough out through your mouth.",
    "guaifenesin": "Used to help loosen congestion in your chest and throat, making it easier to cough out through your mouth.",
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