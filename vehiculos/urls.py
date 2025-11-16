# vehiculos/urls.py
from django.urls import path
from . import views

app_name = 'vehiculos'

urlpatterns = [
    # --- ¡RUTA RAÍZ AÑADIDA AQUÍ! ---
    # Esto le dice a Django qué mostrar en la página principal (/)
    path('', views.dashboard, name='home'), 

    # --- Dashboard (Ruta de la app) ---
    path('dashboard/', views.dashboard, name='dashboard'),

    # --- Vehículos ---
    path('vehiculos/', views.listar_vehiculos, name='listar_vehiculos'),
    path('vehiculos/add/', views.agregar_vehiculo, name='agregar_vehiculo'),
    path('vehiculos/<int:pk>/edit/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/<int:pk>/delete/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    path('vehiculos/<int:pk>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    path('vehiculos/importar/', views.importar_excel, name='importar_excel'),

    # --- Cargas de Combustible ---
    path('cargas/', views.lista_cargas, name='lista_cargas'),
    path('cargas/nueva/', views.nueva_carga, name='nueva_carga'),
    path('cargas/<int:pk>/', views.detalle_carga, name='detalle_carga'),

    # --- Rutas ---
    path('rutas/', views.lista_rutas, name='lista_rutas'),
    path('rutas/planificar/', views.planificar_ruta, name='planificar_ruta'),
    path('rutas/<int:pk>/iniciar/', views.iniciar_ruta, name='iniciar_ruta'),
    path('rutas/<int:pk>/completar/', views.completar_ruta, name='completar_ruta'),
    path('rutas/<int:pk>/', views.detalle_ruta, name='detalle_ruta'),

    # --- Mantenimientos ---
    path('mantenimientos/', views.lista_mantenimientos, name='lista_mantenimientos'),
    path('mantenimientos/registrar/', views.registrar_mantenimiento, name='registrar_mantenimiento'),
    path('mantenimientos/<int:pk>/', views.detalle_mantenimiento, name='detalle_mantenimiento'),
    path('mantenimientos/<int:pk>/eliminar/', views.eliminar_mantenimiento, name='eliminar_mantenimiento'),
    path('mantenimientos/<int:pk>/editar/', views.editar_mantenimiento, name='editar_mantenimiento'),

    # --- Fletes ---
    path('fletes/', views.lista_fletes, name='lista_fletes'),
    path('fletes/crear/', views.crear_flete, name='crear_flete'),
    path('fletes/<int:pk>/editar/', views.editar_flete, name='editar_flete'),
    path('fletes/<int:pk>/eliminar/', views.eliminar_flete, name='eliminar_flete'),
    path('fletes/<int:pk>/', views.detalle_flete, name='detalle_flete'),

    # --- Reportes y Perfil ---
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('reportes/consumo/', views.reporte_consumo, name='reporte_consumo'),
    path('exportar/excel/', views.exportar_todas_tablas, name='exportar_excel'),

    # --- Auth (Signup) ---
    path('signup/', views.signup, name='signup'),
]