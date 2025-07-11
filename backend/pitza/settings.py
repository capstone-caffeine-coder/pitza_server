"""
Django settings for pitza project.

Generated by 'django-admin startproject' using Django 5.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-v0yld&tv!_b!yxr8_h-#6p&$b$0*&ep3+7)u9bt_)qeb5_3km#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1', 'web']

# session logs out when user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'donations.apps.DonationsConfig',
    'minio_storage',  
    'drf_yasg',
    'corsheaders',
    'chat',
    'rest_framework',
    'login',
    'board',
    'services',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'pitza.middleware.DisableCSRFMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

ROOT_URLCONF = 'pitza.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pitza.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST'), # Use the service name 'db'
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            # Example: Ensures UTF8MB4 is used for the connection
            'charset': 'utf8mb4', 
        },
    },
    'test': {
        'NAME': f"test_{os.environ.get('DB_NAME')}",
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'

# Media files (User-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # Or os.path.join(BASE_DIR, 'media')

# MinIO Storage Settings

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STORAGES = {
    "default": {
        "BACKEND": "minio_storage.storage.MinioMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "minio_storage": { 
        "BACKEND": "minio_storage.storage.MinioStorage",
        "ENDPOINT": os.environ.get('MINIO_ENDPOINT'),
        "ACCESS_KEY": os.environ.get('MINIO_ACCESS_KEY'),
        "SECRET_KEY": os.environ.get('MINIO_SECRET_KEY'),
        "USE_HTTPS": os.environ.get('MINIO_USE_HTTPS'),
        "BUCKET_NAME": "pitza-media",
        "AUTO_CREATE_BUCKET": True,
    },
}

MINIO_STORAGE_BACKENDS = {
    "default": {
        "bucket_name": "pitza-media",
    },
}

MINIO_STORAGE_ENDPOINT = os.environ.get('MINIO_ENDPOINT', ':9000')
MINIO_STORAGE_ACCESS_KEY = os.environ.get('MINIO_STORAGE_ACCESS_KEY')
MINIO_STORAGE_SECRET_KEY = os.environ.get('MINIO_STORAGE_SECRET_KEY')
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True
MINIO_STORAGE_USE_HTTPS = False
MINIO_STORAGE_MEDIA_BUCKET_NAME = 'pitza-media'
MINIO_STORAGE_STATIC_BUCKET_NAME = 'pitza-static'
MINIO_STORAGE_MEDIA_USE_PRESIGNED = False
MINIO_STORAGE_STATIC_USE_PRESIGNED = False

MINIO_PUBLIC_URL_BASE = 'http://localhost:9000'
MINIO_STORAGE_ENDPOINT_IS_PUBLIC = True

# Add CORS settings for MinIO
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
]

# 세션/CSRF 쿠키 설정 (HTTP 사용 시 개발용)
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = False


# 배포 후 HTTPS 환경
# SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

AUTH_USER_MODEL= 'login.User'

# 공공데이터, 카카오 REST_API
OPENAPI_SERVICE_KEY = os.getenv('OPENAPI_SERVICE_KEY')
KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")