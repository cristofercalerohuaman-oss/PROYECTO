# ... (comentarios) ...
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_flota.settings')

app = get_wsgi_application() # <-- ¡SOLUCIÓN!