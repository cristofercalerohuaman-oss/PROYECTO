import psycopg2

try:
    conn = psycopg2.connect(
        dbname="gestion_flota",   # Nombre de tu base de datos
        user="postgres",          # Usuario de postgres
        password="tu_contraseña", # ⚠️ pon aquí tu contraseña real
        host="localhost",
        port="5432"
    )
    print("✅ Conexión exitosa a la base de datos")
    conn.close()
except Exception as e:
    print("❌ Error al conectar:", e)
