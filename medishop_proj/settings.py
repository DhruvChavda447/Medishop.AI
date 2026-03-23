import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-medishop-dev-key-change-in-production-2024')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # MediShop Apps — each has its own purpose
    'core_auth',          # Authentication: login, signup, logout, User model extensions
    'home_app',           # Home page
    'shop',               # Product shop + cart + checkout + orders
    'doctors',            # Doctor listing + appointments
    'skin_ai',            # Skin/Eye disease ViT transformer analysis
    'sentiment_check',    # XLM-RoBERTa + mT5 multilingual sentiment
    'portfolio',          # About me + contact form + resume management
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME', 'medishop_db'),
        'USER':     os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'root'),
        'HOST':     os.getenv('DB_HOST', 'localhost'),
        'PORT':     os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Resume password — change this in .env
RESUME_PASSWORD = os.getenv('RESUME_PASSWORD', 'MediShop@Resume2024')

# Production settings
# Support DATABASE_URL env var for Railway/Render/Heroku
_db_url = os.getenv('DATABASE_URL', '')
if _db_url:
    try:
        import dj_database_url as _dj_db
        DATABASES['default'] = _dj_db.config(default=_db_url, conn_max_age=600)
    except Exception:
        pass
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://medishop-ai.onrender.com']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
# ── Email Configuration (Gmail SMTP) ──────────────────────────────
# Set these in your .env file:
#   EMAIL_HOST_USER=your.gmail@gmail.com
#   EMAIL_HOST_PASSWORD=your_app_password   (16-char Gmail App Password)
#   CONTACT_EMAIL=dhruvchavda.intern@gmail.com
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'noreply@medishop.com')
CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', 'dhruvchavda.intern@gmail.com')

# About page edit password
ABOUT_EDIT_PASSWORD = os.getenv('ABOUT_EDIT_PASSWORD', 'MediShop@Resume2024')
