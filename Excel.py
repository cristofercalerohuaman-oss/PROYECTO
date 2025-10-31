import sqlite3
import pandas as pd

# Conexión a tu base de datos
conn = sqlite3.connect("inventario.db")

# Leer toda la tabla de inventario
df = pd.read_sql_query("SELECT * FROM inventario", conn)

# Guardar en Excel
df.to_excel("inventario.xlsx", index=False)

conn.close()
