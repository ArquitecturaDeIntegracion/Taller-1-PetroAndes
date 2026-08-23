
Nivel 1: Contexto del Sistema

```mermaid
C4Context
  title PetroAndes S.A. - Capa de Integración de Telemetría (AndesTransporte)

  Person(analista, "Analista de Conciliación", "Monitorea balance e investiga discrepancias.")
  Person(operador_ot, "Operador de Centro de Control", "Supervisa presiones y caudales.")

  System_Ext(scada, "SCADA & AVEVA PI (OT)", "Supervisión industrial e historiadores.")
  
  System(telemetry_layer, "Capa de Integración de Telemetría (CITA)", "Arquitectura de eventos para captura y detección de anomalías.")
  
  System_Ext(snbv, "SNBV (IT)", "Administra capacidad y balances.")
  System_Ext(sap, "ERP SAP IS-Oil (IT)", "Contabilidad HPM y finanzas.")

  Rel_D(operador_ot, scada, "Opera y monitorea", "HMI")
  Rel_D(analista, snbv, "Concilia balances", "Web")
  
  Rel_R(scada, telemetry_layer, "Publica telemetría", "MQTT")
  Rel_D(telemetry_layer, snbv, "Envía alertas", "REST")
  Rel_D(telemetry_layer, sap, "Registra pérdidas", "Kafka")

```

Nivel 2: Contenedores


```mermaid
C4Container
  title PetroAndes S.A. - CITA - Nivel 2: Contenedores

  Person(operador, "Operador (OT)", "Supervisa caudales y presiones.")
  Person(analista, "Analista (IT)", "Investiga discrepancias y reclamaciones.")

  Boundary(lvl3, "Nivel 3 - Red Operaciones (OT)") {
    Container(sensors, "Concentrador Telemetría", "RTU/PLC", "Captura señales físicas.")
    ContainerDb(mosquitto, "Gateway Eventos", "Eclipse Mosquitto", "Centraliza telemetría de campo.")
  }

  Boundary(lvl3_5, "Nivel 3.5 - DMZ Industrial") {
    Container(bridge, "Puente Integración (Bridge)", "Python/Go", "Normaliza telemetría a CloudEvents.")
  }

  Boundary(lvl4, "Nivel 4 - Red Corporativa (IT/Nube)") {
    ContainerDb(redpanda, "Event Broker", "Redpanda", "Bus inmutable de eventos.")
    Container(registry, "Schema Registry", "Redpanda", "Gobierna contratos de datos.")
    Container(detector, "Motor Anomalías", "Python/Go", "Detecta caídas de presión.")
    
    Boundary(business_app, "Capa de Negocio") {
      Container(router, "Enrutador", "Camel/NiFi", "Aplica patrones EIP.")
      Container(volumetric_api, "API Control Pérdidas", "Python/Java/Node", "Expone servicios REST.")
    }
  }
  
  System_Ext(snbv, "SNBVT", "Liquida balances mensuales.")

  %% Data Flows
  Rel_D(operador, mosquitto, "Monitorea", "HMI")
  Rel_R(sensors, mosquitto, "Publica telemetría", "MQTT/TLS")
  
  Rel_D(mosquitto, bridge, "Subscribe tópicos", "MQTT/TLS")
  Rel_R(bridge, registry, "Consulta esquemas", "HTTPS")
  Rel_D(bridge, redpanda, "Publica CloudEvents", "Kafka API")

  Rel_D(redpanda, detector, "Consume eventos", "Kafka API")
  Rel_U(detector, redpanda, "Publica alertas", "Kafka API")

  Rel_D(redpanda, router, "Consume alertas", "Kafka API")
  Rel_R(router, volumetric_api, "Registra alerta", "HTTPS")
  
  Rel_D(volumetric_api, snbv, "Sincroniza estados", "HTTPS")
  Rel_D(analista, volumetric_api, "Visualiza auditoría", "HTTPS")


```

