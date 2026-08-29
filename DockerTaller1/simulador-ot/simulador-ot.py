import time
import json
import random
import threading
import os
import paho.mqtt.client as mqtt

broker = os.getenv("MQTT_BROKER", "localhost")
topic = "petroandes/ot/ducto/telemetria"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(broker, int(os.getenv("MQTT_PORT", "1883")), 60)
client.loop_start()

# Variables globales para controlar la inyección en tiempo real
inyectar_anomalia = False
anomalias_restantes = 0
inicio_simulacion = time.monotonic()
auto_anomalia_despues = float(os.getenv("AUTO_ANOMALY_AFTER_SECONDS", "0"))
lecturas_anomalas = int(os.getenv("ANOMALY_READINGS", "5"))


def iniciar_anomalia():
    global inyectar_anomalia, anomalias_restantes
    inyectar_anomalia = True
    anomalias_restantes = lecturas_anomalas

print("Iniciando simulación OT...")
print("-> Presiona Ctrl+C para apagar el simulador de forma definitiva.")

try:
    while True:
        if (auto_anomalia_despues > 0
            and not inyectar_anomalia
            and time.monotonic() - inicio_simulacion >= auto_anomalia_despues):
            print("\n[!] Inyección automática de anomalía activada...\n")
            iniciar_anomalia()
            auto_anomalia_despues = 0

        if inyectar_anomalia and anomalias_restantes > 0:
            # Simulación de válvula ilícita o hurto de hidrocarburos[cite: 1]
            payload = {
                "tramo": "Tramo-Centro",
                "presion_psi": round(random.uniform(300.0, 310.0), 2), # Caída anómala de presión[cite: 1]
                "caudal_bpd": round(random.uniform(8000, 8100), 2),    # Descuadre de caudal
                "timestamp": time.time()
            }
            client.publish(topic, json.dumps(payload))
            print(f" Publicado (ANOMALÍA): {payload}")
            
            anomalias_restantes -= 1
            if anomalias_restantes == 0:
                inyectar_anomalia = False
                print("\n[i] Fin de la anomalía. Retornando a la operación normal de PetroAndes...\n")
            
            time.sleep(1) # Cadencia más rápida durante la alerta
            
        else:
            # Operación normal
            payload = {
                "tramo": "Tramo-Centro",
                "presion_psi": round(random.uniform(500.0, 510.0), 2),
                "caudal_bpd": round(random.uniform(10000, 10050), 2),
                "timestamp": time.time()
            }
            client.publish(topic, json.dumps(payload))
            print(f" Publicado (Normal): {payload}")
            
            time.sleep(2) # Cadencia estándar

except KeyboardInterrupt:
    print("\nDeteniendo simulador OT de manera segura...")
finally:
    client.loop_stop()
    client.disconnect()