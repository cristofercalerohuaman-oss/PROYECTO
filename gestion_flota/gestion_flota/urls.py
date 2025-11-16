# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- LOGIN/LOGOUT ---
    path('accounts/', include('django.contrib.auth.urls')), 

    # --- RUTA RAÍZ (HOME) ---
    # ¡ESTO DEBE IR PRIMERO!
    # Redirige la raíz (/) a /dashboard/
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),

    # --- TUS APLICACIONES ---
    # ¡ESTO DEBE IR SEGUNDO!
    # Incluye TODAS las demás URLs de tu app (como /dashboard/, /vehiculos/, etc.)
    path('', include('vehiculos.urls', namespace='vehiculos')),
]