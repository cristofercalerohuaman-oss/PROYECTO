# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth (login/logout/password reset)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # --- RUTA RAÍZ (HOME) ---
    # Esto redirige la página principal ('/') a la URL 'vehiculos:dashboard'
    path('', RedirectView.as_view(pattern_name='vehiculos:dashboard', permanent=False)),

    # --- TUS APLICACIONES ---
    # Esto incluye TODAS las URLs de tu vehiculos/urls.py
    path('', include('vehiculos.urls', namespace='vehiculos')),
]