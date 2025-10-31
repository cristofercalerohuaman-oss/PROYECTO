# safe_read.py
import pandas as pd
from sqlalchemy import create_engine

# --- CONFIG ---
DB_USER = "fleetuser"
DB_PASS = "TuPasswordSeguro"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_flota"
VIEW = "v_costo_total_por_vehiculo"
# ---------------

url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# leemos pidiendo latin1 para no fallar en la lectura y luego forzamos limpieza
engine = create_engine(url, connect_args={"options": "-c client_encoding=latin1"})

df = pd.read_sql(f"SELECT * FROM {VIEW};", engine)
# Reemplazamos bytes problemáticos intentando encode->decode con replace
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].apply(lambda x: x.encode('latin1', errors='replace').decode('utf-8', errors='replace') if isinstance(x, str) else x)

df.to_excel("reporte_safe.xlsx", index=False, engine="openpyxl")
print("Exportado reporte_safe.xlsx (caracteres problemáticos reemplazados). Filas:", len(df))
