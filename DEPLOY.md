# MediCare.AI — A-to-Z GitHub, PostgreSQL Database & Render Deployment Guide

This guide walks you step-by-step (`A to Z`) through pushing this updated project to a **new GitHub repository**, creating a **new PostgreSQL database on Render** (or Neon/Supabase), and deploying your **new Render Web Service** without errors.

## 1. Push Updated Project to a New GitHub Repository

1. Unzip `MediCare_AI_RAG_Final.zip` on your computer and open PowerShell / Terminal inside the `medishop_proj` folder (the folder containing `manage.py`, `requirements.txt`, `build.sh`, and `render.yaml`).
2. Go to **https://github.com/new** and create a new repository (for example: `medicare-ai-rag`). Do **not** check "Add a README".
3. Run these commands in your terminal inside `medishop_proj`:

```bash
git init
git add .
git commit -m "Refactor MediCare.AI: RAG Vector DB, Bill OCR Chat, Multilingual Sentiment & Montserrat UI"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/medicare-ai-rag.git
git push -u origin main
```

## 2. Option A: One-Click Blueprint Deploy on Render (`render.yaml`)

Because `render.yaml` and `build.sh` are already pre-configured inside the project root:

1. Log in to **https://dashboard.render.com**.
2. Click **New +** → **Blueprint**.
3. Connect your new GitHub repository (`medicare-ai-rag`).
4. Render will automatically detect `render.yaml`, create the **`medicare-ai-db` PostgreSQL database**, link `DATABASE_URL`, run `./build.sh` (`pip install`, `collectstatic`, `migrate`), and launch your live site!

## 3. Option B: Manual Step-by-Step Setup on Render (Web Service + PostgreSQL)

If you prefer setting up the database and web service manually on Render:

### Step 3.1 — Create New PostgreSQL Database on Render
1. On Render Dashboard, click **New +** → **PostgreSQL**.
2. **Name**: `medicare-ai-db`
3. **Region**: Singapore (or nearest to you)
4. **Instance Type**: `Free`
5. Click **Create Database**.
6. Wait 1 minute until status is **Available**, then copy the **Internal Database URL** (starts with `postgresql://...`).

### Step 3.2 — Create New Web Service on Render
1. Click **New +** → **Web Service** and select your new GitHub repository (`medicare-ai-rag`).
2. Configure the service settings:
   - **Name**: `medicare-ai-rag` (this becomes your new URL: `https://medicare-ai-rag.onrender.com`)
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh` *(or `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate --no-input`)*
   - **Start Command**: `python manage.py migrate --noinput && gunicorn medishop_proj.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
3. Scroll down to **Environment Variables** and add:

| Key | Value |
| :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` |
| `DEBUG` | `False` |
| `SECRET_KEY` | `medicare-ai-prod-secret-key-2026-random-998877` |
| `ALLOWED_HOSTS` | `*` |
| `DATABASE_URL` | *(Paste your Render PostgreSQL Internal Database URL here)* |
| `GEMINI_API_KEY` | *(Optional: Paste your Google Gemini API key for live Gemini-2.5-Flash RAG responses)* |
| `GROQ_API_KEY` | *(Optional: Paste your Groq API key for live Llama-3.3-70B RAG responses)* |

4. Click **Deploy Web Service**.

## 4. Why This Project Will Not Crash on Render (Fixes Applied)

- **Smart Database Fallback**: Uses `DATABASE_URL` (PostgreSQL) when set, and automatically falls back to SQLite (`db.sqlite3`) during build/collectstatic or local testing if `DATABASE_URL` is absent.
- **Dynamic CSRF Trusted Origins**: Automatically trusts `https://*.onrender.com` and `RENDER_EXTERNAL_HOSTNAME`, preventing `403 CSRF Verification Failed` on any new Render link.
- **Resilient Static Files**: Uses `whitenoise.storage.CompressedStaticFilesStorage` so `collectstatic` never crashes on manifest errors.
- **Auto-Migration on Boot**: Both `build.sh` and `Procfile` run `python manage.py migrate --noinput` automatically so all tables (`doctors_appointment`, `doctors_medicalbill`, `sentiment_check_sentimentlog`, `portfolio_aboutprofile`, `auth_user`) exist before traffic arrives.
