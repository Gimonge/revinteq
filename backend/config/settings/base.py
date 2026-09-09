"""
Revinteq v3 — Base Settings
All config() calls have safe defaults so the file never crashes
when no .env is present (local.py overrides everything anyway).
"""
from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Core — all have defaults so base.py never crashes ────────
SECRET_KEY           = config('DJANGO_SECRET_KEY',    default='change-me-in-production')
ALLOWED_HOSTS        = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
FIELD_ENCRYPTION_KEY = config('FIELD_ENCRYPTION_KEY', default='bG9jYWxkZXZrZXkxMjM0NTY3ODkwMTIzNDU2')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
    'axes',
]

LOCAL_APPS = [
    'apps.tenants',
    'apps.accounts',
    'apps.meta_integration',
    'apps.kommo_integration',
    'apps.whatsapp_tracking',
    'apps.sales',
    'apps.pipeline',
    'apps.metrics',
    'apps.revenue_goals',
    'apps.recommendations',
    'apps.mpesa',
    'apps.sms',
    'apps.bulk_upload',
    'apps.external_api',
    'apps.admin_portal',
    'apps.client_portal',
    'apps.common',
    'apps.customers',
    'apps.crm',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.tenants.middleware.TenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF      = 'config.urls'
WSGI_APPLICATION  = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

# ── Database (overridden to SQLite in local.py) ───────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.mysql',
        'NAME':     config('DB_NAME',     default='revinteq'),
        'USER':     config('DB_USER',     default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 60,
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Cache (overridden to dummy in local.py) ───────────────────
CACHES = {
    'default': {
        'BACKEND':  'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/0'),
        'TIMEOUT':  900,
    }
}

# ── DRF ───────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'apps.external_api.authentication.APIKeyAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS':     'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '200/minute',
    },
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':        True,
    'AUTH_HEADER_TYPES':        ('Bearer',),
}

# ── Celery ────────────────────────────────────────────────────
CELERY_BROKER_URL    = config('CELERY_BROKER_URL',    default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND= config('CELERY_RESULT_BACKEND',default='redis://127.0.0.1:6379/0')
CELERY_TIMEZONE      = 'Africa/Nairobi'
CELERY_ACCEPT_CONTENT= ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULER= 'django_celery_beat.schedulers:DatabaseScheduler'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'sync-meta-ad-data':       {'task': 'apps.meta_integration.tasks.sync_all_accounts',       'schedule': crontab(hour=2,  minute=0)},
    'compute-daily-metrics':   {'task': 'apps.metrics.tasks.compute_all_snapshots',            'schedule': crontab(hour=3,  minute=0)},
    'run-recommendations':     {'task': 'apps.recommendations.tasks.run_all_recommendations',  'schedule': crontab(hour=4,  minute=0)},
    'check-pipeline-velocity': {'task': 'apps.pipeline.tasks.flag_stale_deals',                'schedule': crontab(hour='*/6', minute=0)},
    'check-meta-token-expiry': {'task': 'apps.meta_integration.tasks.check_token_expiry',      'schedule': crontab(hour=8,  minute=0)},
    'cold-deal-sms':           {'task': 'apps.sms.tasks.send_cold_deal_sms',                   'schedule': crontab(hour='*/6', minute=30)},
}

GOOGLE_PLACES_API_KEY = config('GOOGLE_PLACES_API_KEY', default='')

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://localhost:8000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True

# Allow the custom impersonation header from admin portal
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-impersonate-tenant',   # Admin impersonation
]

# ── Meta API ──────────────────────────────────────────────────
META_APP_ID     = config('META_APP_ID',     default='')
META_APP_SECRET = config('META_APP_SECRET', default='')
META_REDIRECT_URI = config('META_REDIRECT_URI', default='http://localhost:8000/api/v1/meta/callback/')
META_SCOPES     = config('META_SCOPES',     default='ads_read,business_management')
META_GRAPH_API_VERSION = 'v20.0'
META_GRAPH_BASE_URL    = f'https://graph.facebook.com/{META_GRAPH_API_VERSION}'

# ── Kommo CRM integration ───────────────────────────────────────
# Each tenant generates their own Long-lived Token inside their own
# Kommo account (Settings -> Integrations -> Keys and scopes -> Generate
# long-lived token) — Kommo's own recommended approach for a private,
# single-account integration. No OAuth exchange, no redirect URI, no
# shared Gimsc-wide credentials (see apps.kommo_integration).
KOMMO_MATCH_WINDOW_MINUTES = 20
KOMMO_MATCH_MAX_RETRIES    = 5

WHATSAPP_WEBHOOK_VERIFY_TOKEN = config('WHATSAPP_WEBHOOK_VERIFY_TOKEN', default='localtoken')

# ── Site ──────────────────────────────────────────────────────
SITE_URL = config('SITE_URL', default='http://localhost:8000')
BUDGET_INCREASE_CAP_PERCENT = 20

# ── Axes (brute-force protection) ─────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME  = timedelta(minutes=30)
AXES_RESET_ON_SUCCESS = True
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ── Internationalisation ──────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Africa/Nairobi'
USE_I18N      = True
USE_TZ        = True

# ── Static & Media ────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
]

SPECTACULAR_SETTINGS = {
    'TITLE':                'Revinteq API v3',
    'DESCRIPTION':          'Multi-tenant Revenue Attribution Platform',
    'VERSION':              '3.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = config('EMAIL_HOST',     default='smtp.gmail.com')
EMAIL_PORT     = config('EMAIL_PORT',     default=587, cast=int)
EMAIL_USE_TLS  = config('EMAIL_USE_TLS',  default=True, cast=bool)
EMAIL_HOST_USER    = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD= config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
