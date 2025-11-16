import os
from pathlib import Path

# --- RUTAS BASE ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = 'django-insecure-(3b9th=9^vl001j65^k05n@5vrj-ha_htjb)8tnjs%d_ccu&@b'
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.vercel.app', '.tudominio.com', 'tu-ip-de-servidor', 'proyecto-theta-nine.vercel.app','proyecto-git-main-cristofers-projects-637cb905.vercel.app',]


# --- APPS INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'import_export',
    # Tu app
    'vehiculos',
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Gestion_Flota',
        'USER': 'flota_user',
        'PASSWORD': 'FlotaAdmin123!', # <-- ¡La nueva contraseña!
        'HOST': 'localhost',
        'PORT': '5432',
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
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
# --- LOGIN Y LOGOUT ---
# settings.py (fragmento)
LOGIN_REDIRECT_URL = 'vehiculos:dashboard'   # a dónde va tras login
LOGOUT_REDIRECT_URL = 'vehiculos:dashboard'  # a dónde va tras logout (si no se usa next_page)
LOGIN_URL = 'login'                           # nombre de la vista login
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Si usás ngrok u otros hosts externos (evita error CSRF Trusted origin)
# sustituí con tu dominio ngrok exacto cuando tests: ej 'https://abcd1234.ngrok-free.app'
CSRF_TRUSTED_ORIGINS = [
    # ejemplo genérico:
    'http://127.0.0.1',
    'http://localhost',
    # agrega aquí el host de ngrok si lo usás (incluye https://)
    # 'https://tu-subdominio.ngrok-free.app',
    "https://unemergent-nonascendently-nickole.ngrok-free.dev",
]
# settings.py (al final)

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'cristofercalerohuaman@gmail.com' # Tu correo
# --- Pega la contraseña aquí ---
EMAIL_HOST_PASSWORD = 'yjgtotiatiszwgtk'
DEFAULT_FROM_EMAIL ='cristofercalerohuaman@gmail.com'
# Al final de settings.py
STATIC_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'