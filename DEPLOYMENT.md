# TenderEval AI - Deployment Guide

## Overview

This system consists of two main components:
- **Backend API**: FastAPI application (port 8000)
- **Frontend**: Streamlit application (port 8501)
- **Vector Store**: Qdrant for semantic search
- **Database**: PostgreSQL or SQLite

## Deployment on Render

### Step 1: Prepare Your Repository

1. Commit all files to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. Ensure `.env.example` is committed (your actual `.env` should be in `.gitignore`)

### Step 2: Deploy Backend API on Render

1. Go to [render.com](https://render.com) and sign in
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `tender-eval-backend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Standard ($12/month) or higher

5. Add Environment Variables:
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `ANTHROPIC_API_KEY`: Your Anthropic API key
   - `QDRANT_HOST`: `tender-eval-qdrant` (if deploying Qdrant on Render)
   - `QDRANT_PORT`: `6333`
   - `DATABASE_URL`: PostgreSQL connection string (see Step 4)
   - `PYTHON_VERSION`: `3.11.0`

6. Click **Create Web Service**

### Step 3: Deploy Frontend on Render

1. Click **New +** → **Web Service**
2. Connect the same GitHub repository
3. Configure the service:
   - **Name**: `tender-eval-frontend`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Plan**: Standard ($12/month)

4. Add Environment Variables:
   - `GROQ_API_KEY`: Same as backend
   - `GEMINI_API_KEY`: Same as backend
   - `STREAMLIT_SERVER_HEADLESS`: `true`
   - `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION`: `false`
   - Add a backend URL variable pointing to your Render backend service

5. Click **Create Web Service**

### Step 4: Deploy PostgreSQL Database

1. Click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `tender-eval-db`
   - **Database**: `tender_eval`
   - **User**: `tender_eval_user`
   - **Plan**: Standard

3. Copy the **Database URL** and add it to your backend environment variables as `DATABASE_URL`

### Step 5: Deploy Qdrant Vector Store (Optional)

Render doesn't have a built-in Qdrant service. Options:

**Option A: Use Qdrant Cloud (Recommended)**
1. Go to [qdrant.io/cloud](https://qdrant.io/cloud)
2. Create an account and set up a cluster
3. Use the cloud URL and API key in your environment variables

**Option B: Use Docker on Render**
1. Click **New +** → **Web Service**
2. Connect your repo (or use Docker Hub)
3. Use Docker image: `qdrant/qdrant:latest`
4. Expose port `6333`

### Step 6: Update Configuration for Production

Update your `backend/config.py` to use environment variables for production:

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tender_eval.db")
```

## Deployment on Vercel

**Note**: Vercel is optimized for frontend deployments (Next.js, React, static sites). For Python backend, Render is a better choice. However, you can deploy the Streamlit frontend on Vercel using serverless functions.

### Frontend Deployment on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **Add New** → **Project**
3. Import your GitHub repository
4. Configure:
   - **Framework**: Other
   - **Build Command**: Leave empty (or `pip install -r requirements.txt`)
   - **Output Directory**: `.`

5. Add Environment Variables:
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `BACKEND_URL`: Your Render backend URL

6. Click **Deploy**

**Limitation**: Vercel's free tier has a 10-second execution limit, so it's not ideal for a Streamlit app. Use Render instead.

## Production Checklist

- [ ] Set all API keys in environment variables (never commit `.env`)
- [ ] Update database to PostgreSQL (SQLite doesn't work well in production)
- [ ] Configure Qdrant for production (Qdrant Cloud or self-hosted)
- [ ] Set `STREAMLIT_SERVER_HEADLESS=true` for frontend
- [ ] Add health check endpoints
- [ ] Configure CORS properly for cross-origin requests
- [ ] Set up SSL/HTTPS (automatic on Render and Vercel)
- [ ] Enable monitoring and logging
- [ ] Set up backup strategy for database

## Environment Variables Required

### Backend
```
GROQ_API_KEY=xxx
GEMINI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
QDRANT_HOST=xxx
QDRANT_PORT=6333
DATABASE_URL=postgresql://user:password@host:5432/db
OCR_CONFIDENCE_THRESHOLD=0.80
SEMANTIC_SIMILARITY_PASS_THRESHOLD=0.75
SEMANTIC_SIMILARITY_REVIEW_THRESHOLD=0.50
```

### Frontend
```
GROQ_API_KEY=xxx
GEMINI_API_KEY=xxx
STREAMLIT_SERVER_HEADLESS=true
BACKEND_URL=https://your-backend.onrender.com
```

## Troubleshooting

### Frontend can't connect to backend
- Check `BACKEND_URL` environment variable
- Ensure backend is running on Render
- Check CORS settings in `backend/main.py`

### Database connection errors
- Verify `DATABASE_URL` format
- Ensure PostgreSQL database exists
- Check firewall/security group settings

### Qdrant connection issues
- Verify `QDRANT_HOST` and `QDRANT_PORT`
- Ensure Qdrant service is running
- Check Qdrant Cloud credentials if using cloud

## Useful Links

- [Render Documentation](https://render.com/docs)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-cloud/deploy-your-app)
- [FastAPI on Render](https://render.com/docs/deploy-fastapi)
- [Qdrant Cloud](https://qdrant.io/cloud)
