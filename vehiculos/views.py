# vehiculos/views.py
from pathlib import Path
from io import BytesIO
import os
from urllib.parse import quote_plus
from datetime import datetime, time, date
from decimal import Decimal, InvalidOperation
# --- Imports de Django ---
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required # ¡SOLO login_required va aquí!
from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Max, Min, F, Value, CharField
from django.db.models.functions import Cast
from django.utils import timezone
from django.contrib.auth import login, update_session_auth_hash, get_user_model
from django.core.mail import send_mail
from django import forms
from django.utils.dateparse import parse_date
from django.db import transaction
from django.forms import inlineformset_factory

# --- Imports de Terceros ---
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
import re

# --- Imports Locales (.forms y .models) ---

# ¡IMPORTACIÓN CORREGIDA! Lo traemos desde nuestro archivo .decorators
from .decorators import admin_o_logistica_required 

try:
    from .forms import SignupForm
except ImportError:
    SignupForm = None
try:
    from .forms import PerfilForm
except ImportError:
    PerfilForm = None
try:
    from .forms import CustomPasswordChangeForm
except ImportError:
    CustomPasswordChangeForm = None

# Importamos TODOS los formularios que hemos creado
from .forms import CargaCombustibleForm, VehiculoForm, MantenimientoForm, RutaForm, DetalleMantenimientoForm, FleteForm

# Importamos TODOS los modelos que hemos creado
try:
    from .models import Vehiculo, Ruta, Mantenimiento, Inventario, Perfil, CargaCombustible, DetalleMantenimiento, Flete
except ImportError:
    Vehiculo = None
    Ruta = None
    Mantenimiento = None
    Inventario = None
    Perfil = None
    CargaCombustible = None
    DetalleMantenimiento = None

# --- Inicialización ---
load_dotenv()
User = get_user_model()

# =============================================
# VISTA: lista_cargas
# =============================================
#@login_required
def lista_cargas(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)

    if user.is_staff:
        base_qs = CargaCombustible.objects.select_related('vehiculo', 'chofer').all()
        vehiculos_para_filtro = Vehiculo.objects.filter(activo=True).order_by('placa')
    elif perfil:
        base_qs = CargaCombustible.objects.select_related('vehiculo', 'chofer').filter(chofer=perfil)
        vehiculos_para_filtro = Vehiculo.objects.filter(activo=True, chofer_asignado=perfil).order_by('placa')
    else:
        base_qs = CargaCombustible.objects.none()
        vehiculos_para_filtro = Vehiculo.objects.none()

    qs = base_qs
    vehiculo_id_filtro = request.GET.get('vehiculo')
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    if vehiculo_id_filtro:
        try: qs = qs.filter(vehiculo_id=int(vehiculo_id_filtro))
        except (ValueError, TypeError): messages.error(request, "ID inválido."); vehiculo_id_filtro = None
    if fecha_inicio_str:
        try: fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date(); qs = qs.filter(fecha__gte=datetime.combine(fecha_inicio, time.min))
        except ValueError: messages.error(request, "Fecha inicio inválida.")
    if fecha_fin_str:
        try: fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date(); qs = qs.filter(fecha__lte=datetime.combine(fecha_fin, time.max))
        except ValueError: messages.error(request, "Fecha fin inválida.")

    sort_by = request.GET.get('sort', '-fecha')
    direction = request.GET.get('dir', 'desc')
    allowed_sort_fields = ['fecha', 'vehiculo__placa', 'chofer__user__username', 'litros', 'costo', 'odometro', 'estacion_nombre']
    current_sort_base = sort_by[1:] if sort_by.startswith('-') else sort_by
    if current_sort_base in allowed_sort_fields:
        sort_field = sort_by
        if direction == 'asc' and sort_field.startswith('-'): sort_field = sort_field[1:]
        elif direction == 'desc' and not sort_field.startswith('-'): sort_field = '-' + sort_field
        try:
            qs = qs.order_by(sort_field)
        except Exception as e:
            print(f"Advertencia: Falló la ordenación por '{sort_field}'. Usando orden por defecto. Error: {e}")
            sort_by = '-fecha'; direction = 'desc'; current_sort_base = 'fecha'
            qs = qs.order_by(sort_by)
    else:
        sort_by = '-fecha'; direction = 'desc'; current_sort_base = 'fecha'
        qs = qs.order_by(sort_by)

    cargas_limpias = []
    error_conversion_final = False
    cargas_qs_texto = qs.annotate(
        litros_str=Cast('litros', output_field=CharField()),
        costo_str=Cast('costo', output_field=CharField())
    ).values(
        'id', 'fecha', 'vehiculo__placa', 'chofer__user__username',
        'litros_str', 'costo_str', 'odometro', 'estacion_nombre'
    )

    for carga_dict in cargas_qs_texto:
        carga_id = carga_dict['id']
        litros_str = carga_dict['litros_str']
        costo_str = carga_dict['costo_str']
        carga_limpia = carga_dict.copy() 
        try:
            if litros_str is not None and litros_str.strip():
                carga_limpia['litros'] = Decimal(litros_str)
            else:
                carga_limpia['litros'] = Decimal('0.00')
            if costo_str is not None and costo_str.strip():
                carga_limpia['costo'] = Decimal(costo_str)
            else:
                carga_limpia['costo'] = Decimal('0.00')
            cargas_limpias.append(carga_limpia)
        except InvalidOperation as e:
            error_conversion_final = True
            print(f"Error de conversión manual ID: {carga_id}, Error: {repr(e)}")

    if error_conversion_final:
        messages.warning(request, "Se omitieron algunas cargas debido a datos numéricos inválidos.")

    paginator = Paginator(cargas_limpias, 20)
    page = request.GET.get('page')
    cargas_paginadas = paginator.get_page(page)

    try:
        total_litros = qs.aggregate(Sum('litros'))['litros__sum'] or 0
        total_gasto = qs.aggregate(Sum('costo'))['costo__sum'] or 0
    except InvalidOperation:
        total_litros = 0; total_gasto = 0
        messages.error(request, "No se pudieron calcular totales.")

    context = {
        'cargas': cargas_paginadas,
        'total_litros': total_litros, 'total_gasto': total_gasto,
        'vehiculos_para_filtro': vehiculos_para_filtro, 'vehiculo_id_seleccionado': vehiculo_id_filtro,
        'fecha_inicio_filtro': fecha_inicio_str, 'fecha_fin_filtro': fecha_fin_str,
        'current_sort': sort_by, 'current_dir': direction, 'current_sort_base': current_sort_base,
        }
    return render(request, 'vehiculos/lista_cargas.html', context)

# =============================================
# VISTA: nueva_carga
# =============================================
@login_required
def nueva_carga(request):
    if request.method == 'POST':
        form = CargaCombustibleForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.creado_por = request.user
            if not request.user.is_staff and hasattr(request.user, 'perfil'):
                obj.chofer = request.user.perfil
            
            obj.save() 
            
            messages.success(request, "Carga registrada correctamente.")
            return redirect('vehiculos:lista_cargas')
        else:
            messages.error(request, "Error en el formulario. Revisa los campos.")
    else:
        initial = {}
        v = request.GET.get('vehiculo')
        if v: initial['vehiculo'] = v
        form = CargaCombustibleForm(initial=initial)
    return render(request, 'vehiculos/nueva_carga.html', {'form': form})

# =============================================
# VISTA: detalle_carga
# =============================================
@login_required
def detalle_carga(request, pk):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    if user.is_staff:
        carga = get_object_or_404(CargaCombustible, pk=pk)
    elif perfil:
        carga = get_object_or_404(CargaCombustible, pk=pk, chofer=perfil)
    else: raise Http404
    return render(request, 'vehiculos/detalle_carga.html', {'carga': carga})

# =============================================
# VISTA: dashboard
# =============================================
@login_required
def dashboard(request):
    user = request.user; perfil = getattr(user, 'perfil', None); hoy = date.today()
    
    if user.is_staff:
        vehiculos_qs = Vehiculo.objects.all(); mantenimientos_qs = Mantenimiento.objects.all(); rutas_qs = Ruta.objects.all()
    elif perfil:
        vehiculos_qs = Vehiculo.objects.filter(chofer_asignado=perfil); mantenimientos_qs = Mantenimiento.objects.filter(vehiculo__in=vehiculos_qs); rutas_qs = Ruta.objects.filter(chofer=perfil)
    else: vehiculos_qs, mantenimientos_qs, rutas_qs = [qs.none() for qs in (Vehiculo.objects, Mantenimiento.objects, Ruta.objects)]
    
    try: vehiculos_count = vehiculos_qs.count()
    except Exception: vehiculos_count = 0
    
    try: ultimos_mantenimientos = mantenimientos_qs.select_related('vehiculo').order_by('-fecha')[:5]
    except Exception: ultimos_mantenimientos = []
    
    try:
        rutas_hoy_qs = rutas_qs.filter(fecha=hoy, status__in=[Ruta.STATUS_PROGRAMADA, Ruta.STATUS_EN_CURSO])
        rutas_hoy_count = rutas_hoy_qs.count()
        rutas_futuras = rutas_qs.filter(fecha__gt=hoy, status=Ruta.STATUS_PROGRAMADA).order_by('fecha')[:5]
    except Exception: rutas_hoy_qs, rutas_hoy_count, rutas_futuras = [], 0, []
    
    try:
        vehiculos_con_mantenimiento = vehiculos_qs.filter(mantenimiento_requerido=True)
        mantenimientos_pendientes = vehiculos_con_mantenimiento.count()
    except Exception: mantenimientos_pendientes, vehiculos_con_mantenimiento = 0, []
    
    context = { 
        'user': user, 
        'vehiculos_count': vehiculos_count, 
        'ultimos_mantenimientos': ultimos_mantenimientos, 
        'rutas_hoy': rutas_hoy_qs, 
        'rutas_hoy_count': rutas_hoy_count, 
        'rutas_futuras': rutas_futuras, 
        'mantenimientos_pendientes': mantenimientos_pendientes, 
        'vehiculos_con_mantenimiento': vehiculos_con_mantenimiento, 
        'hoy': hoy, 
    }
    return render(request, 'vehiculos/dashboard.html', context)

# =============================================
# VISTAS DE VEHÍCULOS (Listar, Detalle, CRUD)
# =============================================
@login_required
def listar_vehiculos(request):
    user = request.user; perfil = getattr(user, 'perfil', None)
    if user.is_staff: base_qs = Vehiculo.objects.all()
    elif perfil: base_qs = Vehiculo.objects.filter(chofer_asignado=perfil)
    else: base_qs = Vehiculo.objects.none()
    qs = base_qs
    marcas_disponibles = base_qs.order_by('marca').values_list('marca', flat=True).distinct()
    marca_filtro = request.GET.get('marca'); activo_filtro = request.GET.get('activo'); mantenimiento_filtro = request.GET.get('mantenimiento')
    if marca_filtro: qs = qs.filter(marca__iexact=marca_filtro)
    if activo_filtro == 'true': qs = qs.filter(activo=True)
    elif activo_filtro == 'false': qs = qs.filter(activo=False)
    if mantenimiento_filtro == 'true': qs = qs.filter(mantenimiento_requerido=True)
    elif mantenimiento_filtro == 'false': qs = qs.filter(mantenimiento_requerido=False)
    qs = qs.order_by('placa'); vehiculos = qs
    context = { 'vehiculos': vehiculos, 'marcas_disponibles': marcas_disponibles, 'marca_seleccionada': marca_filtro, 'activo_seleccionado': activo_filtro, 'mantenimiento_seleccionado': mantenimiento_filtro, }
    return render(request, 'vehiculos/lista_vehiculos.html', context)

@login_required
def detalle_vehiculo(request, pk):
    if Vehiculo is None: return HttpResponse("Modelo Vehiculo no definido", status=500)
    user = request.user; perfil = getattr(user, 'perfil', None)

    # 1. Obtener el vehículo (renombrado a 'vehiculo' para claridad)
    if user.is_staff:
        vehiculo = get_object_or_404(Vehiculo, pk=pk)
    elif perfil:
        vehiculo = get_object_or_404(Vehiculo, pk=pk, chofer_asignado=perfil)
    else: 
        raise Http404

    # 2. ¡NUEVO! Obtener todos los historiales de este vehículo
    # Usamos .select_related() para optimizar y cargar datos relacionados (como el chofer en rutas)
    historial_mantenimientos = vehiculo.mantenimientos.all().order_by('-fecha')
    historial_combustible = vehiculo.cargas.all().select_related('chofer').order_by('-fecha')
    historial_rutas = vehiculo.ruta_set.all().select_related('chofer').order_by('-fecha')

    # 3. Preparar el contexto
    contexto = {
        'vehiculo': vehiculo, # Usaremos 'vehiculo' en la nueva plantilla
        'historial_mantenimientos': historial_mantenimientos,
        'historial_combustible': historial_combustible,
        'historial_rutas': historial_rutas,
    }
    
    return render(request, 'vehiculos/detalle_vehiculo.html', contexto)

@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def eliminar_vehiculo(request, pk):
    if not request.user.is_staff: messages.error(request, "Acceso denegado."); return redirect('vehiculos:listar_vehiculos')
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    placa = vehiculo.placa
    vehiculo.delete()
    messages.success(request, f"Vehículo {placa} eliminado correctamente.")
    return redirect('vehiculos:listar_vehiculos')

@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def agregar_vehiculo(request):
    if not request.user.is_staff: messages.error(request, "Acceso denegado."); return redirect('vehiculos:listar_vehiculos')
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            v = form.save(); messages.success(request, f"Vehículo {v.placa} creado."); return redirect('vehiculos:listar_vehiculos')
    else: form = VehiculoForm()
    return render(request, 'vehiculos/agregar_vehiculo.html', {'form': form})

@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def editar_vehiculo(request, pk):
    if not request.user.is_staff: messages.error(request, "Acceso denegado."); return redirect('vehiculos:listar_vehiculos')
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            v = form.save(); messages.success(request, f"Vehículo {v.placa} actualizado."); return redirect('vehiculos:listar_vehiculos')
    else: form = VehiculoForm(instance=vehiculo)
    return render(request, 'vehiculos/editar_vehiculo.html', {'form': form, 'vehiculo': vehiculo})

# =============================================
# VISTA: importar_excel
# =============================================
@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def importar_excel(request):
    if not request.user.is_staff:
        messages.error(request, "Acceso denegado.")
        return redirect('vehiculos:listar_vehiculos')
    if request.method != 'POST':
        return render(request, 'vehiculos/importar_excel.html')
    if 'excel_file' not in request.FILES:
        messages.error(request, "No se ha enviado ningún archivo.")
        return redirect('vehiculos:listar_vehiculos')
    
    excel_file = request.FILES['excel_file']
    try:
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        messages.error(request, f"Error leyendo el archivo Excel: {e}")
        return redirect('vehiculos:listar_vehiculos')
    
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    def pick(candidates):
        for c in candidates:
            if c and c in df.columns: return c
        return None
    
    c_placa = pick(['TRACTO', 'PLACA', 'TRACTO/PLACA', 'TRACTO-PLACA'])
    c_marca = pick(['MARCA TRACTO', 'MARCA', 'MARCA_TRACTO'])
    c_modelo = pick(['CONFIGURACION', 'CONFIGURACIÓN', 'TIPO DE UNIDAD', 'TIPO', 'MODELO'])
    c_fecha = pick(['FECHA-DISPONIBLE', 'FECHA DISPONIBLE', 'FECHA', 'DATE'])
    allowed_fields = {'placa', 'marca', 'modelo', 'anio', 'combustible_tipo', 'kilometraje', 'activo'}
    
    creados, actualizados, errores, total = 0, 0, [], 0
    columnas_ignoradas = set()
    
    for idx, row in df.iterrows():
        total += 1
        try:
            placa_val = ''
            if c_placa:
                raw = row.get(c_placa)
                if pd.notna(raw): placa_val = str(raw).strip()
            if not placa_val: raise ValueError("Falta PLACA / TRACTO")
            
            defaults = {}
            if c_marca and pd.notna(row.get(c_marca)): defaults['marca'] = str(row.get(c_marca)).strip()
            if c_modelo and pd.notna(row.get(c_modelo)): defaults['modelo'] = str(row.get(c_modelo)).strip()
            if c_fecha and pd.notna(row.get(c_fecha)):
                rawf = row.get(c_fecha); anio_val = None
                try:
                    if hasattr(rawf, 'year'): anio_val = int(rawf.year)
                    else:
                        s = str(rawf); m = re.search(r'(\d{4})', s)
                        if m: anio_val = int(m.group(1))
                except Exception: anio_val = None
                if anio_val: defaults['anio'] = anio_val
                
            for col in df.columns:
                if col not in (c_placa, c_marca, c_modelo, c_fecha): columnas_ignoradas.add(col)
                
            create_defaults = {k: v for k, v in defaults.items() if k in allowed_fields}
            
            with transaction.atomic():
                obj, created = Vehiculo.objects.update_or_create(placa=placa_val, defaults=create_defaults)
            
            if created: creados += 1
            else: actualizados += 1
            
        except Exception as e: errores.append(f"Fila {idx+1}: {e}")
        
    messages.success(request, f"Procesadas {total} filas — creadas: {creados}, actualizadas: {actualizados}, errores: {len(errores)}.")
    if columnas_ignoradas: messages.info(request, "Columnas ignoradas: " + ", ".join(sorted(columnas_ignoradas)))
    if errores:
        for err in errores[:10]: messages.error(request, err)
        if len(errores) > 10: messages.error(request, f"... y {len(errores)-10} errores más.")
    
    return redirect('vehiculos:listar_vehiculos')

# =============================================
# VISTAS DE RUTAS (Listar, Planificar, Acciones)
# =============================================
@login_required
def lista_rutas(request):
    rutas = Ruta.objects.all().order_by('-fecha')
    contexto = {
        'rutas': rutas
    }
    return render(request, 'vehiculos/lista_rutas.html', contexto)

@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def planificar_ruta(request):
    if request.method == 'POST':
        form = RutaForm(request.POST)
        if form.is_valid():
            # 1. Guarda la ruta principal (el viaje)
            ruta_creada = form.save()
            
            # 2. Obtenemos la lista de fletes que el usuario marcó
            fletes_seleccionados = form.cleaned_data['fletes_a_asignar']
            
            # 3. "Enganchamos" cada flete a la nueva ruta
            for flete in fletes_seleccionados:
                flete.ruta = ruta_creada # Asignamos la ruta
                flete.estado = Flete.ESTADO_ASIGNADO # Cambiamos el estado
                flete.save() # Guardamos el flete

            messages.success(request, '¡Ruta planificada! Se asignaron los fletes correctamente.')
            return redirect('vehiculos:lista_rutas')
    else:
        form = RutaForm()

    contexto = {
        'form': form
    }
    return render(request, 'vehiculos/planificar_ruta.html', contexto)

@login_required
def iniciar_ruta(request, pk):
    user = request.user; perfil = getattr(user, 'perfil', None)
    if user.is_staff: ruta = get_object_or_404(Ruta, pk=pk)
    elif perfil: ruta = get_object_or_404(Ruta, pk=pk, chofer=perfil)
    else: raise Http404
    
    if ruta.status == 'programada': # Comparamos con el string
        # 1. Actualiza el estado de la Ruta
        ruta.status = Ruta.STATUS_EN_CURSO # Usamos la variable del modelo para asignar
        ruta.save(update_fields=['status'])
        
        # 2. ¡NUEVO! Actualiza TODOS los fletes "enganchados" a esta ruta
        # Usamos .update() para hacerlo en una sola consulta de base de datos
        ruta.fletes_asignados.filter(estado=Flete.ESTADO_ASIGNADO).update(estado=Flete.ESTADO_EN_TRANSITO)
        
        messages.success(request, f"Ruta '{ruta.titulo}' iniciada. Fletes actualizados a 'En Tránsito'.")
    
    return redirect('vehiculos:dashboard')

@login_required
def completar_ruta(request, pk):
    user = request.user; perfil = getattr(user, 'perfil', None)
    if user.is_staff: ruta = get_object_or_404(Ruta, pk=pk)
    elif perfil: ruta = get_object_or_404(Ruta, pk=pk, chofer=perfil)
    else: raise Http404
    
    if ruta.status == 'en_curso': # Comparamos con el string
        # 1. Actualiza el estado de la Ruta
        ruta.status = Ruta.STATUS_COMPLETADA # Usamos la variable del modelo para asignar
        ruta.save(update_fields=['status'])
        
        # 2. ¡NUEVO! Actualiza TODOS los fletes "enganchados" a esta ruta
        ruta.fletes_asignados.filter(estado=Flete.ESTADO_EN_TRANSITO).update(estado=Flete.ESTADO_ENTREGADO)
        
        messages.success(request, f"Ruta '{ruta.titulo}' completada. Fletes actualizados a 'Entregado'.")
    
    return redirect('vehiculos:dashboard')

@login_required
@admin_o_logistica_required
def lista_mantenimientos(request):
    mantenimientos = Mantenimiento.objects.all().order_by('-fecha')
    contexto = {
        'mantenimientos': mantenimientos
    }
    return render(request, 'vehiculos/lista_mantenimientos.html', contexto)

@login_required
@admin_o_logistica_required
def registrar_mantenimiento(request):
    DetalleFormSet = inlineformset_factory(
        Mantenimiento, 
        DetalleMantenimiento, 
        form=DetalleMantenimientoForm, 
        extra=3,
        can_delete=False
    )

    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        formset = DetalleFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            mantenimiento = form.save(commit=False)
            mantenimiento.save()
            
            formset.instance = mantenimiento
            formset.save() 

            messages.success(request, '¡Mantenimiento registrado! El vehículo y el inventario han sido actualizados.')
            return redirect('vehiculos:lista_mantenimientos')
    else:
        form = MantenimientoForm()
        formset = DetalleFormSet()

    contexto = {
        'form': form,
        'formset': formset
    }
    return render(request, 'vehiculos/registrar_mantenimiento.html', contexto)

# =============================================
# VISTAS DE REPORTE Y EXPORTACIÓN
# =============================================

@login_required
@admin_o_logistica_required
def reporte_consumo(request):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    today = date.today()

    fecha_inicio_str = request.GET.get('fecha_inicio', today.replace(day=1).strftime('%Y-%m-%d'))
    fecha_fin_str = request.GET.get('fecha_fin', today.strftime('%Y-%m-%d'))
    vehiculo_id_filtro = request.GET.get('vehiculo')

    fecha_inicio = None
    fecha_fin = None
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        dt_inicio = datetime.combine(fecha_inicio, time.min)
    except (ValueError, TypeError):
        messages.error(request, "Fecha de inicio inválida.")
        dt_inicio = None
    try:
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        dt_fin = datetime.combine(fecha_fin, time.max)
    except (ValueError, TypeError):
        messages.error(request, "Fecha de fin inválida.")
        dt_fin = None

    if user.is_staff:
        vehiculos_base = Vehiculo.objects.filter(activo=True)
    elif perfil:
        vehiculos_base = Vehiculo.objects.filter(activo=True, chofer_asignado=perfil)
    else:
        vehiculos_base = Vehiculo.objects.none()

    vehiculos_filtrados = vehiculos_base
    if vehiculo_id_filtro:
        try:
            vehiculos_filtrados = vehiculos_base.filter(id=int(vehiculo_id_filtro))
        except (ValueError, TypeError):
            messages.error(request, "ID de vehículo inválido.")
            vehiculo_id_filtro = None

    reporte_data = []
    if dt_inicio and dt_fin:
        for vehiculo in vehiculos_filtrados.order_by('placa'):
            cargas_vehiculo = CargaCombustible.objects.filter(
                vehiculo=vehiculo,
                fecha__gte=dt_inicio,
                fecha__lte=dt_fin
            ).order_by('fecha')

            if cargas_vehiculo.exists():
                agregados = cargas_vehiculo.aggregate(
                    total_litros=Sum('litros'),
                    total_costo=Sum('costo'),
                    km_min=Min('odometro'),
                    km_max=Max('odometro')
                )

                total_litros = agregados['total_litros'] or 0
                total_costo = agregados['total_costo'] or 0
                km_inicio = agregados['km_min']
                km_fin = agregados['km_max']

                distancia_recorrida = 0
                if km_inicio is not None and km_fin is not None and km_fin > km_inicio:
                    distancia_recorrida = km_fin - km_inicio

                rendimiento_promedio = 0
                if total_litros > 0 and distancia_recorrida > 0:
                    try:
                        rendimiento_promedio = round(distancia_recorrida / float(total_litros), 2)
                    except (ValueError, TypeError, InvalidOperation):
                        rendimiento_promedio = 0

                reporte_data.append({
                    'vehiculo': vehiculo,
                    'total_litros': total_litros,
                    'total_costo': total_costo,
                    'distancia_recorrida': distancia_recorrida,
                    'rendimiento_promedio': rendimiento_promedio,
                    'num_cargas': cargas_vehiculo.count()
                })

    context = {
        'reporte_data': reporte_data,
        'vehiculos_para_filtro': vehiculos_base.order_by('placa'),
        'vehiculo_id_seleccionado': vehiculo_id_filtro,
        'fecha_inicio_filtro': fecha_inicio_str,
        'fecha_fin_filtro': fecha_fin_str,
    }
    return render(request, 'vehiculos/reporte_consumo.html', context)

@login_required
@admin_o_logistica_required # <-- ¡Aseguramos esta también!
def exportar_todas_tablas(request):
    if not request.user.is_staff: return HttpResponse("Acceso denegado", status=403)
    engine = _create_engine_from_settings_or_env(); tables = []
    try:
        inspector = inspect(engine)
        if 'postgresql' in str(engine.url):
            try: tables = inspector.get_table_names(schema='public')
            except Exception: tables = inspector.get_table_names()
        else: tables = inspector.get_table_names()
    except Exception: tables = ['vehiculos_vehiculo', 'vehiculos_mantenimiento', 'vehiculos_inventario', 'vehiculos_ruta', 'vehiculos_cargacombustible']
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        for t in tables:
            df = pd.DataFrame()
            try:
                try: df = pd.read_sql_table(t, con=engine)
                except Exception: df = pd.read_sql(f"SELECT * FROM {t};", con=engine)
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].apply(lambda x: x if not isinstance(x, bytes) else x.decode('latin1', errors='replace'))
            except Exception: pass
            df.to_excel(writer, sheet_name=(t[:30]), index=False)
    out.seek(0)
    resp = HttpResponse(out.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp['Content-Disposition'] = 'attachment; filename="reporte_flota.xlsx"'
    return resp

def _create_engine_from_settings_or_env():
    db_conf = settings.DATABASES.get('default')
    use_postgres = db_conf and 'postgresql' in db_conf.get('ENGINE', '')
    if use_postgres:
        user = db_conf.get('USER') or os.getenv('DB_USER')
        password = db_conf.get('PASSWORD') or os.getenv('DB_PASS') or os.getenv('DB_PASSWORD')
        host = db_conf.get('HOST') or os.getenv('DB_HOST', 'localhost')
        port = db_conf.get('PORT') or os.getenv('DB_PORT', '5432')
        name = db_conf.get('NAME') or os.getenv('DB_NAME')
        if user and name:
            pw_esc = quote_plus(str(password)) if password else ''
            engine_url = f"postgresql+psycopg2://{user}:{pw_esc}@{host}:{port}/{name}"
            try:
                engine = create_engine(engine_url, connect_args={"options": "-c client_encoding=utf8"})
                with engine.connect(): pass
                return engine
            except Exception as e: print(f"Warning: no se pudo conectar a Postgres ({e})")
    db_path = settings.BASE_DIR / "db.sqlite3"
    return create_engine("sqlite:///" + str(db_path))

# =============================================
# VISTAS DE USUARIO (Signup, Perfil)
# =============================================
def signup(request):
    if SignupForm is None:
        class _FallbackForm(forms.Form):
            username = forms.CharField(max_length=150)
            password = forms.CharField(widget=forms.PasswordInput)
            def save(self):
                u = User.objects.create_user(username=self.cleaned_data['username'], password=self.cleaned_data['password'])
                return u
        CurrentForm = _FallbackForm
    else: CurrentForm = SignupForm
    if request.method == "POST":
        form = CurrentForm(request.POST)
        if form.is_valid():
            user = form.save(); login(request, user); return redirect('vehiculos:dashboard')
    else: form = CurrentForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def mi_perfil(request):
    user = request.user
    perfil, created = Perfil.objects.get_or_create(user=user)
    password_form = CustomPasswordChangeForm(user) if CustomPasswordChangeForm else None
    perfil_form = PerfilForm(instance=perfil, user=user) if PerfilForm else None
    if request.method == 'POST':
        if 'change_password' in request.POST and password_form:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save(); update_session_auth_hash(request, user)
                messages.success(request, '¡Contraseña cambiada!'); return redirect('vehiculos:mi_perfil')
            else: messages.error(request, 'Error al cambiar contraseña.')
        elif 'update_profile' in request.POST and perfil_form:
            perfil_form = PerfilForm(request.POST, instance=perfil, user=user)
            if perfil_form.is_valid():
                perfil_form.save(); messages.success(request, '¡Perfil actualizado!')
                return redirect('vehiculos:mi_perfil')
            else: messages.error(request, 'Error al actualizar perfil.')
    context = {'password_form': password_form, 'perfil_form': perfil_form}
    return render(request, 'vehiculos/mi_perfil.html', context)

# =============================================
# VISTAS DE DETALLE (Ruta, Mantenimiento)
# =============================================
@login_required
def detalle_ruta(request, pk):
    user = request.user
    perfil = getattr(user, 'perfil', None)
    
    # Lógica de permisos (igual que en tus otras vistas)
    if user.is_staff:
        ruta = get_object_or_404(Ruta, pk=pk)
    elif perfil:
        # El chofer solo puede ver rutas que se le asignaron
        ruta = get_object_or_404(Ruta, pk=pk, chofer=perfil)
    else:
        raise Http404 # No es staff y no tiene perfil
        
    contexto = {
        'ruta': ruta
    }
    return render(request, 'vehiculos/detalle_ruta.html', contexto)

@login_required
@admin_o_logistica_required
def detalle_mantenimiento(request, pk):
    # Buscamos el mantenimiento por su ID (pk)
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    
    # Buscamos los items de inventario que se usaron en este mantenimiento
    items_usados = mantenimiento.detalles_items.all()
    
    contexto = {
        'mantenimiento': mantenimiento,
        'items_usados': items_usados
    }
    return render(request, 'vehiculos/detalle_mantenimiento.html', contexto)

# ¡¡¡LA DEFINICIÓN DEL DECORADOR FUE ELIMINADA DE AQUÍ!!!
# (Debe estar en vehiculos/decorators.py)

@login_required
@admin_o_logistica_required # Protegemos esta vista
def lista_fletes(request):
    fletes = Flete.objects.all().order_by('-fecha_creacion')
    contexto = {
        'fletes': fletes
    }
    return render(request, 'vehiculos/lista_fletes.html', contexto)

@login_required
@admin_o_logistica_required # Protegemos esta vista
def crear_flete(request):
    if request.method == 'POST':
        form = FleteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Flete registrado correctamente!')
            return redirect('vehiculos:lista_fletes')
    else:
        form = FleteForm()

    contexto = {
        'form': form
    }
    return render(request, 'vehiculos/crear_flete.html', contexto)

@login_required
@admin_o_logistica_required
def editar_flete(request, pk):
    # Buscamos el flete que queremos editar por su ID (pk)
    flete = get_object_or_404(Flete, pk=pk)
    
    if request.method == 'POST':
        # Llenamos el formulario con los datos nuevos (request.POST)
        # y le decimos que es para editar el flete existente (instance=flete)
        form = FleteForm(request.POST, instance=flete)
        if form.is_valid():
            form.save() # Guardamos los cambios
            messages.success(request, f'¡Flete "{flete.titulo}" actualizado correctamente!')
            return redirect('vehiculos:lista_fletes')
    else:
        # Si es un GET, solo mostramos el formulario
        # lleno con los datos del flete existente
        form = FleteForm(instance=flete)

    contexto = {
        'form': form,
        'flete': flete # Le pasamos el flete para saber cuál estamos editando
    }
    # Reutilizaremos la plantilla de "crear", pero le cambiaremos el título
    return render(request, 'vehiculos/editar_flete.html', contexto)

@login_required
@admin_o_logistica_required
def eliminar_flete(request, pk):
    # Buscamos el flete que queremos eliminar
    flete = get_object_or_404(Flete, pk=pk)
    
    # Guardamos el título para mostrarlo en el mensaje
    titulo_flete = flete.titulo
    
    # Borramos el flete de la base de datos
    flete.delete()
    
    messages.success(request, f'¡Flete "{titulo_flete}" eliminado correctamente!')
    return redirect('vehiculos:lista_fletes')

@login_required
@admin_o_logistica_required
def eliminar_mantenimiento(request, pk):
    # Buscamos el mantenimiento que queremos eliminar
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    
    # Guardamos el título para mostrarlo en el mensaje
    titulo_mantenimiento = mantenimiento.titulo
    placa_vehiculo = mantenimiento.vehiculo.placa
    
    # Borramos el mantenimiento
    # NOTA: Los 'DetalleMantenimiento' (items de inventario)
    # se borrarán en CASCADA automáticamente.
    mantenimiento.delete()
    
    messages.success(request, f'¡Mantenimiento "{titulo_mantenimiento}" del vehículo {placa_vehiculo} eliminado correctamente!')
    return redirect('vehiculos:lista_mantenimientos')


@login_required
@admin_o_logistica_required
def editar_mantenimiento(request, pk):
    # Buscamos el mantenimiento que queremos editar
    mantenimiento = get_object_or_404(Mantenimiento, pk=pk)
    
    # Preparamos el Formset para los items de inventario,
    # igual que en "registrar"
    DetalleFormSet = inlineformset_factory(
        Mantenimiento, 
        DetalleMantenimiento, 
        form=DetalleMantenimientoForm, 
        extra=1, # Solo mostramos 1 fila extra para añadir más
        can_delete=True # Permitimos borrar items
    )
    
    if request.method == 'POST':
        # Llenamos el formulario principal con los datos enviados (request.POST)
        # y le decimos que es para editar el mantenimiento existente (instance=mantenimiento)
        form = MantenimientoForm(request.POST, instance=mantenimiento)
        
        # Llenamos el formset con los datos enviados Y la instancia
        formset = DetalleFormSet(request.POST, instance=mantenimiento)
        
        if form.is_valid() and formset.is_valid():
            form.save() # Guarda cambios del Mantenimiento
            formset.save() # Guarda cambios de los Items
            
            messages.success(request, f'¡Mantenimiento "{mantenimiento.titulo}" actualizado!')
            return redirect('vehiculos:lista_mantenimientos')
    else:
        # Si es un GET, mostramos el formulario lleno con los datos existentes
        form = MantenimientoForm(instance=mantenimiento)
        # Y mostramos el formset con los items que ya estaban guardados
        formset = DetalleFormSet(instance=mantenimiento)

    contexto = {
        'form': form,
        'formset': formset, # Le pasamos el formset igual que en "registrar"
        'mantenimiento': mantenimiento
    }
    # Crearemos una plantilla nueva para esto
    return render(request, 'vehiculos/editar_mantenimiento.html', contexto)

@login_required
@admin_o_logistica_required # ¡Protegemos la vista!
def detalle_flete(request, pk):
    # Buscamos el flete por su ID (pk)
    # Usamos select_related para "traer" los datos de la ruta y el vehículo
    # en una sola consulta, es más eficiente.
    flete = get_object_or_404(
        Flete.objects.select_related(
            'ruta', 
            'ruta__vehiculo', 
            'ruta__chofer__user'
        ), 
        pk=pk
    )
    
    contexto = {
        'flete': flete
    }
    return render(request, 'vehiculos/detalle_flete.html', contexto)