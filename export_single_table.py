# export_single_table.py
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
import traceback

# Cargar .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST","localhost")
DB_PORT = os.getenv("DB_PORT","5432")
DB_NAME = os.getenv("DB_NAME")
VIEW_OR_TABLE = "v_costo_total_por_vehiculo"   # cambia por tu tabla o vista
OUTFILE = "reporte_flota_real.xlsx"

def get_engine(enc="utf8"):
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # forzamos client_encoding para evitar errores de decoding
    return create_engine(url, connect_args={"options": f"-c client_encoding={enc}"})

def main():
    try:
        engine = get_engine("utf8")
        q = VIEW_OR_TABLE if VIEW_OR_TABLE.strip().lower().startswith("select") else f"SELECT * FROM {VIEW_OR_TABLE};"
        print("Ejecutando consulta...")
        df = pd.read_sql(q, engine)
        print("Filas leídas:", len(df))
        # Normalizar strings para evitar caracteres raros en excel
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.encode('latin1', errors='replace').decode('utf-8', errors='replace') if isinstance(x, str) else x)
        # Guardar .xlsx real
        df.to_excel(OUTFILE, index=False, engine="openpyxl")
        print("✅ Exportado a:", OUTFILE)
    except Exception:
        print("❌ Error durante exportación:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
