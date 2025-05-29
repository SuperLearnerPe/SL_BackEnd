from pathlib import Path
import environ
import dj_database_url
import os
from dotenv import load_dotenv

load_dotenv()

env = environ.Env()
environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = [
    'backend-superlearner-1083661745884.us-central1.run.app',
    'localhost',
    '127.0.0.1',
    '0.0.0.0'
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    'api',
    'frontend',
    'volunteers',
    'students',
    'parents',
    'metricas',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SuperLearner_Peru.urls'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SuperLearner_Peru.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = False

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------- CORS CONFIGURATION -----------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:5501",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://192.168.56.1:3000",
    "http://192.168.0.103:3000",
    "http://172.22.0.1:3000",
    "http://0.0.0.0:8000",
    "https://backend-superlearner-1083661745884.us-central1.run.app",
    "https://front-as-sl-1083661745884.southamerica-west1.run.app",
]

CORS_URLS_REGEX = r'^/(api|swagger|redoc)/.*$'

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'x-api-key',
]

CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_EXPOSE_HEADERS = [
    'content-disposition',
    'content-type',
    'authorization',
]

CORS_PREFLIGHT_MAX_AGE = 86400

# ----------- CSRF CONFIGURATION -----------
CSRF_TRUSTED_ORIGINS = [
    'https://front-as-sl-1083661745884.southamerica-west1.run.app',
    'https://backend-superlearner-1083661745884.us-central1.run.app',
]

# ----------- SECURITY CONFIGURATION -----------
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = False

# ----------- EMAIL CONFIGURATION -----------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_FAIL_SILENTLY = False

# ----------- SWAGGER CONFIGURATION -----------
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Ingresa tu token en formato: Token <tu_token_aqui>'
        }
    },
    'USE_SESSION_AUTH': False,
    'SECURITY_REQUIREMENTS': [{'Token': []}],
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    'DEFAULT_MODEL_RENDERING': 'model',
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'VALIDATOR_URL': None,
    'CACHE_TIMEOUT': 0,
    'DEFAULT_API_URL': 'https://backend-superlearner-1083661745884.us-central1.run.app/api',
    'SPEC_URL': '/?format=openapi',
}




# ----------- DRF CONFIGURATION -----------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}
