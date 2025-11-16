# gestion_flota/gestion_flota/urls.py
from django.contrib import admin
from django.urls import path, include
from vehiculos import views as vehiculos_views  # <-- Importamos la vista del dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- LOGIN/LOGOUT ---
    path('accounts/', include('django.contrib.auth.urls')), 

    # --- RUTA RAÍZ (HOME) ---
    # 1. Define la ruta raíz (/) para que apunte a tu vista de dashboard
    path('', vehiculos_views.dashboard, name='home'),

    # --- TUS APLICACIONES ---
    # 2. Incluye TODAS las demás URLs de tu app (como /dashboard/, /vehiculos/, etc.)
    path('', include('vehiculos.urls', namespace='vehiculos')),
]