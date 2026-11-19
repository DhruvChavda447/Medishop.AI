import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-medicare-ai-production-ready-key-2026')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]
if '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '.onrender.com', '.up.railway.app'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # MediCare.AI Active Core Modules
    'core_auth',          # Authentication & User Dashboard
    'home_app',           # Platform Architecture & Home Overview
    'doctors',            # NLP Doctor Ranking, Checkup Billing & RAG Vector DB + Bill OCR Chat
    'sentiment_check',    # Multilingual XLM-RoBERTa + Aspect Sentiment Analysis & Interactive Chat
    'portfolio',          # Developer Portfolio, Resume Manager & Contact
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'medishop_proj.urls'
WSGI_APPLICATION = 'medishop_proj.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

# ── Smart Database Configuration (PostgreSQL via DATABASE_URL / DB_HOST, or automatic SQLite fallback) ──
_db_url = os.getenv('DATABASE_URL', '').strip()
_db_host = os.getenv('DB_HOST', '').strip()

if _db_url:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=int(os.getenv('DB_CONN_MAX_AGE', '600')),
            ssl_require=os.getenv('DB_SSL_REQUIRE', 'False').lower() in ('true', '1'),
        )
    }
elif _db_host:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'medishop_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
            'HOST': _db_host,
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
        }
    }
else:
    # Automatic SQLite fallback so local runs & zero-DB Render builds never crash
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

FORMSPREE_URL = os.getenv('FORMSPREE_URL', 'https://formspree.io/f/xzdjlepp')
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Use CompressedStaticFilesStorage so missing manifest references never crash Render builds
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

RESUME_PASSWORD = os.getenv('RESUME_PASSWORD', 'MediShop@Resume2024')
ABOUT_EDIT_PASSWORD = os.getenv('ABOUT_EDIT_PASSWORD', 'MediShop@Resume2024')

# ── CSRF & HTTPS Configuration for Any New Render / Railway URL ──
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
_render_host = os.getenv('RENDER_EXTERNAL_HOSTNAME', '').strip()
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')
_custom_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
if _custom_origins:
    for origin in _custom_origins.split(','):
        if origin.strip():
            CSRF_TRUSTED_ORIGINS.append(origin.strip())

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Email Configuration ──
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@medicare-ai.com')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'dhruvchavda.intern@gmail.com')
