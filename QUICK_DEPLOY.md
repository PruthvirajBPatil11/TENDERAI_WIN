# Quick Deployment Commands

## 1. Render Backend Deployment

```bash
# Manual deployment (one-time)
curl -X POST https://api.render.com/deploy/srv-YOUR_SERVICE_ID?key=YOUR_RENDER_API_KEY
```

## 2. Render Frontend Deployment

Same as backend, just with different service ID.

## 3. GitHub Push to Auto-Deploy

```bash
git add .
git commit -m "Deploy updates"
git push origin main
```

## 4. Check Deployment Status

- Render: https://dashboard.render.com
- Vercel: https://vercel.com/dashboard

## 5. View Logs

```bash
# Render logs
render logs -s tender-eval-backend
render logs -s tender-eval-frontend

# Vercel logs
vercel logs
```

## Environment Variables on Render

Set these in your Render dashboard:
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DATABASE_URL` (PostgreSQL connection string)
- `QDRANT_HOST` (Qdrant Cloud URL or your instance)
- `QDRANT_PORT`

## Connecting Services

After deployment, update your frontend to point to backend:

In Render dashboard:
- Set `BACKEND_URL=https://tender-eval-backend.onrender.com` for frontend service
