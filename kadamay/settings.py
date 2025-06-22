# settings.py

import os
import sys
# from pathlib import Path # Not explicitly used for BASE_DIR in the original code, so keeping it commented out for consistency.

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# --- FIX: Corrected typo in os.path.dirname and oos.path.dirname ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add apps directory to Python path
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-kadamay-mortuary-system-development-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True # This is the correct placement for DEBUG

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # --- IMPORTANT: Keep only one 'theme' app, the one we created in 'apps/' ---
    'apps.theme', # This is your custom theme app where static files are.

    # Project apps
    'apps.individual',
    'apps.church',
    'apps.family',
    'apps.payment',
    'apps.account',
    'apps.report',
    'apps.chat',
    'apps.issues',
    'apps.contribution_type',

    # --- REMOVED: 'tailwind' and the second 'theme' app if they are related to django-tailwind,
    # --- as we are using postcss directly for compilation. ---
    # 'tailwind', # Usually from django-tailwind. Remove if not needed for other purposes.
    # 'theme',    # This seems like a duplicate or leftover from django-tailwind. Remove.

    'django_browser_reload', # Keep this for auto-reloading
    'widget_tweaks', # Keep if you are using it
    'rest_framework', # Keep if you are using it
    'crispy_forms', # Keep if you are using it
    'crispy_tailwind', # Keep if you are using it
]

# --- REMOVED: These settings are typically for django-tailwind, which we are not using for compilation. ---
# TAILWIND_APP_NAME = 'theme'
# NPM_BIN_PATH = r"C:\Program Files\nodejs\npm.cmd"

# --- CRISPY FORMS SETTINGS (These are fine) ---
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

ROOT_URLCONF = 'kadamay.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # --- FIX: Use os.path.join for BASE_DIR / 'templates' for consistency ---
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.account.context_processors.user_church',
                'apps.account.context_processors.user_roles',
                'kadamay.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'kadamay.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'), # Use os.path.join here too
    }
}

# Password validation
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

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'  # Philippines timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
# --- FIX: Removed redundant STATIC_ROOT definition and consolidated STATICFILES_DIRS ---
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # REMOVED (redundant)

STATICFILES_DIRS = [
    # This path is for a 'static' folder directly under your project root (e.g., kadamay_project/static/)
    # Keep it if you have other static files there not tied to a specific app.
    # os.path.join(BASE_DIR, 'static'), 
    
    # --- FIX: Corrected path for the 'theme' app's static files ---
    # This points to E:\my_project\kadamay_project\apps\theme\static\
    os.path.join(BASE_DIR, 'apps', 'theme', 'static'), 
]

# This STATIC_ROOT is for the 'collectstatic' command, used in production.
# Keep only one.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected') 


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Email settings (for development - prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@kadamay.org'

# --- REMOVED: Redundant DEBUG = True ---
# DEBUG = True # This is redundant, it's already defined above. You can remove this.