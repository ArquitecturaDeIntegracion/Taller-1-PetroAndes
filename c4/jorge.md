
Nivel 1: Contexto del Sistema

```mermaid
C4Context
  title PetroAndes S.A. - Capa de Integración de Telemetría (AndesTransporte)
  
  Person(analista, "Analista de Conciliación de Pérdidas", "Monitorea el balance volumétrico diario, investiga discrepancias e inicia reclamaciones por hurtos.")
  Person(operador_ot, "Operador de Centro de Control OT", "Supervisa presiones y caudales en tiempo real a lo largo de los 9,000 km de ductos.")
  
  System_Ext(scada, "Sistema SCADA & AVEVA PI (OT - Nivel 3)", "Sistemas de supervisión industrial e historiadores de señales físicas en estaciones y tramos.")
  
  System(telemetry_layer, "Capa de Integración de Telemetría y Alertas (CITA)", "Arquitectura orientada a eventos para captura, normalización y detección temprana de anomalías en ductos.")
  
  System_Ext(snbv, "Sistema de Nominaciones y Balance Volumétrico (IT - Nivel 4)", "Plataforma que administra solicitudes de capacidad, programas de bombeo y balances mensuales de transporte.")
  System_Ext(sap, "ERP SAP IS-Oil (IT - Nivel 4)", "Sistema transaccional para la contabilidad de hidrocarburos (HPM) y conciliaciones financieras.")
  
  Rel(scada, telemetry_layer, "Publica eventos de telemetría normalizada", "MQTT / TLS (Nivel 3.5 IDMZ)")
  Rel(telemetry_layer, snbv, "Envía alertas tempranas de desbalance y caídas de presión", "HTTPS / REST / OpenAPI")
  Rel(telemetry_layer, sap, "Registra traza de pérdidas anómalas verificadas", "Kafka API / Eventos")
  Rel(analista, snbv, "Concilia balances volumétricos", "Web Interface")
  Rel(operador_ot, scada, "Opera válvulas y monitorea presiones", "HMI / SCADA")


```

Nivel 2: Contenedores


```mermaid
C4Container
  title PetroAndes S.A. - AndesTransporte - Capa de Integración de Telemetría (CITA) - Nivel 2: Contenedores
  
  Person(operador, "Operador de Centro de Control (OT)", "Supervisa caudales, presiones y alarmas operativas en tiempo real.")
  Person(analista, "Analista de Conciliación de Pérdidas (IT)", "Investiga discrepancias de balance volumétrico diario e inicia reclamaciones.")

  System_Ext(snbv, "Sistema de Nominaciones y Balance (SNBVT)", "Sistema de Nivel 4 que liquida mensualmente balances y gestiona nominaciones.")

  Boundary(lvl3, "Nivel 3 - Red de Operaciones de AndesTransporte (OT)") {
    Container(sensors, "Concentrador de Telemetría de Campo", "SCADA RTU / PLC", "Captura señales físicas de sensores de presión y caudal a lo largo de los 9,000 km de ductos.")
    ContainerDb(mosquitto, "Gateway de Eventos de Planta (Eclipse Mosquitto)", "MQTT Broker (QoS 1)", "Centraliza localmente ráfagas de telemetría de campo de alta frecuencia antes de su envío corporativo.")
  }

  Boundary(lvl3_5, "Nivel 3.5 - DMZ Industrial (IDMZ)") {
    Container(bridge, "Puente de Integración Industrial (OT-IT Bridge)", "Python / Go Service", "Consume telemetría MQTT, valida esquemas, normaliza el envelope al estándar CloudEvents y publica hacia IT.")
  }

  Boundary(lvl4, "Nivel 4 - Red Corporativa de PetroAndes (IT / Nube)") {
    ContainerDb(redpanda, "Event Broker Corporativo (Redpanda)", "Kafka-API Engine", "Bus de eventos distribuido e inmutable. Almacena en disco tópicos de telemetría histórica y alertas de anomalías.")
    Container(registry, "Registro de Esquemas (Schema Registry)", "Redpanda Registry", "Gobierna y versiona los contratos de datos de la corporación para garantizar compatibilidad backward/forward.")
    Container(detector, "Motor de Detección de Anomalías", "Python / Go (Stateless Window)", "Analiza series de tiempo de presión y caudal en ventanas horarias móviles para detectar caídas de presión y fugas.")
    
    Boundary(business_app, "Capa de Negocio y Conciliación") {
      Container(router, "Enrutador de Mensajería de Negocio", "Apache Camel / Apache NiFi", "Implementa patrones EIP (como Message Translator y Content-Based Router) para consumir alertas y enviarlas a la API.")
      Container(volumetric_api, "API del Sistema de Control de Pérdidas", "Python / Java / Node.js", "Expone servicios REST (OpenAPI) para el control operativo de desbalances y registro de incidentes de hurto.")
    }
  }

  %% Flujos de Datos e Interfaces de Red (Conductos IEC 62443)
  Rel(sensors, mosquitto, "Publica telemetría bruta de sensores", "MQTT (QoS 1) / TLS (Interno OT)")
  Rel(bridge, mosquitto, "Subscribe a tópicos de telemetría (Pull)", "MQTT (QoS 1) / TLS (Entrada IDMZ)")
  Rel(bridge, registry, "Consulta / Registra esquemas de eventos", "HTTPS / JSON (Salida IDMZ)")
  Rel(bridge, redpanda, "Publica CloudEvents normalizados (Push)", "Kafka API / TLS / TCP:9092 (Salida IDMZ)")
  
  Rel(detector, redpanda, "Consume eventos de telemetría de ductos", "Kafka API / TCP")
  Rel(detector, redpanda, "Publica alertas de pérdida/fuga", "Kafka API / TCP")
  
  Rel(router, redpanda, "Consume alertas de anomalías (EIP)", "Kafka API / TCP")
  Rel(router, volumetric_api, "Registra alerta en el sistema (POST /alertas)", "HTTPS / REST / JSON")
  
  Rel(operador, mosquitto, "Monitorea variables de campo", "HMI / SCADA")
  Rel(analista, volumetric_api, "Visualiza estado de tramos y auditoría de pérdidas", "HTTPS / Web UI")
  Rel(volumetric_api, snbv, "Sincroniza estados de balance consolidados", "HTTPS / REST")


```

