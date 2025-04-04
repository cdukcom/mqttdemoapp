import paho.mqtt.client as mqtt
import json
import os
from twilio.rest import Client
from datetime import datetime

# Cargar configuración desde variables de entorno

# Configuración del broker MQTT
BROKER = os.getenv("MQTT_BROKER", "a6cc2b96.ala.us-east-1.emqxsl.com")
PORT = int(os.getenv("MQTT_PORT", 8883))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")

# Configuración de Twilio
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
DESTINATION_NUMBER = os.getenv("DESTINATION_NUMBER")

# Ruta del archivo de log
LOG_FILE = "mqtt_messages.log"

TOPICS = [
    "/LCG-300-NR/00046587",
    "/LCG-300-NR/0004648A",
    "/LCG-300-NR/0004648C"
]

client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Función para formatear fecha y hora
def format_datetime(iso_time):
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", ""))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "Fecha desconocida"

# Función para guardar logs
def log_message(topic, message):
    try:
        with open(LOG_FILE, "a") as file:
            file.write(f"[{datetime.now()}] Tópico: {topic} | Mensaje: {message}\n")
    except Exception as e:
        print(f"Error al escribir en el log: {e}")

# Función para enviar mensaje por WhatsApp
# Callback cuando se recibe un mensaje MQTT

def send_whatsapp_message(message):
    try:
        data = json.loads(message.payload.decode("utf-8"))
        payload = data.get("Payload", {})
        device = payload.get("Device", "Desconocido")
        contact = payload.get("Contact Detection", "")
        fire_alarm = payload.get("Fire Alarm", "")
        temp_alarm = payload.get("High Temperature Alarm", "")
        temp = payload.get("Temperature (°C)", "N/A")
        humidity = payload.get("Humidity (%)", "N/A")
        time = format_datetime(data.get("Time", ""))

        formatted_message = ""

        if device == "LS100-DW":  # Sensor de puerta
            estado_puerta = "Abierta" if contact == "Open" else "Cerrada"
            formatted_message = f"🚪 Edificio 138 Puerta 708 = {estado_puerta}\n{time}"

        elif device == "LS100-SMK":  # Sensor de humo
            estado_humo = "🔥 ALERTA DE INCENDIO" if fire_alarm == "On" else "🔥 Detector Incendio Normal"
            estado_temp = "🌡️ ALERTA DE TEMPERATURA ALTA" if temp_alarm == "On" else "🌡️ Temperatura Normal"
            formatted_message = (
                f"{estado_humo}\n{estado_temp}\n"
                f"Ubicación: Edificio 138 Piso 7 Apartado 08\n{time}"
            )

        elif device == "LS200-TH":  # Sensor temperatura y humedad
            formatted_message = (
                f"🌡️ Temp: {temp}°C | 💧 Humedad: {humidity}%\n"
                f"Ubicación: Edificio 138 Piso 7 Apartado 08\n{time}"
            )

        else:
            formatted_message = f"Mensaje desconocido en {message.topic}:\n{json.dumps(data)}"

        client_twilio.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=DESTINATION_NUMBER,
            body=formatted_message
        )

    except Exception as e:
        print(f"Error al enviar mensaje: {e}")

# Conectar al broker y suscribirse a los tópicos
def on_connect(client, userdata, flags, rc):
    print(f"Conectado al broker {BROKER}:{PORT}")
    for topic in TOPICS:
        client.subscribe(topic)
        print(f"Suscrito al tópico {topic}")

def on_message(client, userdata, message):
    # Guardar el mensaje en el log
    log_message(message.topic, message.payload.decode("utf-8"))
    # Procesar para WhatsApp
    send_whatsapp_message(message)

# Configuración del cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.tls_set() # Activar TLS/SSL
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Conectar al broker y suscribirse a los tópicos
client.connect(BROKER, PORT, 60)

#YY Iniciar el loop para recibir mensajes
client.loop_forever()
