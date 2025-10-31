# test_encodings.py
import pandas as pd
from sqlalchemy import create_engine

DB_USER = "fleetuser"           # tu usuario
DB_PASS = "TuPasswordSeguro"    # tu contraseña
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_flota"

encodings = ["utf8", "latin1", "win1252"]

def test_encoding(enc):
    print(f"\n>>> Probando client_encoding = {enc}")
    try:
        url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(url, connect_args={"options": f"-c client_encoding={enc}"})
        q = "SELECT * FROM v_costo_total_por_vehiculo;"
        df = pd.read_sql(q, engine)
        print(f"OK con {enc} — filas: {len(df)}")
        out = f"salida_{enc}.xlsx"
        df.to_excel(out, index=False)
        print(f"Archivo exportado: {out}")
    except Exception as e:
        print(f"FALLO con {enc}: {e}")

for e in encodings:
    test_encoding(e)
