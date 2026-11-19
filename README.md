# MediShop Pro — AI Healthcare Platform

Full-stack Django + PostgreSQL platform with Transformer NLP, Vision AI, and DNN inference.

---

## Quick Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=medishop
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
RESUME_PASSWORD=YourResumePassword2024
```

### 3. Run migrations
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**OR** use the SQL script directly:
```bash
psql -U postgres -d medishop -f create_tables.sql
python manage.py migrate --run-syncdb
```

---

## Pages

| URL | Page | Description |
|-----|------|-------------|
| `/` | Home | AI pipeline overview, project modules |
| `/shop/` | Medicine Shop | XLM-RoBERTa NLP ranked, category-wise |
| `/doctors/` | Find Doctors | NLP ranked per specialty |
| `/health/` | Health AI | PyTorch DNN cardiovascular risk |
| `/skin/` | Skin ViT | Vision Transformer image analysis |
| `/sentiment/` | Check Sentiment | XLM-R → Prompt → mT5 pipeline |
| `/about/` | About & Contact | Portfolio + contact form + resume |
| `/resume/upload/` | Resume Manager | Password-protected upload |

---

## Resume Management (No Redeployment Needed)

1. Go to `/resume/upload/`
2. Enter your password (set in `.env` as `RESUME_PASSWORD`)
3. Upload new PDF
4. All users instantly see the new resume on `/about/`

---

## Training Your Own ViT

See the "How to Train" section at `/skin/` for full instructions.

Datasets: ISIC (skin), ODIR-5K (eye), Messidor (diabetic retinopathy)

---

## Apps

| App | Purpose |
|-----|---------|
| `home_app` | Landing page |
| `shop` | Products, cart, checkout, orders |
| `doctors` | Doctor listing + appointments |
| `health_ai` | DNN health risk prediction |
| `skin_ai` | ViT image classification |
| `sentiment_check` | XLM-RoBERTa + mT5 pipeline |
| `portfolio` | About, contact form, resume manager |
| `core_auth` | Login, signup, dashboard |
