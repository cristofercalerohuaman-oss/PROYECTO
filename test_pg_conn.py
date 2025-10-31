# test_pg_conn.py
import os
from psycopg2 import connect, OperationalError

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST","localhost")
DB_PORT = os.getenv("DB_PORT","5432")
DB_NAME = os.getenv("DB_NAME")

print("Probando conexión con:")
print(" DB_HOST:", DB_HOST, " DB_PORT:", DB_PORT, " DB_NAME:", DB_NAME, " DB_USER:", DB_USER)

try:
    conn = connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
    print("Conectado OK (psycopg2).")
    conn.close()
except OperationalError as e:
    print("OperationalError:", repr(e))
except Exception as e:
    print("Error general:", repr(e))
