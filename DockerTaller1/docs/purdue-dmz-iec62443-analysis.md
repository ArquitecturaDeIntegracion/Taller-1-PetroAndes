# Análisis IT/OT: Modelo Purdue, DMZ, IEC 62443
## Solución de Integracion de Telemetría OT/IT para AndesTransporte - PetroAndes S.A.

**Autores:** [Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio]
**Curso:** ARTI 4212 - Arquitectura de Integración
**Universidad:** Universidad de los Andes
**Última Fecha Modificación:** Septiembre 5 de 2026
**Proyecto:** Taller 1 - Integración OT/IT Dirigida por Eventos en PetroAndes

---

## Resumen

El presente documento tiene como propósito analizar cómo la solución de detección de anomalías en ductos de AndesTransporte (filial de PetroAndes S.A.) implementa principios de:

1. **Modelo Purdue** - Separación jerárquica de 5 niveles de sistemas.
2. **DMZ Industrial (nivel 3.5)** - Frontera controlada entre OT e IT.
3. **IEC 62443** - Estándar global de ciberseguridad industrial a mediante zonas y ductos.

La presente solución resuelve un problema crítico de negocio identificado en el caso de PetroAndes: **"La detección tardía de anomalías en ductos (válvulas ilícitas, fugas) que tarda semanas en sistemas manuales, retrasando la acción operativa."**

---

## 1. Modelo Purdue

### 1.1 ¿Qué es el modelo Purdue?

El **Modelo de Refinerías Purdue** es un marco arquitectónico desarrollado en los años 1990 por la Universidad Purdue en colaboración con el Industry-Purdue University Consortium for Computer Integrated Manufacturing.

**Definición oficial (NIST SP 800-82 Rev. 3, Septiembre 2023)**

El modelo Purdue es una arquitectura jerárquica que organiza los sistemas de una instalación industrial en **niveles claramente diferenciados**, separando la **instrumentación y control físico (OT)** de los **sistemas de gestión y corporativos (IT)**, con el objetivo de limitar el alcance de incidentes de seguridad y proteger aquello que es verdaderamente crítico para la operación.

**Propósito central**

Según la Universidad Purdue y reafirmado por NIST, el modelo responde a una realidad operativa específica: **en tecnología operativa (OT), la disponibilidad es la prioridad máxima**. Si un servidor corporativo falla, el impacto es económico. Si falla un sistema de control de una planta industrial, el impacto puede ser:
- Parada de planta (Pérdidas millonarias)
- Riesgos físicos a personal
- Daño ambiental

El modelo Purdue establece **límites de confianza claros** entre OT e IT para garantizar que errores, ataques o cambios en IT causen paradas operacionales en OT.

### 1.2 Los 5 niveles jerárquicos del modelo Purdue

| Nivel | Nombre | Descripción | Ejemplos en PetroAndes | Latencia | Criticidad |
|-------|-------|-------|-------|-------|-------|
| **0** | Field Instrumentation | Sensores, transmisores, actuadores físicos en el campo | Tags SCADA de presión (PRES_001), caudal (FLOW_002), válvulas | Milisegundos | Crítica |
| **1** | Basic Process Control | PLCs, DCS que ejecutan lazos cerrados de control automático | SCADA de campos, SCADA de ductos, RTUs | Milisegundos a segundos | Crítica |
| **2** | Area Supervisión & Batch | Historiadores, HMIs, sistemas de supervisión local de áreas | Historiador AVEVA PI (1 por refinería, 1 por campo), alarmas, trending | Segundos a minutos | Alta |
| **3** | Operations Management | MES, planificación, análisis operativo (aún en el piso de la planta) | Sistema de nominaciones de transporte, MES de refinerías, historiador coporativo | Minutos a horas | Media |
| **4** | Corporate planning | ERP, finanzas, decisiones de negocio | SAP HPM, ETRM trading, decisiones de portafolio | Horas a días | Media-Baja |
| **5** | External Networks | Conexiones a internet, organismos reguladores, terceros | Reportes a ANH, comunicación con remitentes terceros | Variable | Baja |

### 1.3 Flujos de Información entre niveles

**Flujo descendente (Órdenes, Setpoints):**
```
Nivel 4 (SAP HPM): "Transportar 1.119 kbd esta semana"
    ↓ (Orden de transporte)
Nivel 3 (Sistema de nominaciones): "Station A-B: 450 bpd, Station B-C: 420 bpd"
    ↓ (Programa detallado)
Nivel 2 (Historiador): "Manten presión entre 400 y 510 PSI en Tramo-Centro"
    ↓ (Setpoint)
Nivel 1 (SCADA): "Si presión < 400, alarma crítica"
    ↓ (Lógica)
Nivel 0 (Válvula motorizada): Se abre/cierra automáticamente
```

**Flujo ascendente (Datos, Alertas):**

```
Nivel 0: "Sensor mide 505 PSI"
    ↑ (Lectura RAW)
Nivel 1: "SCADA confirma lectura, sin alarma"
    ↑ (Señal procesada)
Nivel 2: "Historiador almacena última hora, caudal bajó 0.5%"
    ↑ (Datos resumidos, 5 min de rezago)
Nivel 3: "Sistema de balance calcula: pérdidas normales (evaporación), sin anomalías"
    ↑ (KPI Operativo)
Nivel 4 (SAP): "Dashboard: Tramo-Centro al 100% de capacidad, en presupuesto"
    ↑ (Métrica de negocio, días de rezago)
```

**La realidad de PetroAndes antes de la solución**

Según el caso de estudio **"la detección de anomalías en ductos era completamente manual"**

"Las señales de presión y caudal existen en los SCADA y en los historiadores, pero la correlación entre una caida anómala de presión y un descuadre del balance del tramo solo se descubre **"semanas después"**, cuando los analistas concilian manualmente las planillas de medición con los reportes del sistema de nomincaciones y con SAP."

Esto quiere decir, que **el flujo ascendente de datos no era en tiempo real**. Las anomalías que sucedían en Nivel 0-1 no eran visibles en Nivel 3 sino hasta 2-3 semanas después (manual, con rezago).

---

## 2. DMZ Industrial (Nivel 3.5) - La frontera Controlada

### 2.1 Definición y Ubicación

La **DMZ Industrial (Demilitarized Zone, Nivel 3.5)** es una **frontera de seguridad controlada** entre las redes de tecnología operativa (OT, Niveles 0-2) y los sistemas de tecnología operativa (IT, Niveles 4-5).

**Por qué existe:**

De acuerdo con NIST SP 800-82r3 y la arquitectura de defensa en profundidad (Defense in Depth), la DMZ Industrial existe porque: 

1. **OT requiere aislamiento físico** - Los sistemas de control deben estar protegidos de cambios no autorizados desde sistemas corporativos.
2. **IT requiere acceso a datos OT** - Para análisis, cumplimiento regulatorio, y toma de decisiones
3. **Necesidad de controlador único** - Un solo punto donde se valida, normaliza y autoriza qué datos cruzan.

**En términos de modelo Purdue**

```
______________________________________________________
| Nivel 5 (External, Enterprise Networks)            |
| - Conexiones a internet, ANH, reguladores          |
|____________________________________________________|
                        ↑↓
__________________________________________________________
| Nivel 4 (Corporate Planning & IT Systems)              |
| - SAP ERP, ETRM, Business Intelligence                 |
| - Características: Cloud-ready, cambios frecuentes, TI |
|________________________________________________________|
                        ↑↓
                ___________________
                | Nivel 3.5       |
                | DMZ Industrial  |  -> Frontera controlada
                | - Validación    |
                | - Nomralización |
                | - Autorización  |
                |_________________|
                        ↑↓
____________________________________________________________
| Nivel 3 (Operations Management & Supervisory)            |
| - Historiadores, MES, Sistemas de nominaciones           |
| - Características: Disponibilidad crítica, baja latencia |
|__________________________________________________________|
                        ↑↓
______________________________________________________________
| Nivel 2-1 (Basic Process Control)                          |
| - SCADA, DCS, PLCs, lógica de control en tiempo real       |
| - Características: Latencia milisegundos, seguridad física |
|____________________________________________________________|
                        ↑↓
______________________________________________________________
| Nivel 0 (Field Instrumentation)                            |
| - Sensores, actuadores, transmisores en campo              |
|____________________________________________________________|
```

### 2.2 Implementación de la DMZ Industrial en la solución de PetroAndes

En la solución implementada en el presente taller, **la DMZ industrial se matrializa como:**

#### Componente: Puente DMZ (`puente-dmz-python/puente.py`)

```
__________________________________________________________________________
| RED OT (ot-network)                                                    |
|  ______________________                                                |
|  | MQTT Broker        |                                                |
|  | (Mosquitto)        |                                                |
|  |____________________|                                                |
|            ↓  MQTT (Protocolo simple, sin TLS en demo)                 |
|  ___________________________________________________________________   |
|  |  Puente DMZ (puente.py)                                          |  |
|  |                                                                  |  |
|  |  1. Consume MQTT (on_message callback)                           |  |
|  |     Recibe: {tramo, presion_psi, caudal_bpd, timestamp}          |  |
|  |                                                                  |  |
|  |  2. Valida esquema (campos obligatorios)                         |  |
|  |     if not all([msg.tramo, msg.presion_psi, ...]):               |  |
|  |         reject()                                                 |  |
|  |                                                                  |  |
|  |  3. Normaliza a CloudEvents (CNCF Standard)                      |  |
|  |     Añade: specversion="1.0"                                     |  |
|  |             type="telemetria.ducto"                              |  |
|  |             source="ot-ducto-0"                                  |  |
|  |             datacontenttype="application/json"                   |  |
|  |             timestamp (RFC 3339)                                 |  |
|  |                                                                  |  |
|  |  4. Publica a Redpanda (tópico: it-telemetria-topic)             |  |
|  |     Garantía: at-least-once delivery                             |  |
|  |__________________________________________________________________|  |
|________________________________________________________________________|
                                    ↓   (Frontera: MQTT -> CloudEvents)
__________________________________________________________________________
| RED IT (it-network)                                                    |
|   ___________________                                                  |
|   | Redpanda        |   puerto 9092 (kafka API)                        |
|   | (Event Broker)  |   tópicos: it-telemetria-topic                   |
|   |_________________|              it-alertas-topic                    |
|            ↓  Kafka (protocolo seguro con ACLs)                        |
|   ____________________       _____________________                     |
|   | Detector de      |       | API Rest          |                     |
|   | anomalías        |       | (Sistema-balance) |                     |
|   | (consume,        | ----> |                   |                     |
|   |  procesa,        |       | POST /alertas     |                     |
|   |  publica alerta) |       | GET /estado       |                     |
|   |__________________|       |___________________|                     |
|                                                                        |
|                (Solo lectura - OT no escribe)                          |
|________________________________________________________________________|
```

**Funciones clave del puente DMZ (alineadas con IEC 62443)**
| Función | Implementación | Propósito |
|---------|----------------|-----------|
| **Validación de entrada** | `puente.py`: valida campos | rechazar datos malformados |
| **Normalizaión** | CloudEvents | Formato estándar CNCF |
| **Encapsulación** | Metadata + data | Trazabilidad y auditoría |
| **Unidireccionalidad** | MQTT -> Kafka, no retorno | Prevenir escritura IT -> OT |
| **Garantía de entrega** | kafka at-least-once | No perder telemetría |
| **Logging** | Cada transición registrada | Auditoría de acceso |

### 2.3 ¿Qué cruza la DMZ? (flujos específicos)

#### Conducto 1: OT -> DMZ -> IT (Entrada de Telemetría)

**Origen:** Simulador de sensores (simulador-ot.py)
**Destino:** Red IT (Redpanda, Detector, API Rest)
**Datos:** Lecturas de presión, caudal, temperatura en ductos
**Protocolo:** MQTT (OT) -> CloudEvents (DMZ) -> Kafka (IT)
**Dirección:** Unidireccional (OT -> IT)
**Autoridad de control:** Puente DMZ

#### Conducto 2: IT -> OT (Retorno de Comandos)

**No existe:**

**Política arquitectónica:** Conforme al modelo Purdue, **ningun sistema de Nivel 3 o superior, describe en nivel 2 o inferior**

**Justificación:**

Según NIST SP 800-82r3, "Restricting OT user privileges and implementing automated controls trat prevent unauthorized commands from IT systems to OT systems is essential for maintaining safety and preventing unintended consequences from compromised IT systems."

---

## 3. IEC 62443 - Ciberseguridad Industrial mediante zonas y conductos

### 3.1 Estándar ISA/IEC 62443

**IEC 62443** es el estándar global líder en ciberseguridadpara sistemas de automatización y control industrial, desarrollado conjuntamente por:
- **ISA (International Society of Automation)**
- **IEC (International Electrotechnical Comission)**

**Definición Oficial (IEC 62443-1-1 Models and Concepts):**

IEC 62443 define una arquitectura de zonas y conductos que segmenta los sistemas industriales en regiones lógicas con requisitos de seguridad comunes, e implementa defensa en profundidad mediante 4 niveles de seguridad en función del riesgo del negocio.

**Concepto Central: ZONAS + CONDUCTOS**

- **Zona:** Agrupación de dispositivos, sistemas y aplicaciones con **requisitos de seguridad comunes**
- **Conducto:** Agrupación de canales de comunicación que **conectan dos o más zonas**, compartiendo reglas de tráfico específicas.

### 3.2 Zonas de Seguridad en la Solución de PetroAndes

#### Zona 1: OT Local (Nivel 0-2)

**Componentes:**
- Simulador de sensores (simulador-ot.py)
- MQTT Broker (Mosquitto) en el puerto 1883
- Red Docker: `ot-network`

**Caracteristicas de Seguridad:**
- Aislamiento físico (red Docker separada)
- Acceso anónimo (demo; en prod: credenciales requeridas)
- Protocolo: MQTT (publish/subscribe sin TLS en demo)
- Criticidad: **ALTA** (control de procesos en tiempo real)

**Nivel de Seguridad (IEC 62443):** SL2 (Proteccón contra uso indebido intencionado mediante medios sencillos)

#### Zona 2: DMZ Industrial (Nivel 3.5)

**Componentes:**
- Puente DMZ (puente.py)
- Red Docker: `dmz-network`

**Características de seguridad:**
- Validación de esquema (rechaza mensajes malformados)
- Normalización obligatoria (CloudEvents)
- Unidireccional (OT entrada, IT salida, no retorno)
- Logging de toda transición
- Control de acceso implícito (solo tráfico autorizado por Puente)

**Nivel de Seguridad (IEC 62443):** SL3 (Protección contra ataques sofisticados con recursos moderados)

#### Zona 3: IT Corporativo (Nivel 3-4)

**Componentes:**
- Redpanda (Event Broker) puerto 9092
- Detector de anomalías
- Enrutador de alertas
- API REST (sistema-balance) pueto 8000
- Redpanda Console (BI) puerto 8082
- Red Docker: `it-network`

**Características de seguridad:**
- Aislamiento de red (no conecta directo a OT)
- Acceso solo a través de DMZ
- Esquemas validados por Schema Registry (en prod: RBAC)
- ACLs en Redpanda (en demo: permisivo; en prod: RBAC)
- Criticidad: **MEDIA-BAJA** (análisis, decisiones, no control)

**Nivel de Seguridad (IEC 62443):** SL2 (Suficiente para análisis; SL3+ si hay escritura a OT)

### 3.3 Conductos de Seguridad

Un conducto es un **camino específico entre zonas donde datos cruzan reglas explícitas de tráfico.**

#### Conducto A: OT -> IT (Telemetría)

```
Zona OT              Conducto A              Zona IT
________________     (Validado)          ________________
| Sensor OT    |----------MQTT---------->| Puente DMZ   |
| (MQTT: 1883) |     1. Recibe           | 1. Valida    |
|              |     2. Normaliza        | 2. Normaliza |
|______________|     3. Publica          | 3. Publica   |
                        (Kafka)          |______________|
                                                |
                                                |
                                                |
                                                ▼
                                         ___________________
                                         | Redpanda        |
                                         | (Topis: it-...) |
                                         |                 |
                                         | Detector,       |
                                         | API REST        |
                                         |_________________|
```

**Reglas del Conducto OT -> IT:**

| Regla | Implementación |
|-------|----------------|
| **Permitido:** Leer datos MQTT | `puente.py` linea 30: `on_message(client, userdata, msg)` |
| **Permitido:** Validar esquema | Linea 35-37: campos obligatorios |
| **Permitido:** Enriquecer con metadata | CloudEvents: specversion, type, source, timestamp |
| **No permitido:** Escribir de vuelta a MQTT | Codigo no lo hace; política ISA-95 |
| **No permitido:** Pasar datos sin normalizar | Todo pasa por CloudEvents antes de Kafka |
| **Auditado:** Registrar tránsito | Logs de puente (Docker logs) |

**Garantías de confiabilidad:**

- **At-least-once delivery:** Si el puente falla, los mensajes se reintentan.
- **No duplicación de datos:** Schema Registy al ser implementado, evita duplicados.
- **Trazabilidad:** Cada mensaje tiene `timestamp` y `source` en CloudEvents.

#### Conducto B: IT -> OT (Retorno de Comandos)

```
Zona IT              Conducto B          Zona IT
________________     (Vacío)        ________________
| API REST     |-------------------X| MQTT         |
|              |  (No hay retorno)  | (No recibe   |
| Retorno      |                    | comandos)    |
|______________|                    |              |
                                    |______________|
```

Política cumplida: IT no escribe en OT.

**Reglas del conducto IT -> OT:**

| Regla | Implementación |
|-------|----------------|
| **No permitido:** Escribir a MQTT | Código IT no lo hace |
| **No permitido:** Cambiar a setpoints SCADA | No existe endpoint para ello |
| **No permitido:** Comandar válvulas | API REST es solo lectura y estadísticas |
| **Permitido:** Notificar al operador | API devuelve alertas que operador ve manualmente |

**Justificación (IEC 62443):**

Según el estándar, esta unidireccionalidad es defensa en profundidad. Que IT esté comprometido no debe afectar control OT. Si se necesita actuar:

```
Escenario: Detectar válvula ilícita -> actuar
|-> Detector pública alerta en it-alertas-topic
|-> API REST muestra alerta en dashboard
|-> Operador humano revisa y aprueba la acción
|-> Operador ejecuta cierre manual en SCADA (o orden verbal a campo)
    |-> No es automático desde IT
```

### 3.4 Niveles de Seguridad IEC 62443 (SL 1-4)

IEC 62443 define **4 niveles de seguridad** basados en capacidad del atacante y recursos disponibles:

| Nivel | Nombre | Descripción | Ejemplos de Protección | Aplicable a PetroAndes |
|-------|--------|-------------|------------------------|------------------------|
| **SL1** | Protección básica | Defiende contra uso indebido involuntario | Cambios de contraseña regulares, logs básicos | No aplicable (infraestructura crítica) |
| **SL2** | Protección estándar | Defiende contra ataques simples (script kiddies, errores) | Firewalls, RBAC, auditoría básica, cambios de config | **Zona OT + DMZ (actual)** |
| **SL3** | Protección avanzada | Defiende contra ataques sofisticados (adversarios con recursos) | IDS/IPS, segmentación fina, Zero Trust, monitoreo continuo, hardening | **Zona IT (recomendado para ampliación)** |
| **SL4** | Protección máxima | Defiende contra ataques APT (Advanced Persistent Threats) con equipo especializado | Defensa en profundidad total, encriptación E2E, aislamiento air-grap, verificación formal | **No presente en demo; requerido en prod pars SIS (Safety Instrumented Systems)** |

**Evaluación de la solución actual:**

```
Zona OT:            SL2 OK (aislamiento básico, demo sin TLS)
Zona DMZ:           SL3 OK (validación + normalización)
Zona IT:            SL2 OK (aislamiento, pero sin IDS/IPS activos)
Conducto OT->IT     SL3 OK (validación + unidireccionalidad)
Conducto IT->OT     N/A OK (no existe por poíticas de seguridad)
```