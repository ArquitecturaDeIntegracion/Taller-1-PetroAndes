
Nivel 1: Contexto del Sistema

```mermaid
C4Context
  title PetroAndes OT/IT Integration - Nivel 1: Contexto
  
  Person(operador, "Operador de AndesTransporte", "Supervisa el estado de los tramos y actúa ante alertas de pérdidas.")
  Person(monitor, "Monitor Académico / Comité", "Evalúa el prototipo funcional, la inyección de anomalías y los escenarios de calidad [3, 4].")
  
  System_Ext(sensors, "Sensores de Campo y Simulador (OT)", "Genera y simula señales de telemetría (presión, caudal, temperatura) de pozos y ductos [5].")
  
  System(telemetry_integration, "Solución de Integración (Taller 1)", "Capa de integración dirigida por eventos (EDA) que captura, normaliza, detecta anomalías y enruta alertas [3, 6].")
  
  System_Ext(volumetric, "Sistema de Balance Volumétrico (IT)", "Sistema corporativo simulado que consolida el estado del tramo y recibe alertas de posibles válvulas ilícitas [3, 7].")
  
  Rel(sensors, telemetry_integration, "Publica eventos de telemetría bruta", "MQTT")
  Rel(telemetry_integration, volumetric, "Envía alertas de anomalías (posibles válvulas ilícitas)", "REST/OpenAPI")
  Rel(operador, volumetric, "Consulta el estado consolidado de los tramos", "Web/API")
  Rel(monitor, telemetry_integration, "Monitorea comportamiento del sistema y tópicos en vivo [4]", "Redpanda Console")
```

Nivel 2: Contenedores


```mermaid
C4Container
  title PetroAndes OT/IT Integration - Nivel 2: Contenedores

  Person(operador, "Operador de AndesTransporte", "Supervisa el tramo y las alertas.")
  Person(monitor, "Monitor Académico", "Evalúa el prototipo en vivo [3, 4].")

  Boundary(ot_zone, "Nivel 3 - Zona de Operaciones (OT)") {
    Container(sensors, "Generador de Datos Sintéticos", "Python / Go / JS", "Simula las señales físicas de presión y caudal del oleoducto e inyecta anomalías [5].")
    ContainerDb(mosquitto, "Broker MQTT (Eclipse Mosquitto)", "Message Broker", "Recibe telemetría bruta de alta frecuencia desde el campo [5].")
  }

  Boundary(idmz, "Nivel 3.5 - DMZ Industrial (IDMZ)") {
    Container(bridge, "Puente OT-IT (Edge Node)", "Python / Go / Java", "Consume de MQTT, normaliza el envelope a CloudEvents y publica en Redpanda [5].")
  }

  Boundary(it_zone, "Nivel 4 - Zona Corporativa (IT)") {
    ContainerDb(redpanda, "Redpanda (Event Broker)", "Event Streaming Platform", "Log de eventos distribuido con topics de telemetría y alertas [2].")
    Container(registry, "Schema Registry", "Redpanda Registry", "Gobierna y valida los contratos de datos en formato JSON/Avro [2, 7].")
    Container(detector, "Detector de Anomalías", "Python / Go / Java", "Analiza ventanas horarias para detectar caídas de presión o descuadres de balance y emite alertas [7].")
    
    Boundary(business_app, "Aplicación de Negocio Simulado") {
      Container(router, "Enrutador de Negocio", "Apache Camel / NiFi", "Consume alertas de Redpanda (EIP) y las enruta a la API [7].")
      Container(volumetric_api, "API de Balance Volumétrico", "Python / Java / Node.js", "Expone endpoints REST documentados con OpenAPI para registrar alertas y estados [7].")
    }
  }

  %% Flujos de Datos
  Rel(sensors, mosquitto, "Publica telemetría bruta", "MQTT (QoS 1)")
  Rel(bridge, mosquitto, "Consume datos de sensores (Pull)", "MQTT (QoS 1)")
  Rel(bridge, registry, "Valida/Registra esquema", "HTTP")
  Rel(bridge, redpanda, "Publica CloudEvents validados (Push)", "Kafka API")
  
  Rel(detector, redpanda, "Consume telemetría de ductos", "Kafka API")
  Rel(detector, redpanda, "Publica alerta de anomalía", "Kafka API")
  
  Rel(router, redpanda, "Consume alertas de anomalías (EIP)", "Kafka API")
  Rel(router, volumetric_api, "Enruta alerta (POST /alert)", "REST / JSON")
  
  Rel(operador, volumetric_api, "Consulta estado del tramo", "HTTP / OpenAPI")
  Rel(monitor, redpanda, "Monitorea tópicos en vivo [4]", "Redpanda Console")


```

