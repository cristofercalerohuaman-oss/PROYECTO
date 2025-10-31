# vehiculos/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from .models import Vehiculo, Inventario, Mantenimiento, DetalleMantenimiento, Perfil

User = get_user_model()

# =======================================================================
# PRUEBA DE FUNCIONALIDAD: INVENTARIO Y MANTENIMIENTO
# =======================================================================
class MantenimientoTestCase(TestCase):
    
    def setUp(self):
        # 1. Crear un usuario admin para que las FK funcionen
        self.user = User.objects.create_user(username='admin_test', password='password')
        self.perfil, _ = Perfil.objects.get_or_create(user=self.user)
        
        # 2. Crear un vehículo de prueba
        self.vehiculo = Vehiculo.objects.create(
            placa='ABC-123',
            kilometraje=90000,
            km_proximo_mantenimiento=100000,
            km_para_mantenimiento=10000,
            activo=True
        )
        
        # 3. Crear items de inventario con stock inicial
        self.filtro = Inventario.objects.create(nombre='Filtro de Aceite', cantidad=20, precio=15.00)
        self.aceite = Inventario.objects.create(nombre='Galón de Aceite', cantidad=50, precio=50.00)
        self.bujia = Inventario.objects.create(nombre='Bujía', cantidad=10, precio=5.00)

    def test_01_stock_is_deducted_on_maintenance_creation(self):
        """
        Verifica que el stock de inventario se descuenta cuando se crea el DetalleMantenimiento.
        """
        # STOCK INICIAL: Filtro=20, Aceite=50
        
        # 1. Crear el registro de Mantenimiento
        mantenimiento = Mantenimiento.objects.create(
            vehiculo=self.vehiculo,
            odometro=90500,
            costo=150.00,
            titulo="Cambio de Aceite",
            fecha=date.today(),
            resetea_odometro=True
        )
        
        # 2. Asignar items al mantenimiento (activando la lógica de stock en save())
        DetalleMantenimiento.objects.create(
            mantenimiento=mantenimiento,
            item_inventario=self.filtro,
            cantidad_usada=2 # Usamos 2 filtros
        )
        DetalleMantenimiento.objects.create(
            mantenimiento=mantenimiento,
            item_inventario=self.aceite,
            cantidad_usada=5 # Usamos 5 galones
        )
        
        # 3. Recargar el objeto de la base de datos para ver el stock actualizado
        self.filtro.refresh_from_db()
        self.aceite.refresh_from_db()
        self.bujia.refresh_from_db()

        # 4. AFIRMACIONES
        self.assertEqual(self.filtro.cantidad, 18, "El stock de Filtro no se descontó correctamente.")
        self.assertEqual(self.aceite.cantidad, 45, "El stock de Aceite no se descontó correctamente.")
        self.assertEqual(self.bujia.cantidad, 10, "El stock de Bujía se modificó erróneamente.")

    def test_02_maintenance_alert_resets_km(self):
        """
        Verifica que al registrar un mantenimiento, la alerta se apaga
        y el proximo KM de mantenimiento se actualiza.
        """
        # Simulamos que el vehículo necesita mantenimiento
        self.vehiculo.mantenimiento_requerido = True
        self.vehiculo.kilometraje = 105000
        self.vehiculo.save()
        
        # 1. La alerta debe estar activada antes de la acción
        self.assertTrue(self.vehiculo.mantenimiento_requerido, "Fallo: La alerta debería estar activada antes del mantenimiento.")

        # 2. Crear el Mantenimiento (esto activa el .save() del modelo)
        Mantenimiento.objects.create(
            vehiculo=self.vehiculo,
            odometro=105000,
            fecha=date.today(),
            resetea_odometro=True
        )
        
        # 3. Recargar el objeto del vehículo
        self.vehiculo.refresh_from_db()

        # 4. AFIRMACIONES
        # Próximo KM debe ser: KM del servicio + intervalo (105000 + 10000 = 115000)
        self.assertEqual(self.vehiculo.km_proximo_mantenimiento, 115000, "Fallo: El próximo KM de mantenimiento no se calculó correctamente.")
        # La alerta debe estar apagada
        self.assertFalse(self.vehiculo.mantenimiento_requerido, "Fallo: La alerta de mantenimiento no se apagó después del servicio.")