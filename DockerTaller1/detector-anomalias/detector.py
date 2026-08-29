import json
import uuid
import os
from collections import deque
from confluent_kafka import Consumer, Producer

# 1. Configuración de conexión a Redpanda (Forzando IPv4)
conf_base = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '127.0.0.1:19092'),
    'broker.address.family': 'v4'
}

# Consumidor para leer telemetría
consumer = Consumer({
    **conf_base,
    'group.id': 'grupo-deteccion-fraude',
    'auto.offset.reset': 'latest' # Ignorar histórico, evaluar tiempo real
})

# Productor para emitir alertas
producer = Producer(conf_base)

topic_entrada = "it-telemetria-topic"
topic_salida = "it-alertas-topic"

# 2. Estado en memoria para la regla de negocio
# Analizaremos una ventana móvil de las últimas 3 lecturas consecutivas (aprox. 6 segundos)
ventana_lecturas = deque(maxlen=3)

# Umbrales basados en el comportamiento normal (Presión ~500, Caudal ~10000)
UMBRAL_PRESION = 400.0  
UMBRAL_CAUDAL = 9000.0  

def delivery_report(err, msg):
    """Callback de confirmación de entrega en Redpanda."""
    if err is not None:
        print(f"[Detector] Error enviando alerta: {err}")
    else:
        print(f"[Detector] ALERTA PUBLICADA en Redpanda (topic: {msg.topic()}) ")

def evaluate_anomaly():
    """Evalúa si existe una caída anómala sostenida más diferencia de balance[cite: 1]."""
    if len(ventana_lecturas) == 3:
        # Verificar si las 3 lecturas están por debajo del umbral normal
        caida_presion = all(lec['presion_psi'] < UMBRAL_PRESION for lec in ventana_lecturas)
        descuadre_caudal = all(lec['caudal_bpd'] < UMBRAL_CAUDAL for lec in ventana_lecturas)

        if caida_presion and descuadre_caudal:
            print("\n[!] Regla de negocio cumplida: Posible válvula ilícita o fuga detectada.")
            publish_alert(ventana_lecturas[-1])
            ventana_lecturas.clear() # Limpiar ventana para evitar avalancha de alertas

def publish_alert(ultima_lectura):
    """Estructura y publica la alerta en formato CloudEvents."""
    alerta_event = {
        "specversion": "1.0",
        "type": "alerta.seguridad.valvula_ilicita",
        "source": "/petroandes/it/detector",
        "id": str(uuid.uuid4()),
        "datacontenttype": "application/json",
        "data": {
            "nivel_riesgo": "CRITICO",
            "tramo": ultima_lectura['tramo'],
            "descripcion": "Caída anómala de presión sostenida y descuadre de caudal detectado en ventana horaria.",
            "presion_actual_psi": ultima_lectura['presion_psi'],
            "caudal_actual_bpd": ultima_lectura['caudal_bpd']
        }
    }
    
    producer.produce(
        topic=topic_salida,
        value=json.dumps(alerta_event).encode('utf-8'),
        callback=delivery_report
    )
    producer.poll(0)

# 3. Ciclo principal de consumo
consumer.subscribe([topic_entrada])
print(f"Detector de anomalías iniciado. Escuchando tópico: '{topic_entrada}'...")

try:
    while True:
        msg = consumer.poll(1.0) # Esperar hasta 1 segundo por nuevos mensajes
        if msg is None:
            continue
        if msg.error():
            print(f"Error en consumidor: {msg.error()}")
            continue

        # Extraer el CloudEvent y los datos operativos
        payload_str = msg.value().decode('utf-8')
        cloud_event = json.loads(payload_str)
        datos_operativos = cloud_event.get("data", {})

        print(f"Analizando métricas -> Presión: {datos_operativos.get('presion_psi')} psi | Caudal: {datos_operativos.get('caudal_bpd')} bpd")
        
        # Almacenar en la ventana móvil y evaluar
        ventana_lecturas.append(datos_operativos)
        evaluate_anomaly()

except KeyboardInterrupt:
    print("\nDeteniendo detector...")
finally:
    consumer.close()
    producer.flush()