# Egyptian Medicine Tracker - Render Deployment Guide

## Files for Deployment

✅ **requirements.txt** - Updated with all necessary dependencies including:
- `gunicorn>=21.2.0` - WSGI HTTP Server for production
- `openai>=1.12.0` - OpenAI API client  
- `langchain>=0.1.0` - LangChain framework
- `langchain-community>=0.0.13` - LangChain community models

✅ **Procfile** - Contains the start command:
```
web: gunicorn src.main:app --bind 0.0.0.0:$PORT
```

## Render Setup Instructions

### 1. Connect Repository
- Go to [Render Dashboard](https://dashboard.render.com/)
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select the `egyptian_medicine_tracker` folder as root directory

### 2. Configure Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn src.main:app --bind 0.0.0.0:$PORT`
  (This should auto-detect from your Procfile)

### 3. Environment Variables
Add these environment variables in the Render dashboard:

#### Required:
- `OPENAI_API_KEY` - Your OpenAI API key
  - Get this from [OpenAI API Keys](https://platform.openai.com/api-keys)
  - Format: `sk-...` (starts with sk-)

#### Optional:
- `FLASK_ENV` - Set to `production`
- `FLASK_DEBUG` - Set to `false`

### 4. Deploy
- Click "Create Web Service"
- Render will automatically deploy your app
- Your app will be available at `https://your-app-name.onrender.com`

## App Features
- Medicine search and tracking
- Price comparison
- Usage information
- Arabic/English support
- Chat interface for medicine questions

## Local Testing
To test locally before deployment:
```bash
cd egyptian_medicine_tracker
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key-here"
python src/main.py
```

## Troubleshooting
- If build fails, check that all dependencies are in `requirements.txt`
- If app doesn't start, verify the Procfile command matches your app structure
- For OpenAI errors, ensure `OPENAI_API_KEY` is set correctly 