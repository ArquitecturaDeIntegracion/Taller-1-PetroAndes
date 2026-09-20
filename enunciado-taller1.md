# Taller 1 — Integración OT/IT dirigida por eventos en PetroAndes

## Nombre de grupo

Group 1

## Instrucciones

### Objetivos

- Diseñar una arquitectura de integración dirigida por eventos (EDA) que conecte la telemetría OT de pozos y ductos con los sistemas IT, respetando la convergencia IT/OT (Modelo Purdue, ISA-95, DMZ industrial, IEC 62443).
- Especificar contratos de eventos con AsyncAPI y CloudEvents, con esquemas gobernados en un schema registry.
- Implementar un prototipo funcional con tecnologías gratuitas y de código abierto, y sustentarlo ante un comité / monitor del curso.

### Contexto (escenario del caso)

AndesTransporte necesita detectar en tiempo casi real anomalías de presión y caudal en un tramo de oleoducto —posibles válvulas ilícitas o fugas— integrando la telemetría de campo con el sistema de balance volumétrico. Hoy la detección es tardía: las señales existen en el SCADA y en los historiadores, pero la correlación entre una caída anómala de presión y un descuadre del balance del tramo solo se descubre semanas después, durante la conciliación manual. El grupo asumirá el rol del equipo de arquitectura que diseña e implementa el prototipo de la nueva capa de integración de telemetría.

### Actividades de análisis y diseño

- Diagrama C4 de la solución de integración (niveles de contexto y de contenedores).
- Mapeo de la solución sobre el Modelo Purdue, con identificación explícita de la DMZ industrial (nivel 3.5) y de los conductos IEC 62443 (qué cruza la frontera, en qué dirección y por qué).
- Selección justificada de patrones (EDA, event mesh, CloudEvents como envelope, transactional outbox para publicación confiable, patrones EIP del flujo) documentada mediante al menos cuatro ADRs (Architecture Decision Records) con alternativas descartadas.
- Contrato de eventos con AsyncAPI 3.0 (canales de telemetría y de alertas) y esquema del payload registrado en un schema registry, con la regla de compatibilidad elegida y justificada.

### Parte práctica de implementación (hands-on)

- **Infraestructura:** archivo Docker Compose que levante Redpanda (o Apache Kafka) como broker de eventos, con su consola de administración y schema registry.
- **Simulación OT:** un broker MQTT (Eclipse Mosquitto) que simule la telemetría de sensores de pozos y ductos (presión, caudal, temperatura), alimentado por un generador de datos sintéticos (el grupo puede inyectar anomalías).
- **Puente OT→IT:** un componente que consuma del broker MQTT, normalice los mensajes al formato CloudEvents y los publique en un topic de Redpanda con esquema registrado; este puente representa el paso por la DMZ industrial.
- **Detección:** un consumidor que aplique una regla de detección de anomalías (por ejemplo: caída anómala de presión sostenida más diferencia de balance por ventana horaria superior al umbral → alerta de posible válvula ilícita) y publique la alerta en el canal correspondiente.
- **Integración con el negocio:** un flujo de integración con Apache Camel o Apache NiFi (o un iPaaS con tier gratuito) que enrute la alerta hacia un sistema simulado de balance volumétrico, y una API REST documentada con OpenAPI que exponga el estado consolidado del tramo.

### Entregables

- Repositorio con el `docker-compose.yml`, el código del puente y del consumidor, y las instrucciones de ejecución reproducibles (`README`).
- Especificación AsyncAPI validada (sin errores) y esquemas registrados.
- ADRs (mínimo cuatro) y diagramas C4.
- Demostración en vivo del sistema implementado y detección de una anomalía inyectada, de extremo a extremo.

### Rúbrica de evaluación

| Criterio | Peso |
| --- | --- |
| Diseño arquitectónico y calidad de los ADRs | 30% |
| Contrato AsyncAPI/CloudEvents y gobierno del esquema | 15% |
| Implementación funcional (broker, MQTT, puente, flujo, detección) | 35% |
| Calidad del análisis IT/OT (Purdue, DMZ, IEC 62443) | 10% |
| Sustentación | 10% |

### Sustentación

- Defensa virtual y extra clase (~20 minutos: 15 de demostración y 5 de preguntas). Se debe conectar al menos un integrante del grupo.
- Preguntas típicas: justificación de la clave de partición y de la semántica de entrega; comportamiento ante la caída de un consumidor; ubicación de la DMZ en el diseño; identificación de los patrones EIP utilizados por su nombre canónico; trade-offs de latencia frente a confiabilidad y acoplamiento.
