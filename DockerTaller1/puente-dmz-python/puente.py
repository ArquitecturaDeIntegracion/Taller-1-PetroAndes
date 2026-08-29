import json
import os
import paho.mqtt.client as mqtt
from confluent_kafka import Producer

# Configuración de Kafka (Redpanda)
kafka_conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:19092'),
    'broker.address.family': 'v4'
}
kafka_producer = Producer(kafka_conf)

def delivery_report(err, msg):
    """Callback de confirmación de entrega en Redpanda."""
    if err is not None:
        print(f"[DMZ Bridge] Error al publicar en Redpanda: {err}")
    else:
        print(f"[DMZ Bridge] Publicado en Redpanda (topic: {msg.topic()})")

# Configuración de MQTT (Broker OT)
mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
mqtt_topic = "petroandes/ot/ducto/telemetria"

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Puente DMZ activo. Conectado a MQTT con código: {reason_code}")
    client.subscribe(mqtt_topic)
    print(f"Suscrito a MQTT: {mqtt_topic}. Replicando a Redpanda...")

def on_message(client, userdata, msg):
    try:
        # 1. Recibir payload de MQTT (Red OT)
        raw_payload = msg.payload.decode('utf-8')
        json_payload = json.loads(raw_payload)
        print(f"\n[DMZ Bridge] Recibido de MQTT: {json_payload}")

        # 2. Transformar a CloudEvents
        cloud_event = {
            "specversion": "1.0",
            "type": "telemetria.ducto",
            "source": "/petroandes/ot/scada",
            "datacontenttype": "application/json",
            "data": json_payload
        }
        
        # 3. Publicar en Redpanda (Red IT)
        kafka_producer.produce(
            topic="it-telemetria-topic",
            value=json.dumps(cloud_event).encode('utf-8'),
            callback=delivery_report
        )
        
        # Liberar la cola de callbacks de Kafka
        kafka_producer.poll(0)
        
    except Exception as e:
        print(f"[DMZ Bridge] Error procesando mensaje: {e}")

# Inicializar cliente MQTT
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    # Conexión asíncrona y ciclo de escucha
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\nDeteniendo Puente DMZ...")
finally:
    # Asegurar que todos los mensajes en la cola interna de Kafka se envíen antes de cerrar
    print("Vaciando cola de mensajes hacia Redpanda...")
    kafka_producer.flush()