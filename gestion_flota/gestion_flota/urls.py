"""
WSGI config for gestion_flota project.
... (el resto de tus comentarios) ...
"""

import os
from django.core.wsgi import get_wsgi_application

# --- ¡LA LÍNEA CORREGIDA! ---
# Le decimos la ruta completa al archivo settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_flota.gestion_flota.settings')

app = get_wsgi_application()