# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- LOGIN/LOGOUT ---
    path('accounts/', include('django.contrib.auth.urls')), 

    # --- ¡LO ÚNICO QUE IMPORTA! ---
    # Incluye TODAS las URLs de tu app (incluyendo la raíz)
    # Vercel buscará en 'vehiculos.urls' la ruta para ''
    path('', include('vehiculos.urls', namespace='vehiculos')),
]