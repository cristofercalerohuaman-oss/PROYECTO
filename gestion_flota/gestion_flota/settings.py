import os
from pathlib import Path

# --- RUTAS BASE ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = 'django-insecure-(3b9th=9^vl001j65^k05n@5vrj-ha_htjb)8tnjs%d_ccu&@b'  
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'unemergent-nonascendently-nickole.ngrok-free.dev','.vercel.app',
    'proyecto-theta-nine.vercel.app',
    'proyecto-git-main-cristofers-projects-637cb905.vercel.app',
    'proyecto-gvvpo4zmu-cristofers-projects-637cb905.vercel.app',
]
CSRF_TRUSTED_ORIGINS = [
    'https://unemergent-nonascendently-nickole.ngrok-free.dev',
    # añade aquí https://<tu-otro-subdominio-ngrok>
]
# --- APPS INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    # Tu app
    'vehiculos',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# --- ROOT ---
ROOT_URLCONF = 'flota_site.urls'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # <-- carpeta para templates globales
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

# --- WSGI ---
WSGI_APPLICATION = 'flota_site.wsgi.application'

# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

# --- PASSWORDS ---
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

# --- IDIOMA Y ZONA HORARIA ---
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# --- STATIC ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# --- LOGIN Y LOGOUT ---
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'   # a dónde va después de iniciar sesión
LOGOUT_REDIRECT_URL = '/login/'      # a dónde va después de cerrar sesión
