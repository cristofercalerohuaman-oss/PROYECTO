# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # auth (login/logout/password reset)
    path('accounts/', include('django.contrib.auth.urls')), 

    # --- TUS APLICACIONES (¡ESTO DEBE IR PRIMERO!) ---
    # Esto incluye TODAS las URLs de tu vehiculos/urls.py
    # y define el namespace 'vehiculos' (para que 'vehiculos:dashboard' funcione)
    path('', include('vehiculos.urls', namespace='vehiculos')),

    # --- RUTA RAÍZ (HOME) (¡ESTO DEBE IR DESPUÉS!) ---
    # Ahora Django ya sabe qué es 'vehiculos:dashboard'
    path('', RedirectView.as_view(pattern_name='vehiculos:dashboard', permanent=False), name='home'),
]