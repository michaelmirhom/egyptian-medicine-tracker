# 🏥 Egyptian Medicine Tracker

A comprehensive web application for tracking medicine prices, information, and providing AI-powered chat assistance for pharmaceutical queries. Built with Flask, featuring real-time API integration, offline DailyMed database, and Arabic language support.

## 🌟 Features

### 💊 **Medicine Database**
- **51,441+ medicines** with comprehensive information
- **Real-time price tracking** from Egyptian Medicine Price API
- **Offline DailyMed database** with FDA-approved information
- **Arabic and English** medicine name support
- **Fuzzy search** with typo tolerance

### 🤖 **AI Chat Assistant**
- **Intelligent medicine queries** with natural language processing
- **Multi-source information** from local DB, DailyMed, RxNav, and openFDA
- **Arabic language support** with automatic translation
- **Usage information** for medicines including indications, contraindications
- **Floating chat widget** with drag-and-drop functionality

### 🔍 **Advanced Search**
- **Real-time API search** for current prices
- **Local database search** for offline access
- **Multi-language support** (Arabic/English)
- **Price comparison** and tracking
- **Manufacturer information**

### 📊 **Data Sources**
- **Egyptian Medicine Price API** - Real-time pricing
- **DailyMed Database** - FDA-approved label information
- **RxNav API** - Drug interaction and usage data
- **openFDA API** - Comprehensive drug information
- **Local curated database** - Verified medicine information

## 🏗️ Architecture

```
egyptian-medicine-tracker/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── models/                 # Database models
│   │   ├── medicine.py         # Medicine data model
│   │   ├── user.py            # User management
│   │   ├── chat_memory.py     # Chat history
│   │   └── dailymed.py        # DailyMed database model
│   ├── routes/                # API endpoints
│   │   ├── medicine.py        # Medicine search and management
│   │   ├── user.py           # User operations
│   │   └── label.py          # DailyMed label data
│   ├── services/              # Business logic
│   │   ├── medicine_api.py    # Egyptian Medicine Price API
│   │   ├── rxnav_api.py       # RxNav API integration
│   │   ├── usage_fallback.py  # Multi-source usage information
│   │   ├── name_resolver.py   # Arabic-English translation
│   │   └── local_usage_db.py  # Local usage database
│   └── static/                # Frontend assets
│       ├── index.html         # Main web interface
│       ├── js/chat.js         # Chat widget functionality
│       └── favicon.ico        # App icon
├── scripts/                   # Data processing scripts
│   └── ingest_dailymed.py     # DailyMed data ingestion
├── requirements.txt           # Python dependencies
├── Procfile                  # Heroku deployment config
└── deployment_database.db     # Production database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd egyptian-medicine-tracker
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
cd egyptian_medicine_tracker
python src/main.py
```

4. **Access the application**
- Open your browser to `http://localhost:5000`
- Start searching for medicines or use the chat feature

## 📱 Usage

### Web Interface
- **Search medicines** by name (Arabic or English)
- **View prices** and detailed information
- **Compare medicines** from different sources
- **Track price changes** over time

### Chat Assistant
- **Ask questions** about medicine usage, side effects, interactions
- **Get dosage information** and contraindications
- **Arabic language support** - ask questions in Arabic
- **Multi-source responses** from FDA-approved databases

### API Endpoints

#### Search Medicines
```bash
GET /api/medicines/search?q=paramol
```

#### Real-time API Search
```bash
GET /api/medicines/api-search?q=paramol
```

#### Chat Interface
```bash
POST /api/medicines/chat
Content-Type: application/json

{
  "question": "What is the usage of aspirin?",
  "user_id": "user123"
}
```

#### Get Medicine Details
```bash
GET /api/medicines/api-details/<medicine_id>
```

## 🔧 Configuration

### Environment Variables
```bash
# Flask configuration
SECRET_KEY=your_secret_key_here

# Database configuration
DATABASE_URL=sqlite:///app.db

# API configuration
EGYPTIAN_MEDICINE_API_URL=https://moelshafey.xyz/API/MD
```

### Database Setup
The application uses SQLite by default. For production, you can configure other databases:

```python
# PostgreSQL example
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://user:pass@localhost/dbname"

# MySQL example
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://user:pass@localhost/dbname"
```

## 🗄️ Database Schema

### Medicine Table
```sql
CREATE TABLE medicine (
    id INTEGER PRIMARY KEY,
    trade_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    reg_no VARCHAR(100),
    applicant VARCHAR(200),
    price FLOAT,
    currency VARCHAR(10) DEFAULT 'EGP',
    last_updated DATETIME,
    source VARCHAR(100),
    api_id VARCHAR(200),
    api_image VARCHAR(500),
    api_description TEXT,
    api_components TEXT,
    api_company VARCHAR(200),
    api_usage TEXT
);
```

### DailyMed Labels Table
```sql
CREATE TABLE dailymed_label (
    id INTEGER PRIMARY KEY,
    setid VARCHAR(36) UNIQUE,
    brand VARCHAR(250),
    generic VARCHAR(200),
    indications TEXT,
    contraind TEXT,
    ingredients TEXT
);
```

## 🌐 Deployment

### Heroku Deployment
1. **Create Heroku app**
```bash
heroku create your-app-name
```

2. **Set environment variables**
```bash
heroku config:set SECRET_KEY=your_secret_key
```

3. **Deploy**
```bash
git push heroku main
```

### Render Deployment
1. **Connect your GitHub repository**
2. **Set build command**: `pip install -r requirements.txt`
3. **Set start command**: `gunicorn src.main:app --bind 0.0.0.0:$PORT`
4. **Deploy automatically**

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:5000"]
```

## 🔍 Data Sources Integration

### Egyptian Medicine Price API
- **Real-time pricing** from Egyptian pharmaceutical market
- **Arabic medicine names** support
- **Manufacturer information** and product details
- **Automatic price updates**

### DailyMed Database
- **51,441+ FDA-approved medicines**
- **Offline access** for reliability
- **Comprehensive label information**
- **Indications and contraindications**

### RxNav API
- **Drug interactions** and usage information
- **Generic name resolution**
- **Dosage recommendations**
- **Side effect information**

## 🛠️ Development

### Project Structure
```
src/
├── crew/agents.py             # AI chat agents
├── database/                  # Database configuration
├── models/                    # Data models
├── routes/                    # API endpoints
├── services/                  # Business logic
└── static/                    # Frontend assets
```

### Adding New Features
1. **Create models** in `src/models/`
2. **Add routes** in `src/routes/`
3. **Implement services** in `src/services/`
4. **Update frontend** in `src/static/`

### Testing
```bash
# Run API tests
python test_api.py

# Test chat functionality
python test_chat_questions.py

# Test database integration
python test_database_connection.py
```

## 📊 Performance

### Database Statistics
- **Total Medicines**: 51,441+
- **DailyMed Records**: 2,020 medicines
- **Unique Medicines**: 1,337 different medicines
- **Database Size**: ~1.36 MB
- **Search Response Time**: <100ms

### Optimization Features
- **Indexed database** for fast queries
- **Caching** for frequently accessed data
- **Rate limiting** for API calls
- **Connection pooling** for database access

## 🔒 Security

### API Security
- **Rate limiting** to prevent abuse
- **Input validation** for all endpoints
- **SQL injection protection** via SQLAlchemy
- **CORS configuration** for web access

### Data Privacy
- **User session management**
- **Secure chat history** storage
- **No sensitive data logging**
- **GDPR compliance** ready

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit a pull request**

### Development Guidelines
- **Follow PEP 8** Python style guide
- **Add docstrings** to all functions
- **Write unit tests** for new features
- **Update documentation** for API changes

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Egyptian Medicine Price API** for real-time pricing data
- **DailyMed** for comprehensive FDA-approved medicine information
- **RxNav** for drug interaction and usage data
- **openFDA** for additional drug information
- **Flask** community for the excellent web framework

## 📞 Support

For support and questions:
- **Create an issue** on GitHub
- **Check the documentation** in the docs folder
- **Review the integration guides** for specific features

---

**🏥 Built with ❤️ for the Egyptian pharmaceutical community** 