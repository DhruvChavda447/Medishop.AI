# MediShop Pro — Free Deployment Guide

## ✅ Recommended: Railway.app (Free Tier)
**Best option — Django + PostgreSQL, zero config, auto-deploy from GitHub**

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/medishop-pro.git
git push -u origin main
```

### Step 2 — Deploy on Railway
1. Go to **https://railway.app** → Sign up with GitHub (free)
2. Click **New Project → Deploy from GitHub repo**
3. Select your repo → Railway auto-detects Django
4. Click **Add Service → PostgreSQL** — Railway creates DB automatically
5. In your Django service, go to **Variables** tab and add:

```
SECRET_KEY=your-random-secret-key-here-make-it-long
DEBUG=False
DATABASE_URL=${{Postgres.DATABASE_URL}}   ← auto-filled by Railway
ALLOWED_HOSTS=*.up.railway.app
EMAIL_HOST_USER=your.gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
CONTACT_EMAIL=dhruvchavda.intern@gmail.com
RESUME_PASSWORD=YourSecureResumePassword
```

6. Add a **Procfile** (already included):
```
web: gunicorn medishop_proj.wsgi --log-file -
```

7. Railway will auto-deploy → get your URL like `https://medishop.up.railway.app`

---

## 🔑 Gmail App Password Setup (for contact form emails)

1. Go to **myaccount.google.com**
2. Security → Enable **2-Step Verification**
3. Security → **App Passwords**
4. Select app: **Mail**, device: **Other** → name it "MediShop"
5. Copy the 16-character password → paste as `EMAIL_HOST_PASSWORD` in Railway

---

## ⚙️ Run Migrations on Railway

After deploy, open Railway terminal for your Django service:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
```

---

## 🆓 Alternative Free Platforms

### Render.com
1. Connect GitHub repo at **render.com**
2. New → **Web Service** → select repo
3. Build Command: `pip install -r requirements.txt && python manage.py collectstatic --no-input`
4. Start Command: `gunicorn medishop_proj.wsgi`
5. Add **PostgreSQL** database service (free tier)
6. Set environment variables same as Railway

### Heroku (Free tier removed, use Eco ~$5/mo)
```bash
heroku create medishop-pro
heroku addons:create heroku-postgresql:mini
heroku config:set SECRET_KEY=... DEBUG=False ...
git push heroku main
heroku run python manage.py migrate
```

---

## 📦 requirements.txt additions needed
Make sure these are in requirements.txt:
```
gunicorn>=21.0
whitenoise>=6.6
psycopg2-binary>=2.9
dj-database-url>=2.1
```

---

## 🔧 settings.py for Production

Already configured with `whitenoise` for static files.
For Railway/Render, add this to settings.py if not present:

```python
import dj_database_url, os
if os.getenv('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(conn_max_age=600)
```

---

## ✅ Checklist Before Deploy
- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is a long random string (not the default)
- [ ] `ALLOWED_HOSTS` includes your domain
- [ ] Gmail App Password set for contact form emails
- [ ] `python manage.py collectstatic` run
- [ ] `python manage.py migrate` run
- [ ] Superuser created for admin panel
- [ ] Resume uploaded at `/resume/upload/`
