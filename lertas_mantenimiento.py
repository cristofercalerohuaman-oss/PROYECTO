# alertas_mantenimiento.py
import os
import smtplib
import logging
from email.message import EmailMessage
from datetime import date
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar .env si existe
load_dotenv()

# ---------- Config ----------
DB_USER = os.getenv("DB_USER", "user_ascii")
DB_PASS = os.getenv("DB_PASS", "PassSimple123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gestion_flota")

UMBRAL_DIAS = int(os.getenv("UMBRAL_DIAS", "180"))

# Telegram
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()

# Email SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")

LOGFILE = os.path.join(os.path.dirname(__file__), "alertas.log")

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGFILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ---------- DB Connection ----------
def get_engine(client_encoding="utf8"):
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url, connect_args={"options": f"-c client_encoding={client_encoding}"})

# ---------- Query: vehículos con días desde último mantenimiento ----------
QUERY = """
SELECT v.id, v.placa, v.marca, v.modelo,
       MAX(m.fecha) AS ultima_fecha,
       CASE WHEN MAX(m.fecha) IS NULL THEN NULL ELSE (CURRENT_DATE - MAX(m.fecha)) END AS dias_desde
FROM vehiculos v
LEFT JOIN mantenimiento m ON m.vehiculo_id = v.id
GROUP BY v.id, v.placa, v.marca, v.modelo
HAVING (MAX(m.fecha) IS NULL) OR ((CURRENT_DATE - MAX(m.fecha)) > :umbral)
ORDER BY dias_desde DESC NULLS LAST;
"""

def fetch_vehiculos_criticos(engine, umbral):
    with engine.connect() as conn:
        # pasamos el intervalo como texto: e.g. '180 days'
        res = conn.execute(text(QUERY), {"umbral": f"{umbral} days"})
        rows = [dict(row) for row in res]
    return rows

# ---------- Envío Telegram ----------
def send_telegram_message(token, chat_id, text_msg):
    if not token or not chat_id:
        logging.info("Telegram no configurado, salto envío Telegram.")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text_msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
        logging.info("Mensaje enviado por Telegram.")
        return True
    except Exception:
        logging.exception("Fallo envío Telegram:")
        return False

# ---------- Envío Email ----------
def send_email(subject, body, smtp_host, smtp_port, smtp_user, smtp_pass, from_addr, to_addr):
    if not smtp_host or not smtp_user or not smtp_pass or not to_addr:
        logging.info("SMTP no configurado correctamente, salto envío email.")
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if smtp_port in (587, 25):
                server.starttls()
                server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        logging.info("Email enviado correctamente.")
        return True
    except Exception:
        logging.exception("Fallo envío Email:")
        return False

# ---------- Formateo mensaje ----------
def build_message(rows, umbral):
    if not rows:
        return f"✅ Todos los vehículos tienen mantenimiento dentro de los últimos {umbral} días. (Fecha: {date.today()})"
    header = f"⚠️ *Alerta de mantenimiento* — Vehículos sin mantenimiento en los últimos {umbral} días\n\n"
    lines = []
    for r in rows:
        dias = r.get("dias_desde")
        if dias is None:
            dias_text = "Sin historial"
        else:
            dias_text = str(dias)
        placa = r.get("placa") or "-"
        marca = r.get("marca") or ""
        modelo = r.get("modelo") or ""
        ultima = r.get("ultima_fecha") or "N/A"
        lines.append(f"- *{placa}* ({marca} {modelo}) — Últ. mantenimiento: {ultima} — Días: {dias_text}")
    footer = "\n\nRevisa la planificación y programa mantenimiento preventivo."
    return header + "\n".join(lines) + footer

# ---------- Main ----------
def main():
    logging.info("Iniciando comprobación de mantenimiento.")
    try:
        engine = get_engine()
    except Exception:
        logging.exception("No se pudo crear engine de DB. Revisa credenciales/DB.")
        return

    try:
        rows = fetch_vehiculos_criticos(engine, UMBRAL_DIAS)
        logging.info(f"Vehículos críticos encontrados: {len(rows)}")
    except Exception:
        logging.exception("Error al ejecutar consulta en DB.")
        return

    message = build_message(rows, UMBRAL_DIAS)
    logging.info("Mensaje preparado:\n" + message)

    sent_tg = False
    sent_email = False

    # Intentar enviar por Telegram si configurado
    if TG_BOT_TOKEN and TG_CHAT_ID:
        sent_tg = send_telegram_message(TG_BOT_TOKEN, TG_CHAT_ID, message)

    # Intentar email si está configurado
    if SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO:
        subject = f"[Alerta] Mantenimiento > {UMBRAL_DIAS} días - {len(rows)} vehículos"
        sent_email = send_email(subject, message, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO)

    logging.info(f"Envio Telegram: {sent_tg}, Envio Email: {sent_email}")
    logging.info("Ejecución finalizada.")

if __name__ == "__main__":
    main()
