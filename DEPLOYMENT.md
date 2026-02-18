# 🚀 Deployment Guide — MindMate

Deploy for **$0** using **Render** (backend) + **Vercel** (frontend).

---

## Prerequisites

1. **Groq API Key** — Get one free at [console.groq.com](https://console.groq.com/)
2. **GitHub Account** — Push your code to a GitHub repository
3. **Render Account** — Sign up at [render.com](https://render.com) (free)

4. **Vercel Account** — Sign up at [vercel.com](https://vercel.com) (free)

---

## Step 1: Deploy Backend on Render (Free)

### Option A: One-Click with render.yaml (Recommended)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and configure everything
5. Set the `GROQ_API_KEY` environment variable when prompted
6. Click **Apply** — your backend will be live at `https://mindmate-api.onrender.com`

### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `mindmate-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Add environment variables:
   | Key | Value |
   |-----|-------|
   | `GROQ_API_KEY` | Your Groq API key |
   | `GROQ_MODEL` | `llama-3.1-8b-instant` |
   | `BACKEND_CORS_ORIGINS` | `https://your-app.vercel.app` |
5. Click **Create Web Service**

> **Note**: Render free tier spins down after 15 min of inactivity. First request after idle may take ~30s.

---

## Step 2: Deploy Frontend on Vercel (Free)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard) → **Add New** → **Project**
2. Import your GitHub repo
3. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
4. Add environment variable:
   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://mindmate-api.onrender.com` |
5. Click **Deploy**

Your frontend will be live at `https://your-project.vercel.app`

---

## Step 3: Update CORS (Important!)

After deploying the frontend, update the backend's CORS setting:

1. Go to your Render service → **Environment**
2. Set `BACKEND_CORS_ORIGINS` to your Vercel URL:
   ```
   https://your-project.vercel.app
   ```
3. Render will auto-redeploy

---

## Local Development

```bash
# Backend
cd backend
cp .env.example .env    # Edit with your GROQ_API_KEY
pip install -r requirements.txt
uvicorn api:app --reload

# Frontend (separate terminal)
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

---

## Docker (Optional)

```bash
# Set your API key
export GROQ_API_KEY=gsk_your_key_here

# Build and run
docker-compose up --build
```

Open http://localhost:3000

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ | — | Your Groq API key |
| `GROQ_MODEL` | ❌ | `llama-3.1-8b-instant` | LLM model to use |
| `BACKEND_CORS_ORIGINS` | ❌ | `http://localhost:3000` | Comma-separated allowed origins |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ❌ | `http://localhost:8000` | Backend API URL |

---

## Architecture

```
[Vercel - Free]           [Render - Free]          [Groq Cloud - Free]
┌─────────────┐           ┌──────────────┐         ┌──────────────┐
│  Next.js    │  ──POST──▶│  FastAPI     │──API──▶ │  Groq LLM    │
│  Frontend   │◀─JSON────│  + LangGraph │◀───────│  (llama-3.1) │
└─────────────┘           └──────────────┘         └──────────────┘
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors | Check `BACKEND_CORS_ORIGINS` matches your frontend URL exactly |
| Backend 503 | Graph failed to initialize — check Groq API key is valid |
| Slow first load | Render free tier cold start (~30s) — this is normal |
| Build fails | Ensure `GROQ_API_KEY` is set in Render environment |
| Vercel 404 / Loading | Ensure **Root Directory** is set to `frontend` in Vercel settings |
| Vercel "Failed to fetch" | Ensure `NEXT_PUBLIC_API_URL` is set to your Render backend URL |
