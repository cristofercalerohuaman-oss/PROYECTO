import os
from django.core.wsgi import get_wsgi_application

# Apuntamos al archivo settings correcto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_flota.gestion_flota.settings')

# Definimos la variable 'app' para Vercel
app = get_wsgi_application()