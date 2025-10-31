# vehiculos/forms.py
from django import forms # type: ignore
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from .models import CargaCombustible, Vehiculo, Perfil, Mantenimiento, Ruta, DetalleMantenimiento, DetalleMantenimiento, Flete
from decimal import Decimal
# importa el modelo Vehiculo (asegúrate de que exista en vehiculos/models.py)
try:
    from .models import Vehiculo
except Exception:
    Vehiculo = None



User = get_user_model()
class PerfilForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Correo electrónico")
    class Meta:
        model = Perfil
        fields = ['telefono','email']

    def __init__(self, *args, **kwargs):
        # Necesitamos la instancia del usuario para obtener el email inicial
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        if self.user:
            # Ponemos el email actual del usuario como valor inicial
            self.fields['email'].initial = self.user.email

    def save(self, commit=True):
        # Guardamos el perfil (teléfono)
        perfil = super().save(commit=commit)
        if commit and self.user:
            # Guardamos el email en el modelo User
            self.user.email = self.cleaned_data['email']
            self.user.save(update_fields=['email'])
        return perfil

class CargaCombustibleForm(forms.ModelForm):
    # ==========================================================
    # ¡NUEVO CAMPO! Lo usamos para la entrada del usuario
    # ==========================================================
    galones = forms.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False,
        label="Cantidad en Galones",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej: 20.5'})
    )
    # ==========================================================
    
    class Meta:
        model = CargaCombustible
        # Eliminamos 'litros' de los fields para que no se muestre por defecto
        # Aunque lo necesitamos para el guardado, lo manejaremos con JS
        fields = [
            'vehiculo','chofer','fecha','litros','costo','odometro',
            'estacion_nombre','lat','lng','comprobante','notas'
        ]
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type':'datetime-local', 'class': 'form-control'}),
            # Añadimos la clase form-control a los otros campos para que se vean bien
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'chofer': forms.Select(attrs={'class': 'form-control'}),
            'litros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'odometro': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'estacion_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'lat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'lng': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    # El método clean se asegura de que el valor de 'litros' se establezca 
    # si se ingresó un valor en 'galones'.
    def clean(self):
        cleaned_data = super().clean()
        galones = cleaned_data.get('galones')
        
        # Si se ingresó un valor en galones, lo convertimos a litros
        if galones:
            CONVERSION_FACTOR = 3.78541
            litros_calculados = galones * Decimal(str(CONVERSION_FACTOR))
            # Sobreescribimos el campo 'litros' del modelo
            cleaned_data['litros'] = litros_calculados.quantize(Decimal('0.01'))
        
        return cleaned_data

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        # ajusta los campos según tu modelo; aquí uso los que mostraste (placa, marca, modelo, anio)
        fields = ("placa", "marca", "modelo", "anio")
        widgets = {
            "placa": forms.TextInput(attrs={"placeholder": "ABC-123", "class": "form-control"}),
            "marca": forms.TextInput(attrs={"placeholder": "Toyota", "class": "form-control"}),
            "modelo": forms.TextInput(attrs={"placeholder": "Hilux", "class": "form-control"}),
            "anio": forms.NumberInput(attrs={"placeholder": "2020", "class": "form-control"}),
        }

    def clean_placa(self):
        placa = self.cleaned_data.get("placa", "").strip()
        # ejemplo de validación simple
        if not placa:
            raise forms.ValidationError("La placa es obligatoria.")
        return placa
    
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadimos placeholders para que se vean mejor
        self.fields['old_password'].widget.attrs.update({'placeholder': 'Tu contraseña actual', 'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'Tu nueva contraseña', 'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'Confirma tu nueva contraseña', 'class': 'form-control'})
        
        # Opcional: Quitar la ayuda de texto si no la quieres
        self.fields['old_password'].help_text = None
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].help_text = None
# Sigue en vehiculos/forms.py
# ... (Aquí va tu CargaCombustibleForm, PerfilForm, etc.) ...

class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = Mantenimiento
        # Campos que pediremos en el formulario
        fields = [
            'vehiculo', 
            'fecha', 
            'odometro', 
            'tipo', 
            'titulo', 
            'notas', 
            'costo', 
            'realizado_por',
            'resetea_odometro' # El checkbox
        ]
        
        # Widgets para que se vean bien (¡Bootstrap!)
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'odometro': forms.NumberInput(attrs={'placeholder': 'KM al momento del servicio', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'value': 'Mantenimiento Preventivo'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Ej: Cambio de aceite y filtros...'}),
            'costo': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'realizado_por': forms.TextInput(attrs={'placeholder': 'Nombre del taller o mecánico', 'class': 'form-control'}),
            'resetea_odometro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ... (después de tu MantenimientoForm) ...

class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        # Campos que pediremos en el formulario
        fields = [
            'titulo', 
            'vehiculo', 
            'chofer', 
            'fecha', 
            'origen',
            'destino',
            'descripcion',
            'distancia_km',
            'status', # El estado (programada, en curso, etc.)
        ]

        # Widgets para que se vean bien (¡Bootstrap!)
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Carga a Arequipa'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'chofer': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Almacén Lima'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cliente Arequipa'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Detalles de la carga...'}),
            'distancia_km': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class DetalleMantenimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMantenimiento
        fields = ['item_inventario', 'cantidad_usada']
        widgets = {
            # Usamos 'data-control' para un JavaScript futuro, si quisiéramos
            'item_inventario': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_usada': forms.NumberInput(attrs={'class': 'form-control', 'value': 1}),
        }
# ... (después de tu DetalleMantenimientoForm) ...

class FleteForm(forms.ModelForm):
    class Meta:
        model = Flete
        fields = ['titulo', 'cliente', 'descripcion', 'peso_toneladas', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Carga de cemento a Arequipa'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'peso_toneladas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 20.5'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
class RutaForm(forms.ModelForm):
    # ==========================================================
    #           ¡NUEVO CAMPO PARA ASIGNAR FLETES!
    # ==========================================================
    fletes_a_asignar = forms.ModelMultipleChoiceField(
        queryset=Flete.objects.filter(estado=Flete.ESTADO_PENDIENTE, ruta__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False, # No es obligatorio asignar un flete
        label="Fletes Pendientes para Asignar"
    )
    # ==========================================================

    class Meta:
        model = Ruta
        # ¡Asegúrate de que 'fletes_a_asignar' NO esté en esta lista!
        fields = [
            'titulo', 
            'vehiculo', 
            'chofer', 
            'fecha', 
            'origen',
            'destino',
            'descripcion',
            'distancia_km',
            'status',
        ]
        
        # (Tus widgets se mantienen igual)
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Carga a Arequipa'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select'}),
            'chofer': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'origen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Almacén Lima'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cliente Arequipa'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Detalles de la carga...'}),
            'distancia_km': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }