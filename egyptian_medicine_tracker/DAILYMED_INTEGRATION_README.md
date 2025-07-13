# DailyMed Integration

This document describes the offline DailyMed integration that provides comprehensive medicine usage information even when external APIs are unavailable.

## Overview

The system now includes an offline DailyMed database that serves as a reliable fallback for medicine usage information. This ensures the bot never says "no usage info" and provides accurate, FDA-approved information.

## Architecture

### Fallback Chain (Priority Order)
1. **Local Database** - Curated, verified usage information for common medicines
2. **Local DailyMed Database** - Offline FDA-approved label data
3. **RxNav API** - Live API for drug information
4. **openFDA API** - Live FDA API
5. **DailyMed API** - Live DailyMed API

### Database Schema

```python
class DailyMedLabel(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    setid        = db.Column(db.String(36), unique=True)
    brand        = db.Column(db.String(250))
    generic      = db.Column(db.String(200), index=True)
    indications  = db.Column(db.Text)
    contraind    = db.Column(db.Text)
    ingredients  = db.Column(db.Text)
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Ingest DailyMed Data

Place your DailyMed archives in the `data/` directory:
- `dm_spl_release_human_rx_part1.zip`
- `dm_spl_release_human_rx_part2.zip`
- `dm_spl_release_human_rx_part3.zip`
- `dm_spl_release_human_rx_part4.zip`
- `dm_spl_release_human_rx_part5.zip`

Run the ingestion script:
```bash
python scripts/ingest_dailymed.py
```

This will:
- Extract XML files from all archives
- Parse label information (brand, generic, indications, contraindications, ingredients)
- Store data in SQLite database
- Show progress with tqdm
- Commit every 1000 records

### 3. Start the Application

```bash
flask run
```

## API Endpoints

### Get Label Information
```
GET /api/labels/{generic_name}
```

Example:
```bash
curl http://localhost:5000/api/labels/loratadine
```

Response:
```json
{
  "brand": "Claritin",
  "generic": "loratadine",
  "indications": "Claritin is indicated for the relief of symptoms associated with allergic rhinitis...",
  "contraind": "Hypersensitivity to loratadine or any of the excipients...",
  "ingredients": "Loratadine 10 mg"
}
```

## Usage in Chat

The system automatically uses the DailyMed fallback when:

1. **Arabic medicine names** are resolved to English equivalents
2. **Trade names** are matched to generic names
3. **Live APIs fail** or return invalid information

Example chat interaction:
```
User: "ما هو استخدام كلاريتين؟"
Bot: "Claritin (loratadine) is used to relieve allergy symptoms such as watery eyes, runny nose, itching eyes/nose, and sneezing. It is an antihistamine that works by blocking histamine, a substance in the body that causes allergic symptoms."
```

## Testing

Run the integration test:
```bash
python test_dailymed_integration.py
```

This will verify:
- Database connectivity
- Medicine lookup functionality
- Arabic name resolution
- Full fallback chain operation

## File Structure

```
src/
├── models/
│   └── dailymed.py              # DailyMed database model
├── routes/
│   └── label.py                 # API endpoints for label data
├── services/
│   └── usage_fallback.py        # Updated with local DailyMed fallback
└── main.py                      # Updated with new blueprint registration

scripts/
└── ingest_dailymed.py           # Data ingestion script

data/
├── dm_spl_release_human_rx_part1.zip
├── dm_spl_release_human_rx_part2.zip
├── dm_spl_release_human_rx_part3.zip
├── dm_spl_release_human_rx_part4.zip
└── dm_spl_release_human_rx_part5.zip
```

## Benefits

1. **Offline Reliability** - Works without internet connection
2. **FDA-Approved Data** - Uses official FDA label information
3. **Comprehensive Coverage** - Includes thousands of medicines
4. **Fast Response** - No API latency
5. **Arabic Support** - Seamless Arabic-to-English resolution
6. **Fallback Chain** - Multiple layers of reliability

## Troubleshooting

### No Data After Ingestion
- Check that archives are in the correct location (`data/` directory)
- Verify archive names match the expected pattern
- Check for XML parsing errors in the ingestion log

### API Endpoint Not Found
- Ensure the label blueprint is registered in `main.py`
- Restart the Flask application after changes

### Memory Issues During Ingestion
- The ingestion process uses significant memory
- Consider processing archives one at a time if needed
- Monitor system resources during ingestion

## Performance Notes

- **Ingestion Time**: ~30-60 minutes for all 5 archives
- **Database Size**: ~500MB-1GB depending on archive content
- **Query Performance**: Fast due to indexed generic name field
- **Memory Usage**: Moderate during ingestion, low during normal operation 