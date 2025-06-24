import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Replace with your actual SECRET_KEY
SECRET_KEY = 'django-insecure-*************************************************'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://127.0.0.1',
                        'http://127.0.0.1:8000/', 'http://localhost:8000/']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # <--- AKONG GI-ADD NI DIRI PARA MAKA-GAMIT KA SA {% load humanize %}
    'django.contrib.humanize',

    # My Apps (Important: Check paths for each app)
    'apps.individual',
    'apps.church',
    'apps.family',
    'apps.payment',
    'apps.account',
    'apps.report',
    'apps.chat',
    'apps.issues',
    'apps.contribution_type',

    # Third-party apps
    # 'django_browser_reload',
    'widget_tweaks',
    'rest_framework',
    'crispy_forms',
    'crispy_tailwind',
    # 'django_tailwind', # Removed as we manually compile Tailwind CSS
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django_browser_reload.middleware.BrowserReloadMiddleware',   # For browser auto-reload
]

ROOT_URLCONF = 'kadamay.urls'

# kadamay/settings.py

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # This is good for project-level templates
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,  # This tells Django to look in app_name/templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.account.context_processors.user_church',
                'apps.account.context_processors.user_permissions_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'kadamay.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'   # Set to your local timezone

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
# Where collectstatic will put files in production (should be outside project root)
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'

# Tell Django where to look for additional static files during development
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # <--- AKOA GI-ADD NI PARA MA-APIL ANG IMONG ROOT STATIC FOLDER
    # This is for static files specific to your 'theme' app/folder
    BASE_DIR / 'theme' / 'static',
    # You can add more paths here if you have other project-level static folders
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model if applicable
# AUTH_USER_MODEL = 'account.User' # Uncomment if you have a custom User model

# Login/Logout Redirect URLs
LOGIN_URL = 'account:login'   # Name of the login URL
LOGIN_REDIRECT_URL = 'home'   # Name of the URL to redirect to after successful login
# Name of the URL to redirect to after logout
LOGOUT_REDIRECT_URL = 'account:login'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'
