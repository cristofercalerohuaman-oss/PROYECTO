# vehiculos/admin.py
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
# Asegúrate de importar todos los modelos
from .models import Vehiculo, Ruta, Mantenimiento, Inventario, Perfil, CargaCombustible

# --- Clase Admin para Vehiculo ---
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("id", "placa", "marca", "modelo", "anio", "chofer_asignado", "kilometraje", "km_proximo_mantenimiento", "mantenimiento_requerido") # Añadidos campos nuevos
    search_fields = ("placa", "marca", "modelo")
    list_filter = ("marca", "mantenimiento_requerido") # Añadido filtro

# --- Clase Admin para Perfil ---
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'telefono', 'recibe_alertas_mantenimiento') # <-- Revisa esta palabra
    fields = ('user', 'rol', 'telefono', 'recibe_alertas_mantenimiento')       # <-- Revisa esta palabra
    list_filter = ('rol', 'recibe_alertas_mantenimiento')                     # <-- Revisa esta palabra
    # ...

# --- Clase Admin para Mantenimiento ---
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'fecha', 'tipo', 'resetea_odometro') # Añadido resetea_odometro
    list_filter = ('vehiculo', 'tipo', 'fecha', 'resetea_odometro')
    search_fields = ('vehiculo__placa', 'titulo', 'notas')

# --- Clase Admin para CargaCombustible ---
class CargaCombustibleAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'chofer', 'fecha', 'litros', 'costo', 'odometro', 'estacion_nombre')
    list_filter = ('vehiculo', 'chofer', 'fecha')
    search_fields = ('estacion_nombre', 'vehiculo__placa')
    # Opcional: Hacer lat/lng solo lectura si se rellenan por el mapa
    # readonly_fields = ('lat', 'lng')

# --- Registrar modelos usando una función auxiliar para claridad ---
def safe_register(model, admin_class=None):
    """Registra un modelo solo si no está ya registrado."""
    try:
        if admin_class:
            admin.site.register(model, admin_class)
        else:
            # Registrar con ModelAdmin por defecto si no se provee clase
            admin.site.register(model)
    except AlreadyRegistered:
        pass

# Registrar cada modelo con su clase admin específica (o por defecto)
safe_register(Vehiculo, VehiculoAdmin)
safe_register(Perfil, PerfilAdmin) # Usa el nuevo PerfilAdmin
safe_register(Mantenimiento, MantenimientoAdmin)
safe_register(CargaCombustible, CargaCombustibleAdmin)
safe_register(Ruta) # Usa admin por defecto para Ruta
safe_register(Inventario) # Usa admin por defecto para Inventario