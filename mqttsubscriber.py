{\rtf1\ansi\ansicpg1252\cocoartf2821
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import paho.mqtt.client as mqtt\
import json\
from twilio.rest import Client\
\
# Configuraci\'f3n del broker MQTT\
BROKER = "test.mosquitto.org"  # Puedes cambiarlo por el broker que est\'e9s usando\
PORT = 1883\
TOPICS = [\
    "/LCG-300-NR/0004648AQoS: 0",\
    "/LCG-300-NR/0004648CQoS: 0",\
    "/LCG-300-NR/00046587QoS: 0",\
    "/LCG-300-NR/0004648A",\
    "/LCG-300-NR/0004648C"\
]\
\
# Configuraci\'f3n de Twilio\
TWILIO_ACCOUNT_SID = "TU_ACCOUNT_SID"\
TWILIO_AUTH_TOKEN = "TU_AUTH_TOKEN"\
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # N\'famero de Twilio para WhatsApp\
DESTINATION_NUMBER = "whatsapp:+573134991467"  # N\'famero de destino\
\
client_twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)\
\
# Funci\'f3n para enviar mensaje por WhatsApp\
def send_whatsapp_message(message):\
    client_twilio.messages.create(\
        from_=TWILIO_WHATSAPP_NUMBER,\
        to=DESTINATION_NUMBER,\
        body=message\
    )\
\
# Callback cuando se recibe un mensaje MQTT\
def on_message(client, userdata, msg):\
    try:\
        payload = msg.payload.decode()\
        print("Mensaje recibido en el t\'f3pico:", msg.topic)\
        print(payload)\
        \
        # Manejo especial para el t\'f3pico /LCG-300-NR/0004648A\
        if msg.topic == "/LCG-300-NR/0004648A":\
            if "OPEN" in payload:\
                message = "\uc0\u55357 \u57002  *Alerta de puerta*\\nPuerta 001 Abierta"\
            elif "CLOSE" in payload:\
                message = "\uc0\u55357 \u57002  *Alerta de puerta*\\nPuerta 001 Cerrada"\
            else:\
                message = f"Mensaje desconocido en \{msg.topic\}: \{payload\}"\
        # Manejo especial para el t\'f3pico /LCG-300-NR/0004648C\
        elif msg.topic == "/LCG-300-NR/0004648C":\
            payload_json = json.loads(payload)\
            fire_alarm_status = payload_json.get("Payload", \{\}).get("Fire Alarm", "Desconocido")\
            if fire_alarm_status == "Normal":\
                message = "\uc0\u55357 \u56613  *Estado del sensor*: NORMAL"\
            elif fire_alarm_status == "On":\
                message = "\uc0\u55357 \u57000 \u55357 \u56613  *ALERTA DE INCENDIO* \u55357 \u56613 \u55357 \u57000 "\
            else:\
                message = f"\uc0\u55357 \u56613  *Estado del sensor*: \{fire_alarm_status\}"\
        # Manejo especial para el t\'f3pico /LCG-300-NR/00046587 (Humedad y Temperatura)\
        elif msg.topic == "/LCG-300-NR/00046587QoS: 0":\
            payload_json = json.loads(payload)\
            humidity = payload_json.get("Payload", \{\}).get("Humidity (%)", "Desconocido")\
            temperature = payload_json.get("Payload", \{\}).get("Temperature (\'b0C)", "Desconocido")\
            message = f"\uc0\u55356 \u57121 \u65039  *Datos Ambientales*\\n\u55357 \u56487  Humedad: \{humidity\}%\\n\u55356 \u57121 \u65039  Temperatura: \{temperature\}\'b0C"\
        else:\
            # Procesar mensaje JSON\
            payload = json.loads(payload)\
            device = payload.get("Payload", \{\}).get("Device", "Desconocido")\
            timestamp = payload.get("Time", "Desconocido")\
            data = payload.get("Payload", \{\})\
            data_str = "\\n".join([f"\{key\}: \{value\}" for key, value in data.items() if key != "Device"])\
            \
            message = f"\uc0\u55357 \u56545  *Nuevo mensaje MQTT recibido*\\n\u55357 \u56517  Timestamp: \{timestamp\}\\n\u55357 \u56543  Dispositivo: \{device\}\\n\{data_str\}"\
        \
        send_whatsapp_message(message)\
        \
    except json.JSONDecodeError as e:\
        print("Error al decodificar JSON:", e)\
\
# Configuraci\'f3n del cliente MQTT\
client = mqtt.Client()\
client.on_message = on_message\
\
# Conectar al broker y suscribirse a los t\'f3picos\
client.connect(BROKER, PORT, 60)\
for topic in TOPICS:\
    client.subscribe(topic)\
    print(f"Suscrito al t\'f3pico \{topic\}")\
\
print(f"Conectado al broker \{BROKER\}:\{PORT\}")\
\
# Iniciar el loop para recibir mensajes\
client.loop_forever()\
}