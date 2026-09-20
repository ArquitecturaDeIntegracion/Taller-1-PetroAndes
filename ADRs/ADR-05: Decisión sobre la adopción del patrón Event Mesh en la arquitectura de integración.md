# ADR-05: Decisión sobre la adopción del patrón Event Mesh en la arquitectura de integración

**Metadatos**
* **Código:** CITA-ADR-005
* **Fecha:** 2026-09-20
* **Título:** Adopción diferida del patrón Event Mesh
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
El enunciado del taller exige justificar la selección de patrones de integración, incluyendo Event Mesh. La solución actual conecta la telemetría OT con los consumidores IT mediante un broker MQTT en OT, un puente en la IDMZ y un único backbone de eventos en Redpanda/Kafka para la red IT. Se requiere decidir si el prototipo implementa formalmente un Event Mesh o si, por alcance y topología, corresponde clasificarlo como una arquitectura EDA con backbone centralizado.

## 2. Decisión de Arquitectura
Se evalúa el patrón Event Mesh, pero no se adopta en esta iteración del prototipo. Para el Taller 1, PetroAndes estandariza una arquitectura EDA con backbone centralizado de eventos sobre Redpanda/Kafka en la red IT, alimentado por un puente OT→IT ubicado en la IDMZ. El broker MQTT de OT y Redpanda cumplen roles distintos de borde y backbone; su coexistencia no constituye por sí sola una malla distribuida de eventos.

## 3. Justificación Técnica
* **Topología centralizada verificable:** el `docker-compose.yaml` materializa un único broker MQTT para OT y un único clúster Redpanda para IT; los consumidores (`detector-anomalias` y `enrutador-alertas`) leen del mismo backbone central, sin federación entre brokers ni replicación entre dominios.
* **Flujo lineal y acotado al caso de uso:** el recorrido `simulador-ot -> Mosquitto -> puente-dmz -> Redpanda -> detector/enrutador` resuelve un solo flujo de negocio principal y no requiere enrutamiento dinámico entre múltiples dominios, sitios, regiones o líneas de producto.
* **Ausencia de capacidades propias de Event Mesh:** el prototipo no implementa propagación distribuida de tópicos/eventos, descubrimiento entre brokers, políticas de ruteo entre dominios ni gobierno federado de eventos entre varias plataformas de mensajería.
* **Adecuación al alcance del taller:** una malla de eventos completa agregaría complejidad operacional y de sustentación sin aportar evidencia adicional para un escenario con una sola fuente OT principal, un único backbone IT y dos consumidores de negocio.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Adoptar Event Mesh desde el inicio** | Incorporar una topología distribuida de brokers o dominios de eventos federados desde el prototipo. | Sobredimensiona el alcance del taller: no hay múltiples sitios, dominios autónomos ni necesidad de ruteo distribuido que justifique su costo operativo y argumentativo. |
| **Integración punto a punto sin backbone central** | Conectar productores y consumidores con enlaces directos o colas ad hoc entre componentes. | Aumenta el acoplamiento entre servicios y debilita la trazabilidad, la persistencia y la reutilización del flujo de eventos frente a la solución EDA con Redpanda como backbone común. |

## 5. Implicaciones y Próximos Pasos
* En la sustentación debe afirmarse explícitamente que el prototipo implementa **EDA con backbone centralizado**, no un Event Mesh completo.
* La decisión mantiene la arquitectura simple y defendible para la demo, pero limita la flexibilidad para crecimiento multi-sitio o multi-dominio sin rediseño adicional.
* Event Mesh queda registrado como una evolución válida cuando PetroAndes necesite conectar múltiples plantas, distritos, nubes o dominios de negocio con intercambio distribuido de eventos y gobierno federado.
