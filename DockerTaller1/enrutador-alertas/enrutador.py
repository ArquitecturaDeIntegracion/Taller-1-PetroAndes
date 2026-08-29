import json
import os
import requests
from confluent_kafka import Consumer

# Configuración de Redpanda
conf = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:19092'),
    'group.id': 'grupo-enrutador-balance',
    'auto.offset.reset': 'latest',
    'broker.address.family': 'v4'
}

consumer = Consumer(conf)
topic_alertas = "it-alertas-topic"
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/alertas")

consumer.subscribe([topic_alertas])
print(f"Enrutador iPaaS iniciado. Escuchando tópico '{topic_alertas}' y conectando con API REST...")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            continue

        # Extraer datos de la alerta generada por el detector
        payload = json.loads(msg.value().decode('utf-8'))
        datos = payload.get("data", {})
        
        # Mapear datos al contrato de la API REST
        alerta_api = {
            "id_alerta": payload.get("id"),
            "tramo": datos.get("tramo"),
            "nivel_riesgo": datos.get("nivel_riesgo"),
            "descripcion": datos.get("descripcion"),
            "presion_psi": datos.get("presion_actual_psi"),
            "caudal_bpd": datos.get("caudal_actual_bpd")
        }

        print(f"\n[Enrutador] Alerta detectada. Enviando vía HTTP POST a {API_URL}...")
        
        # Integración con el negocio (Llamada REST)
        respuesta = requests.post(API_URL, json=alerta_api, timeout=10)
        
        if respuesta.status_code == 200:
            print("[Enrutador] ✅ Integración exitosa. El sistema de balance ha sido notificado.")
        else:
            print(f"[Enrutador] ❌ Error en integración. Status: {respuesta.status_code}")

except KeyboardInterrupt:
    print("\nDeteniendo enrutador...")
finally:
    consumer.close()