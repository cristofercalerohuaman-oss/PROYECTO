# export_xlsx.py
import pandas as pd
from sqlalchemy import create_engine
import traceback

# --- CONFIGURA AQUÍ ---
DB_USER = "user_ascii"           # tu usuario DB
DB_PASS = "PassSimple123"    # tu contraseña
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Gestion_Flota"
VIEW_OR_QUERY = "v_costo_total_por_vehiculo"  # vista o tabla o una query completa
OUTFILE = "reporte_flota_real.xlsx"
# ------------------------

def get_engine(client_encoding="utf8"):
    # Forzamos client_encoding para evitar problemas de decoding
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # la opción -c client_encoding=... le dice al servidor el encoding del cliente
    return create_engine(url, connect_args={"options": f"-c client_encoding={client_encoding}"})

def export_view(engine, view_name, outfile):
    try:
        # Si view_name contiene 'SELECT' lo tratamos como query; si no, lo leemos como vista
        if view_name.strip().lower().startswith("select"):
            q = view_name
        else:
            q = f"SELECT * FROM {view_name};"
        print("Ejecutando consulta...")
        df = pd.read_sql(q, engine)
        print("Filas leídas:", len(df))
        # Normalizar strings: reemplazar bytes problemáticos y garantizar utf-8
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(
                lambda x: x.encode('latin1', errors='replace').decode('utf-8', errors='replace')
                if isinstance(x, str) else x
            )
        # Guardar como .xlsx real con openpyxl
        df.to_excel(outfile, index=False, engine="openpyxl")
        print("✅ Exportado correctamente a:", outfile)
    except Exception as e:
        print("❌ Error durante exportación:")
        traceback.print_exc()

if __name__ == "__main__":
    # Intento 1: con UTF-8
    print("Intento con client_encoding=utf8")
    try:
        eng = get_engine("utf8")
        export_view(eng, VIEW_OR_QUERY, OUTFILE)
    except Exception as e:
        print("Fallo con UTF8 — intentando LATIN1")
        # Intento 2: con LATIN1 (común en Windows)
        try:
            eng = get_engine("latin1")
            export_view(eng, VIEW_OR_QUERY, OUTFILE)
        except Exception:
            print("Fallo definitivo. Revisa credenciales, servidor o ejecuta la exportación desde pgAdmin.")
