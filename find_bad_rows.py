# find_bad_rows.py
import psycopg2
import csv
import sys

# --- CONFIGURA AQUI ---
DB_USER = "fleetuser"
DB_PASS = "TuPasswordSeguro"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gestion_flota"
TABLE_OR_VIEW = "v_costo_total_por_vehiculo"  # vista o tabla que da problemas
# ------------------------

# Conectamos pidiendo client_encoding=latin1 para leer bytes crudos
conn_str = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASS} options='-c client_encoding=latin1'"
print("Conectando con client_encoding=latin1...")
conn = psycopg2.connect(conn_str)
cur = conn.cursor()

query = f"SELECT * FROM {TABLE_OR_VIEW};"
print("Ejecutando query:", query)
cur.execute(query)

cols = [desc[0] for desc in cur.description]
print("Columnas detectadas:", cols)

bad_rows_file = "filas_problema.csv"
with open(bad_rows_file, "w", newline='', encoding="utf-8") as fout:
    writer = csv.writer(fout)
    # encabezado: intentamos incluir 'id' si está entre las columnas
    writer.writerow(["row_number"] + cols + ["error_column","error_message"])
    row_num = 0
    fetch_size = 200
    while True:
        rows = cur.fetchmany(fetch_size)
        if not rows:
            break
        for r in rows:
            row_num += 1
            problem = False
            err_col = ""
            err_msg = ""
            new_row = list(r)
            # comprobar cada columna string (tratamos bytes como latin1 y luego decode utf-8 para detectar error)
            for i, val in enumerate(r):
                if isinstance(val, str):
                    try:
                        # probar re-decode: interpretamos los bytes como latin1 y tratamos de decodificar a utf-8
                        _ = val.encode('latin1').decode('utf-8')
                    except Exception as e:
                        problem = True
                        err_col = cols[i]
                        err_msg = str(e)
                        new_row[i] = "[BAD_BYTES]"
                        break
            if problem:
                writer.writerow([row_num] + new_row + [err_col, err_msg])

print(f"Proceso finalizado. Filas problemáticas guardadas en: {bad_rows_file}")
cur.close()
conn.close()
