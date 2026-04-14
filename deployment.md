# 🚀 Deployment Guide — Book Insight (Free Hosting)

Deploy the full Book Insight app for free so anyone can test it via a public link.

**Recommended stack:**
- **Backend (Django API)** → [Render](https://render.com) — free web service
- **Frontend (React)** → [Vercel](https://vercel.com) — free static hosting

---

## 📋 Prerequisites

- A [GitHub](https://github.com) account with your project pushed to a repository
- A [Render](https://render.com) account (sign up free)
- A [Vercel](https://vercel.com) account (sign up free with GitHub)

---

## Part 1 — Deploy the Backend on Render

### Step 1 — Add a `requirements.txt` check

Make sure `backend/requirements.txt` includes `gunicorn` and `whitenoise`:

```
gunicorn>=21.2
whitenoise>=6.6
```

Add them if missing:

```bash
cd backend
pip install gunicorn whitenoise
pip freeze | grep -E "gunicorn|whitenoise" >> requirements.txt
```

### Step 2 — Configure Django for production

Open `backend/book_insight/settings.py` and make these changes:

**a) Allow the Render host and read settings from environment:**

```python
import os
from pathlib import Path

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',   # ← add this
]
```

**b) Add WhiteNoise for static files (after `django.middleware.security.SecurityMiddleware`):**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← add this second
    ...
]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**c) Update CORS to allow your future Vercel frontend URL:**

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://your-app-name.vercel.app",   # ← replace with your Vercel URL after deploying frontend
]
```

### Step 3 — Create a `render.yaml` (optional but convenient)

Create `render.yaml` in the **project root**:

```yaml
services:
  - type: web
    name: book-insight-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt && python manage.py migrate && python manage.py load_sample_books && python manage.py collectstatic --noinput"
    startCommand: "cd backend && gunicorn book_insight.wsgi:application --bind 0.0.0.0:$PORT"
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: ".onrender.com"
```

### Step 4 — Deploy on Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub account and select the `book_insight` repository
3. Set the following manually (if not using `render.yaml`):

   | Field | Value |
   |-------|-------|
   | **Name** | `book-insight-backend` |
   | **Root Directory** | `backend` |
   | **Environment** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt && python manage.py migrate && python manage.py load_sample_books && python manage.py collectstatic --noinput` |
   | **Start Command** | `gunicorn book_insight.wsgi:application --bind 0.0.0.0:$PORT` |

4. Under **Environment Variables**, add:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Any long random string (e.g. `myrandomsecretkey12345678`) |
   | `DEBUG` | `False` |

5. Click **Create Web Service** and wait for the build to finish (~3–5 min).
6. Copy the URL shown at the top — it looks like: `https://book-insight-backend.onrender.com`

> ⚠️ **Note:** Free Render services **spin down after 15 minutes of inactivity**. The first request after sleep takes ~30 seconds to wake up. This is normal for free tier.

---

## Part 2 — Deploy the Frontend on Vercel

### Step 1 — Point the frontend to your Render backend

Open `frontend/src/api/index.js` (or wherever `axios` base URL is set) and change:

```js
// Before
const API_BASE_URL = 'http://localhost:8000/api';

// After
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
```

This lets you set the API URL via an environment variable on Vercel.

### Step 2 — Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New → Project**
2. Import your GitHub repository (`book_insight`)
3. Set **Root Directory** to `frontend`
4. Vercel auto-detects React (Create React App) — leave defaults
5. Under **Environment Variables**, add:

   | Key | Value |
   |-----|-------|
   | `REACT_APP_API_URL` | `https://book-insight-backend.onrender.com/api` |

6. Click **Deploy** — your app will be live at `https://your-app-name.vercel.app`

### Step 3 — Update CORS on the backend

Once you know your Vercel URL (e.g. `https://book-insight-abc123.vercel.app`), go back to **Render → Environment** and add:

```
CORS_ALLOWED_ORIGINS=https://book-insight-abc123.vercel.app
```

Or update `settings.py` to read from an environment variable:

```python
import os

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000'
).split(',')
```

Then redeploy the backend.

---

## ✅ Testing Your Live App

1. Visit your Vercel URL (e.g. `https://book-insight-abc123.vercel.app`)
2. Click **"🔄 Scrape Books"** on the dashboard — the backend will load the 43 sample books
3. Click any book to view AI summary and sentiment
4. Try the **Ask AI** page to test the RAG question-answering feature
5. Share your Vercel link with anyone! 🎉

---

## 🔗 Share the Link

Your sharable link is your Vercel URL:

```
https://your-app-name.vercel.app
```

Share this link in your portfolio, resume, LinkedIn, or with recruiters for a live demo.

---

## 🐛 Common Issues

| Issue | Fix |
|-------|-----|
| Backend gives `CORS error` | Add Vercel URL to `CORS_ALLOWED_ORIGINS` in Render environment variables |
| Backend shows `DisallowedHost` | Add `.onrender.com` to `ALLOWED_HOSTS` in `settings.py` |
| Frontend API calls fail | Make sure `REACT_APP_API_URL` points to your full Render URL including `/api` |
| Render build fails on `chromadb` | `chromadb` requires Python 3.10+; make sure Render's Python version is set correctly |
| Data disappears on redeploy | SQLite and ChromaDB are stored on Render's ephemeral disk; click "Scrape Books" again after each deploy |
| Wake-up delay on first request | Free Render services sleep after 15 min; first request takes ~30 sec — this is expected |

---

## 💡 Alternative Free Platforms

| Platform | Backend | Frontend | Notes |
|----------|---------|----------|-------|
| **Railway** | ✅ Free starter | ✅ Static hosting | 500 free hours/month |
| **Fly.io** | ✅ Free tier | — | More config needed |
| **Netlify** | — | ✅ Free | Alternative to Vercel for frontend |
| **GitHub Pages** | — | ✅ Free | Requires `homepage` in `package.json` and routing workaround |

---

> 💡 **Tip:** Render + Vercel is the easiest free combination for a Django + React project with zero credit card required.
