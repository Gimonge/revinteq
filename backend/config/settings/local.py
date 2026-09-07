"""
Revinteq v3 — Local Development Settings
SQLite database — no MySQL, Redis, or external services required.

Usage:
    python manage.py runserver --settings=config.settings.local
    python manage.py migrate   --settings=config.settings.local

Or set in your shell once:
    export DJANGO_SETTINGS_MODULE=config.settings.local
"""
from .base import *

# ── Override ALL config() calls — no .env needed locally ─────
SECRET_KEY   = 'local-dev-secret-key-revinteq-not-for-production-xyz'
DEBUG        = True
ALLOWED_HOSTS= ['localhost', '127.0.0.1', '0.0.0.0', '*']

# ── SQLite — no MySQL install needed ─────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':    BASE_DIR / 'db.sqlite3',
    }
}

# ── No Redis needed — tasks run inline ───────────────────────
CELERY_TASK_ALWAYS_EAGER    = True
CELERY_TASK_EAGER_PROPAGATES= True
CELERY_BROKER_URL           = 'memory://'
CELERY_RESULT_BACKEND       = 'cache+memory://'

# ── Dummy cache ───────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# ── CORS — allow everything locally ──────────────────────────
CORS_ALLOW_ALL_ORIGINS  = True
CORS_ALLOWED_ORIGINS    = ['http://localhost:5173', 'http://localhost:8000']

# ── Encryption ────────────────────────────────────────────────
FIELD_ENCRYPTION_KEY = 'bG9jYWxkZXZrZXkxMjM0NTY3ODkwMTIzNDU2'

# ── Meta — dummy values for local dev ────────────────────────
META_APP_ID               = 'local-meta-app-id'
META_APP_SECRET           = 'local-meta-app-secret'
META_REDIRECT_URI         = 'http://localhost:8000/api/v1/meta/callback/'
META_SCOPES               = 'ads_read,business_management'
WHATSAPP_WEBHOOK_VERIFY_TOKEN = 'localtoken'
SITE_URL                  = 'http://localhost:8000'

# ── Email — print to terminal, no SMTP needed ────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── No password complexity rules locally ─────────────────────
AUTH_PASSWORD_VALIDATORS = []

# ── Remove axes (brute-force protection — not needed locally) ─
INSTALLED_APPS  = [a for a in INSTALLED_APPS  if a != 'axes']
MIDDLEWARE       = [m for m in MIDDLEWARE       if 'axes' not in m]
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

# ── Remove debug_toolbar (install it if you want it) ─────────
INSTALLED_APPS  = [a for a in INSTALLED_APPS  if a != 'debug_toolbar']
MIDDLEWARE       = [m for m in MIDDLEWARE       if 'debug_toolbar' not in m]

print("\033[92m⚡ LOCAL settings — SQLite, no Redis, no MySQL, no .env needed\033[0m")
