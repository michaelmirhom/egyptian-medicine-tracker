# PDF Medicine Information Extractor

This system can analyze PDF files containing medicine information and extract structured data to populate your database.

## 🚀 Features

- **Multi-format PDF support**: Text-based and image-based PDFs
- **OCR capability**: Extracts text from scanned documents
- **Arabic language support**: Recognizes Arabic medicine names
- **Intelligent parsing**: Extracts medicine names, prices, dosages, manufacturers
- **Confidence scoring**: Rates extraction quality
- **Database integration**: Automatically saves to SQLite database

## 📋 What it extracts

- **Trade/Brand names** (e.g., "Panadol", "Augmentin")
- **Generic names** (e.g., "Paracetamol", "Amoxicillin")
- **Arabic names** (Arabic medicine names)
- **Prices** (with currency detection)
- **Dosages** (mg, g, ml, mcg)
- **Manufacturers** (company names)
- **Registration numbers** (license numbers)

## 🛠️ Installation

### 1. Install Python dependencies
```bash
pip install -r pdf_requirements.txt
```

### 2. Install Tesseract OCR (for image-based PDFs)

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-eng  # English
sudo apt-get install tesseract-ocr-ara  # Arabic
```

**On Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH

**On macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # Language packs
```

## 📁 Usage

### Quick Start
1. Create a folder called `pdfs` in your project directory
2. Add your PDF files to the `pdfs` folder
3. Run the analysis:
```bash
python run_pdf_analysis.py
```

### Advanced Usage
```python
from pdf_analyzer import PDFMedicineAnalyzer

# Initialize analyzer
analyzer = PDFMedicineAnalyzer()

# Analyze a specific directory
analyzer.analyze_pdf_directory("path/to/your/pdfs")

# Get statistics
stats = analyzer.get_database_stats()
print(f"Extracted {stats['total_records']} records")

# Close connection
analyzer.close()
```

## 📊 Database Schema

The system creates a new table `medicine_pdf` with the following structure:

```sql
CREATE TABLE medicine_pdf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_name TEXT,           -- Brand name
    generic_name TEXT,         -- Generic/active ingredient
    arabic_name TEXT,          -- Arabic name
    dosage TEXT,               -- Strength/dosage
    price REAL,                -- Price amount
    currency TEXT DEFAULT 'EGP', -- Currency
    manufacturer TEXT,         -- Company name
    registration_no TEXT,      -- Registration number
    pdf_source TEXT,           -- Source PDF filename
    extracted_date TIMESTAMP,  -- When extracted
    confidence_score REAL,     -- Extraction quality (0-1)
    raw_text TEXT              -- Original extracted text
);
```

## 🔍 How it works

1. **Text Extraction**: Uses multiple methods (PyPDF2, pdfplumber, OCR)
2. **Section Splitting**: Divides text into medicine-related sections
3. **Pattern Matching**: Uses regex patterns to extract specific information
4. **Confidence Scoring**: Rates extraction quality based on found fields
5. **Database Storage**: Saves structured data with metadata

## 📝 Supported PDF Types

- **Text-based PDFs**: Direct text extraction
- **Scanned documents**: OCR-based extraction
- **Mixed content**: Combines text and OCR
- **Arabic documents**: Supports Arabic text recognition

## ⚙️ Configuration

You can customize the extraction patterns in `pdf_analyzer.py`:

```python
self.medicine_patterns = {
    'trade_name': r'(?i)(?:trade\s*name|brand\s*name)[:\s]*([A-Za-z0-9\s\-]+)',
    'generic_name': r'(?i)(?:generic\s*name|active\s*ingredient)[:\s]*([A-Za-z0-9\s\-/]+)',
    # Add more patterns as needed
}
```

## 📈 Performance Tips

- **Large PDFs**: Process in batches
- **Image quality**: Higher resolution = better OCR
- **Text layout**: Structured documents work better
- **Language**: Install appropriate Tesseract language packs

## 🔧 Troubleshooting

### Common Issues

1. **"No text extracted"**
   - PDF might be image-based, ensure Tesseract is installed
   - Check PDF file integrity

2. **"Missing libraries"**
   - Run: `pip install -r pdf_requirements.txt`

3. **"OCR not working"**
   - Install Tesseract and language packs
   - Check file permissions

4. **"Low confidence scores"**
   - PDF format might not match expected patterns
   - Consider adjusting regex patterns

### Logs
Check `pdf_analysis.log` for detailed error information.

## 📊 Example Output

```
🔍 PDF Medicine Information Extractor
==================================================
📁 Analyzing PDFs in: pdfs
📄 Found 3 PDF files:
   - medicine_catalog.pdf
   - price_list.pdf
   - drug_info.pdf

📊 Analysis Results:
==============================
Total records: 45
Unique medicines: 38
PDF sources: 3
Average confidence: 0.75
```

## 🔗 Integration with Main App

The extracted data can be used by your main application:

```python
# Query extracted medicine data
cursor.execute("""
    SELECT trade_name, generic_name, price, manufacturer 
    FROM medicine_pdf 
    WHERE confidence_score > 0.5
    ORDER BY extracted_date DESC
""")
```

This provides a comprehensive local database backup for when external APIs are unavailable. 