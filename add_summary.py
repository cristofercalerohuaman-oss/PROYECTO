# add_summary.py
import pandas as pd
from openpyxl import load_workbook

XFILE = "base_completa.xlsx"
UMBRAL_STOCK = 5  # ajustar

# leer hojas relevantes
xls = pd.read_excel(XFILE, sheet_name=None)  # dict de DataFrames

# total gasto por mes (si existe columna 'costo' y 'fecha')
if 'vehiculos_mantenimiento' in xls:
    m = xls['vehiculos_mantenimiento'].copy()
    if 'fecha' in m.columns:
        m['fecha'] = pd.to_datetime(m['fecha'], errors='coerce')
        m['mes'] = m['fecha'].dt.to_period('M').astype(str)
        gastos_mes = m.groupby('mes', dropna=True)['costo'].sum().reset_index().sort_values('mes')
    else:
        gastos_mes = pd.DataFrame(columns=['mes','costo'])
else:
    gastos_mes = pd.DataFrame(columns=['mes','costo'])

# vehiculo con mayor gasto total
if not m.empty:
    gasto_por_veh = m.groupby('vehiculo')['costo'].sum().reset_index().sort_values('costo', ascending=False)
else:
    gasto_por_veh = pd.DataFrame(columns=['vehiculo','costo'])

# inventario bajo
if 'vehiculos_inventario' in xls:
    inv = xls['vehiculos_inventario'].copy()
    if 'cantidad' in inv.columns:
        inv_bajo = inv[inv['cantidad'] <= UMBRAL_STOCK].sort_values('cantidad')
    else:
        inv_bajo = pd.DataFrame()
else:
    inv_bajo = pd.DataFrame()

# escribir hojas nuevas (mantener existentes)
with pd.ExcelWriter(XFILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    gastos_mes.to_excel(writer, sheet_name="Resumen_Gastos_Mes", index=False)
    gasto_por_veh.to_excel(writer, sheet_name="Resumen_Gasto_Veh", index=False)
    inv_bajo.to_excel(writer, sheet_name="Inventario_Bajo", index=False)

print("Resumen agregado en base_completa.xlsx")
