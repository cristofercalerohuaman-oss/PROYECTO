# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- LOGIN/LOGOUT ---
    path('accounts/', include('django.contrib.auth.urls')), 

    # --- ¡LA LÍNEA MÁS IMPORTANTE! ---
    # Pasa CUALQUIER otra petición (incluyendo la raíz '/')
    # al archivo urls.py de tu aplicación 'vehiculos'.
    path('', include('vehiculos.urls', namespace='vehiculos')),
]