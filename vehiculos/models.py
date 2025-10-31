# vehiculos/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db.models import F # <-- ¡IMPORTANTE! Asegúrate de que F esté importado

User = get_user_model()

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=30, default='chofer')
    telefono = models.CharField(max_length=30, blank=True, default='')
    creado_en = models.DateTimeField(default=timezone.now)
    recibe_alertas_mantenimiento = models.BooleanField(default=False, help_text="Marcar si el usuario debe recibir correos de alerta de mantenimiento")

    def __str__(self):
        return f"{self.user.username} ({self.rol})"

class Vehiculo(models.Model):
    # ... (Tu modelo Vehiculo se mantiene exactamente igual) ...
    placa = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=50, blank=True, default='')
    modelo = models.CharField(max_length=50, blank=True, default='')
    anio = models.IntegerField(null=True, blank=True)
    combustible_tipo = models.CharField(max_length=30, blank=True, default='')
    kilometraje = models.IntegerField(default=0) # Odómetro actual
    activo = models.BooleanField(default=True)
    chofer_asignado = models.ForeignKey(
        'Perfil', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='vehiculos'
    )
    km_para_mantenimiento = models.IntegerField(
        null=True, blank=True, 
        default=5000, 
        help_text="Intervalo de KM para el próximo mantenimiento (ej: 5000)"
    )
    km_proximo_mantenimiento = models.IntegerField(
        null=True, blank=True, 
        default=5000, 
        help_text="Odómetro del próximo mantenimiento (ej: 150000)"
    )
    mantenimiento_requerido = models.BooleanField(
        default=False, 
        help_text="Marcar si el vehículo ha pasado su KM de mantenimiento"
    )
    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"
    class Meta:
        # Añadimos índices para búsquedas rápidas
        indexes = [
            models.Index(fields=['chofer_asignado']), 
        ]

class CargaCombustible(models.Model):
    # ... (Tu modelo CargaCombustible se mantiene exactamente igual, con su método save()) ...
    vehiculo = models.ForeignKey('Vehiculo', on_delete=models.CASCADE, related_name='cargas')
    chofer = models.ForeignKey('Perfil', null=True, blank=True, on_delete=models.SET_NULL, related_name='cargas')
    fecha = models.DateTimeField(default=timezone.now)
    litros = models.DecimalField(max_digits=8, decimal_places=2)
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    odometro = models.IntegerField(null=True, blank=True)
    odometro_anterior = models.IntegerField(null=True, blank=True, help_text="Odómetro registrado en la carga anterior para este vehículo")
    rendimiento_km_lt = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Rendimiento calculado para este tramo (KM/Lt)")
    estacion_nombre = models.CharField(max_length=200, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/', null=True, blank=True)
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['vehiculo', 'fecha']), # Búsqueda común
            models.Index(fields=['chofer']), 
        ]
    def __str__(self):
        return f"{self.vehiculo} - {self.litros}L @ {self.fecha.date()}"
    def save(self, *args, **kwargs):
        vehiculo = self.vehiculo
        try:
            ultima_carga = vehiculo.cargas.filter(fecha__lt=self.fecha).latest('fecha')
            odometro_ant = ultima_carga.odometro
        except CargaCombustible.DoesNotExist:
            odometro_ant = None
        if odometro_ant and self.odometro:
            self.odometro_anterior = odometro_ant
            km_recorridos = self.odometro - odometro_ant
            if self.litros > 0 and km_recorridos > 0:
                self.rendimiento_km_lt = km_recorridos / self.litros
        if self.odometro and self.odometro > vehiculo.kilometraje:
             vehiculo.kilometraje = self.odometro
        if vehiculo.km_proximo_mantenimiento and vehiculo.kilometraje > vehiculo.km_proximo_mantenimiento:
            vehiculo.mantenimiento_requerido = True
        vehiculo.save(update_fields=['kilometraje', 'mantenimiento_requerido'])
        super().save(*args, **kwargs)

class Inventario(models.Model):
    nombre = models.CharField(max_length=200, default='Producto sin nombre')
    cantidad = models.IntegerField(default=0) # <-- Este es el stock
    precio = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True, default=0.00)
    proveedor = models.CharField(max_length=200, blank=True, default='Desconocido')
    ultimo_movimiento = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} ({self.cantidad})"

# ==========================================================
# === 1. ¡NUEVO MODELO INTERMEDIARIO! ===
# ==========================================================
class DetalleMantenimiento(models.Model):
    """
    Este modelo es la "lista" que conecta un Mantenimiento con
    los items de Inventario que usó.
    """
    mantenimiento = models.ForeignKey(
        'Mantenimiento', 
        on_delete=models.CASCADE, 
        related_name="detalles_items" # Nombre para referenciar desde Mantenimiento
    )
    item_inventario = models.ForeignKey(
        Inventario, 
        on_delete=models.SET_NULL, # Si se borra el item, no se borra el detalle
        null=True,
        related_name="usos_en_mantenimiento"
    )
    cantidad_usada = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad_usada} x {self.item_inventario.nombre}"

    # ==========================================================
    # === 2. ¡LÓGICA PARA RESTAR STOCK! ===
    # ==========================================================
    def save(self, *args, **kwargs):
        # Esta lógica se activa CADA VEZ que se guarda un detalle
        
        # Primero, guarda el detalle (para que tenga un 'pk')
        super().save(*args, **kwargs)
        
        # Ahora, actualiza el stock del item en el inventario
        if self.item_inventario and self.cantidad_usada > 0:
            # Usamos F() para restar de forma segura (evita problemas de concurrencia)
            # self.item_inventario.cantidad -= self.cantidad_usada (¡Esta es la forma INCORRECTA!)
            
            self.item_inventario.cantidad = F('cantidad') - self.cantidad_usada
            self.item_inventario.save(update_fields=['cantidad'])
            self.item_inventario.refresh_from_db() # Actualiza el objeto

# ==========================================================

class Mantenimiento(models.Model):
    TIPOS_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
        ('otros', 'Otros'),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='mantenimientos')
    fecha = models.DateField(default=timezone.now)
    odometro = models.IntegerField(null=True, blank=True, help_text="El kilometraje del vehículo CUANDO se hizo el mantenimiento")
    titulo = models.CharField(max_length=200, default='Mantenimiento')
    tipo = models.CharField(max_length=50, choices=TIPOS_CHOICES, default='preventivo')
    notas = models.TextField(blank=True, default='')
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    realizado_por = models.CharField(max_length=200, blank=True, default='')
    resetea_odometro = models.BooleanField(default=True, help_text="Marcar si este mantenimiento resetea el contador de KM")

    # ==========================================================
    # === 3. ¡CONEXIÓN M2M CON INVENTARIO! ===
    # ==========================================================
    items_usados = models.ManyToManyField(
        Inventario,
        through=DetalleMantenimiento, # Le decimos que use nuestro modelo "intermediario"
        related_name='mantenimientos_asociados'
    )

    def __str__(self):
        return f"{self.vehiculo.placa} - {self.tipo} ({self.fecha})"

    # --- LÓGICA DE AUTO-RESETEO (MODIFICADA) ---
    def save(self, *args, **kwargs):
        if not self.odometro and self.vehiculo:
             self.odometro = self.vehiculo.kilometraje
        
        # Guardamos el mantenimiento ANTES de la lógica de reseteo
        super().save(*args, **kwargs) 
        
        if self.resetea_odometro and self.vehiculo:
            vehiculo = self.vehiculo
            intervalo = vehiculo.km_para_mantenimiento or 5000
            vehiculo.km_proximo_mantenimiento = self.odometro + intervalo
            vehiculo.mantenimiento_requerido = False
            vehiculo.save(update_fields=['km_proximo_mantenimiento', 'mantenimiento_requerido'])
        # (El guardado de 'super()' ya se hizo al inicio)

class Ruta(models.Model):
    # ... (Tu modelo Ruta se mantiene exactamente igual) ...
    STATUS_PROGRAMADA = 'programada'
    STATUS_EN_CURSO = 'en_curso'
    STATUS_COMPLETADA = 'completada'
    STATUS_CHOICES = [
        (STATUS_PROGRAMADA, 'Programada'),
        (STATUS_EN_CURSO, 'En Curso'),
        (STATUS_COMPLETADA, 'Completada'),
    ]
    titulo = models.CharField(max_length=200, default='Ruta sin título')
    descripcion = models.TextField(blank=True, default='')
    fecha = models.DateField(default=timezone.now)
    chofer = models.ForeignKey(Perfil, null=True, blank=True, on_delete=models.SET_NULL, related_name='rutas')
    vehiculo = models.ForeignKey(Vehiculo, null=True, blank=True, on_delete=models.SET_NULL)
    origen = models.CharField(max_length=200, blank=True, default='')
    destino = models.CharField(max_length=200, blank=True, default='')
    distancia_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROGRAMADA, help_text="Estado actual de la ruta")

    def __str__(self):
        return f"{self.titulo} - {self.fecha} ({self.get_status_display()})"
    class Meta:
        ordering = ['-fecha']
        # Añadimos índices para búsquedas rápidas
        indexes = [
            models.Index(fields=['fecha']), 
            models.Index(fields=['chofer']), 
            models.Index(fields=['vehiculo']),
        ]

# En vehiculos/models.py
class Flete(models.Model):
    # --- Opciones para el estado ---
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_ASIGNADO = 'asignado'
    ESTADO_EN_TRANSITO = 'en_transito'
    ESTADO_ENTREGADO = 'entregado'
    ESTADO_CANCELADO = 'cancelado'
    
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente de Asignación'),
        (ESTADO_ASIGNADO, 'Asignado a Ruta'),
        (ESTADO_EN_TRANSITO, 'En Tránsito'),
        (ESTADO_ENTREGADO, 'Entregado'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    # --- Campos del Modelo ---
    titulo = models.CharField(max_length=200, default='Carga sin título')
    cliente = models.CharField(max_length=200, blank=True, help_text="Nombre del cliente o empresa")
    descripcion = models.TextField(blank=True, default='')
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        help_text="Estado actual del flete"
    )
    
    # El flete puede estar asignado a UNA ruta
    ruta = models.ForeignKey(
        'Ruta',  # <-- Debe apuntar al modelo 'Ruta'
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="fletes_asignados"
    )

    peso_toneladas = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Peso de la carga en toneladas"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titulo} ({self.get_estado_display()})"

    class Meta:
        ordering = ['-fecha_creacion']

