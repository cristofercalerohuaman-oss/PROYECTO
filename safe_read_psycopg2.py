# safe_read_psycopg2.py
import psycopg2
import pandas as pd
import traceback
from sqlalchemy import create_engine

DB_USER = "fleetuser"
DB_PASS = "TuPasswordSeguro"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_flota"
VIEW = "v_costo_total_por_vehiculo"

# Intentamos conectar por psycopg2 (keyword args) y forzar encoding después
try:
    print("Intentando conexión directa psycopg2 (y luego forzar client_encoding)...")
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
    # Forzamos la codificación del cliente
    conn.set_client_encoding('LATIN1')   # cambia a 'WIN1252' si lo prefieres
    print("Conectado. client_encoding seteado a LATIN1.")
    # Usamos pandas con esta conexión abierta
    q = f"SELECT * FROM {VIEW};"
    df = pd.read_sql(q, conn)
    # Limpiamos reemplazando bytes problemáticos
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].apply(lambda x: x.encode('latin1', errors='replace').decode('utf-8', errors='replace') if isinstance(x, str) else x)
    df.to_excel("reporte_safe_psycopg2.xlsx", index=False)
    print("Exportado reporte_safe_psycopg2.xlsx (filas: {})".format(len(df)))
    conn.close()
except Exception as e:
    print("Fallo conexión o lectura via psycopg2:")
    traceback.print_exc()
    # Intento fallback con SQLAlchemy + opción client_encoding en connect_args
    try:
        print("Intentando fallback con SQLAlchemy connect_args options=-c client_encoding=latin1 ...")
        url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(url, connect_args={"options": "-c client_encoding=latin1"})
        df = pd.read_sql(f"SELECT * FROM {VIEW};", engine)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.encode('latin1', errors='replace').decode('utf-8', errors='replace') if isinstance(x, str) else x)
        df.to_excel("reporte_safe_sqlalchemy.xlsx", index=False)
        print("Exportado reporte_safe_sqlalchemy.xlsx (filas: {})".format(len(df)))
    except Exception:
        print("Fallback falló también. Revisa credenciales, servidor y que PG esté activo.")
        traceback.print_exc()
