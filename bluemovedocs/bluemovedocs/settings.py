"""
Django settings for bluemovedocs project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'p))=+%0jt3=tzv)i$vscj0+o-rypw^br6=ip+fre=mgmaidjf&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# 배포 시 도메인 입력
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',
    'notice',
    'box',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'users',
    'ckeditor',
    'django.forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bluemovedocs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'home', 'templates')],
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

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

CKEDITOR_BASEPATH = "/static/ckeditor/ckeditor/"

WSGI_APPLICATION = 'bluemovedocs.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'home', 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files

MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'home', 'media')

# allauth

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = '/'

SESSION_COOKIE_AGE = 3600

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

SESSION_SAVE_EVERY_REQUEST = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            # 'https://www.googleapis.com/auth/drive', # 블루무버 계정 로그인 시에만 적용되도록 설정해두었음
            # 'https://www.googleapis.com/auth/documents', # 블루무버 계정 로그인 시에만 적용되도록 설정해두었음
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'offline',
            # 'approval_prompt': 'force', # force로 설정 시 로그인할 때마다 Google 계정 액세스 관련 프롬프트 표시됨
            'prompt': 'select_account'
            # 'hd': 'bluemove.or.kr', # 블루무버 계정 로그인 시에만 적용되도록 설정해두었음
        }
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True

SOCIALACCOUNT_EMAIL_REQUIRED = True

SOCIALACCOUNT_EMAIL_VERIFICATION = "mandatory"

ACCOUNT_USERNAME_REQUIRED = True

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_USERNAME_BLACKLIST = [
    'bluewavebluemove',
    'bluewavebluemove-secretariat',
    'bluewavebluemove-management',
    'bluewavebluemove-posongvi',
    'bluewavebluemove-barrierfree',
    'bluewavebluemove_secretariat',
    'bluewavebluemove_management',
    'bluewavebluemove_posongvi',
    'bluewavebluemove_barrierfree',
    'bluewavebluemove.secretariat',
    'bluewavebluemove.management',
    'bluewavebluemove.posongvi',
    'bluewavebluemove.barrierfree',
    'bluewavebluemove+secretariat',
    'bluewavebluemove+management',
    'bluewavebluemove+posongvi',
    'bluewavebluemove+barrierfree',
    'bluewavebluemove-management-team',
    'bluewavebluemove-posongvi-team',
    'bluewavebluemove-barrierfree-team',
    'bluewavebluemove_management_team',
    'bluewavebluemove_posongvi_team',
    'bluewavebluemove_barrierfree_team',
    'bluewavebluemove.management.team',
    'bluewavebluemove.posongvi.team',
    'bluewavebluemove.barrierfree.team',
    'bluewavebluemove+management+team',
    'bluewavebluemove+posongvi+team',
    'bluewavebluemove+barrierfree+team',
    'bluemove',
    'bluemove-secretariat',
    'bluemove-management',
    'bluemove-posongvi',
    'bluemove-barrierfree',
    'bluemove_secretariat',
    'bluemove_management',
    'bluemove_posongvi',
    'bluemove_barrierfree',
    'bluemove.secretariat',
    'bluemove.management',
    'bluemove.posongvi',
    'bluemove.barrierfree',
    'bluemove+secretariat',
    'bluemove+management',
    'bluemove+posongvi',
    'bluemove+barrierfree',
    'bluemove-management-team',
    'bluemove-posongvi-team',
    'bluemove-barrierfree-team',
    'bluemove_management_team',
    'bluemove_posongvi_team',
    'bluemove_barrierfree_team',
    'bluemove.management.team',
    'bluemove.posongvi.team',
    'bluemove.barrierfree.team',
    'bluemove+management+team',
    'bluemove+posongvi+team',
    'bluemove+barrierfree+team',
    'secretariat',
    'management',
    'posongvi',
    'barrierfree',
    'management-team',
    'posongvi-team',
    'barrierfree-team',
    'management_team',
    'posongvi_team',
    'barrierfree_team',
    'management.team',
    'posongvi.team',
    'barrierfree.team',
    'management+team',
    'posongvi+team',
    'barrierfree+team',
]

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Format', 'FontSize'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
            ['TextColor', 'BGColor'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Link', 'Unlink'],
            ['Smiley', 'SpecialChar'],
            ['Find', 'Replace'],
            ['Undo', 'Redo'],
        ],
        'extraPlugins': ','.join([
            'autolink',
        ]),
        'tabSpaces': 4,
        'width': 'auto',
        'toolbarCanCollapse': True,
    },
}