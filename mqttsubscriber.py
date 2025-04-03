import paho.mqtt.client as mqtt
import json
from twilio.rest import Client

# Configuración del broker MQTT
BROKER = "broker.emqx.io"  # Puedes cambiarlo por el broker que estés usando
PORT = 1883
TOPICS = [
    "/LCG-300-NR/0004648AQoS: 0",
    "/LCG-300-NR/0004648CQoS: 0",
    "/LCG-300-NR/00046587QoS: 0",
    "/LCG-300-NR/0004648A",
    "/LCG-300-NR/0004648C"
]

# Configuración de Twilio
TWILIO_ACCOUNT_SID = "TU_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "TU_AUTH_TOKEN"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Número de Twilio para WhatsApp
DESTINATION_NUMBER = "whatsapp:+573134991467"  # Número de destino

client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Función para enviar mensaje por WhatsApp
def send_whatsapp_message(message):
    client_twilio.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=DESTINATION_NUMBER,
        body=message
    )

# Callback cuando se recibe un mensaje MQTT
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("Mensaje recibido en el tópico:", msg.topic)
        print(payload)
        
        # Manejo especial para el tópico /LCG-300-NR/0004648A
        if msg.topic == "/LCG-300-NR/0004648A":
            if "OPEN" in payload:
                message = "🚪 *Alerta de puerta*\nPuerta 001 Abierta"
            elif "CLOSE" in payload:
                message = "🚪 *Alerta de puerta*\nPuerta 001 Cerrada"
            else:
                message = f"Mensaje desconocido en {msg.topic}: {payload}"
        # Manejo especial para el tópico /LCG-300-NR/0004648C
        elif msg.topic == "/LCG-300-NR/0004648C":
            payload_json = json.loads(payload)
            fire_alarm_status = payload_json.get("Payload", {}).get("Fire Alarm", "Desconocido")
            if fire_alarm_status == "Normal":
                message = "🔥 *Estado del sensor*: NORMAL"
            elif fire_alarm_status == "On":
                message = "🚨🔥 *ALERTA DE INCENDIO* 🔥🚨"
            else:
                message = f"🔥 *Estado del sensor*: {fire_alarm_status}"
        # Manejo especial para el tópico /LCG-300-NR/00046587 (Humedad y Temperatura)
        elif msg.topic == "/LCG-300-NR/00046587QoS: 0":
            payload_json = json.loads(payload)
            humidity = payload_json.get("Payload", {}).get("Humidity (%)", "Desconocido")
            temperature = payload_json.get("Payload", {}).get("Temperature (°C)", "Desconocido")
            message = f"🌡️ *Datos Ambientales*\n💧 Humedad: {humidity}%\n🌡️ Temperatura: {temperature}°C"
        else:
            # Procesar mensaje JSON
            payload = json.loads(payload)
            device = payload.get("Payload", {}).get("Device", "Desconocido")
            timestamp = payload.get("Time", "Desconocido")
            data = payload.get("Payload", {})
            data_str = "\n".join([f"{key}: {value}" for key, value in data.items() if key != "Device"])
            
            message = f"📡 *Nuevo mensaje MQTT recibido*\n📅 Timestamp: {timestamp}\n📟 Dispositivo: {device}\n{data_str}"
        
        send_whatsapp_message(message)
        
    except json.JSONDecodeError as e:
        print("Error al decodificar JSON:", e)

# Configuración del cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message

# Conectar al broker y suscribirse a los tópicos
client.connect(BROKER, PORT, 60)
for topic in TOPICS:
    client.subscribe(topic)
    print(f"Suscrito al tópico {topic}")

print(f"Conectado al broker {BROKER}:{PORT}")

#YY Iniciar el loop para recibir mensajes
client.loop_forever()

