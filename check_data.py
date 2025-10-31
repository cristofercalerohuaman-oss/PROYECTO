# check_data.py
import os
import django
from decimal import Decimal, InvalidOperation

# Configura Django para poder usar los modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flota_site.settings')
django.setup()

# Ahora sí, el código de verificación
from vehiculos.models import CargaCombustible
from django.db import connection

print("Buscando datos inválidos (modo estricto desde archivo)...")
cursor = connection.cursor()
cursor.execute("SELECT id, litros, costo FROM vehiculos_cargacombustible")
rows = cursor.fetchall()
cursor.close()

error_encontrado = False
for row_id, litros_raw, costo_raw in rows:
    valor_litros_para_probar = litros_raw
    valor_costo_para_probar = costo_raw

    if valor_litros_para_probar is None or str(valor_litros_para_probar).strip() == '':
         valor_litros_para_probar = 0
    if valor_costo_para_probar is None or str(valor_costo_para_probar).strip() == '':
         valor_costo_para_probar = 0

    litros_ok = True
    costo_ok = True

    if isinstance(litros_raw, str) and litros_raw.strip() == '':
        litros_ok = False
    else:
        try:
            Decimal(valor_litros_para_probar)
        except (InvalidOperation, ValueError, TypeError):
            litros_ok = False

    if isinstance(costo_raw, str) and costo_raw.strip() == '':
        costo_ok = False
    else:
        try:
            Decimal(valor_costo_para_probar)
        except (InvalidOperation, ValueError, TypeError):
            costo_ok = False

    if not litros_ok or not costo_ok:
        print(f"--- ¡ERROR ENCONTRADO! ---")
        print(f"  ID de Carga: {row_id}")
        try:
            carga_obj = CargaCombustible.objects.get(id=row_id)
            print(f"  Vehículo: {carga_obj.vehiculo}")
            print(f"  Fecha: {carga_obj.fecha}")
        except CargaCombustible.DoesNotExist:
            print(f"  (No se pudo obtener más info del objeto)")
        print(f"  Valor crudo en Litros: '{litros_raw}' (Tipo: {type(litros_raw)})")
        print(f"  Valor crudo en Costo: '{costo_raw}' (Tipo: {type(costo_raw)})")
        print(f"--------------------------")
        error_encontrado = True

if not error_encontrado:
    print("No se encontraron errores de formato decimal (ni strings vacíos) en las cargas.")

print("--- Fin del script ---")