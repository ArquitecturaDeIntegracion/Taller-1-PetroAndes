# ADR-06: Decisión sobre la adopción del patrón Transactional Outbox para publicación confiable

**Metadatos**
* **Código:** CITA-ADR-006
* **Fecha:** 2026-09-20
* **Título:** Adopción diferida del patrón Transactional Outbox
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
El enunciado del taller exige justificar la selección del patrón Transactional Outbox para publicación confiable. En la solución actual, el puente OT→IT consume telemetría MQTT y la publica directamente en Redpanda, mientras que el detector consume de Redpanda y publica alertas directamente en `it-alertas-topic`. El sistema de balance, por su parte, no emite eventos: solo recibe alertas vía REST y las persiste en SQLite. Se requiere decidir si el prototipo debe afirmar la implementación formal de Transactional Outbox o si corresponde adoptar un mecanismo alternativo de confiabilidad más ajustado al flujo realmente construido.

## 2. Decisión de Arquitectura
Se evalúa el patrón Transactional Outbox, pero no se adopta en esta iteración del prototipo. Para el Taller 1, PetroAndes resuelve la publicación confiable con una combinación de persistencia nativa del broker, entrega al-menos-una-vez, confirmación controlada del consumidor Kafka en el enrutador de alertas, DLQ e idempotencia en el sistema de balance. No existe en el repositorio un servicio que actualice estado de negocio en una base transaccional local y que, en la misma unidad de consistencia, deba publicar un evento hacia el backbone.

## 3. Justificación Técnica
* **Los publicadores actuales son procesadores de flujo, no servicios CRUD transaccionales:** `puente.py` recibe telemetría de MQTT y la publica en Redpanda sin escribir antes en una base de datos local; `detector.py` consume telemetría y genera alertas en memoria, también sin una transacción local que coordinar con la publicación.
* **No hay doble escritura local del tipo que Transactional Outbox resuelve:** el problema clásico del patrón aparece cuando un servicio debe persistir en su propia base de datos y, además, emitir un evento sin riesgo de inconsistencia entre ambas acciones. En este prototipo, ningún productor combina esas dos operaciones sobre un mismo agregado local.
* **La confiabilidad verificable ya está implementada por otros mecanismos:** el enrutador de alertas usa commit manual de offset, reintentos, `acks=all` hacia la DLQ y el sistema de balance deduplica por `id_alerta` en SQLite. Esto no equivale a Transactional Outbox, pero sí constituye una estrategia defendible de publicación/procesamiento confiable para el alcance del taller.
* **Adoptarlo ahora introduciría complejidad artificial:** para justificar un outbox real habría que rediseñar al menos un productor para persistir primero en una tabla outbox y luego relanzar esos registros con un relay/poller, sin una necesidad funcional clara en el escenario actual.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Implementar Transactional Outbox en el detector o en el puente** | Persistir cada evento saliente en una base local y publicar desde una tabla outbox mediante un proceso relay. | No existe una entidad de negocio local cuyo cambio de estado deba mantenerse atómicamente consistente con la publicación; agregar almacenamiento intermedio solo para “cumplir el patrón” sobredimensiona el prototipo. |
| **Publicación directa sin controles adicionales** | Producir a Redpanda o llamar la API REST sin DLQ, reintentos ni deduplicación. | Debilita la confiabilidad observable de la demo y deja casos de duplicación o pérdida sin tratamiento explícito. |

## 5. Implicaciones y Próximos Pasos
* En la sustentación debe afirmarse que el prototipo **evalúa** Transactional Outbox, pero **no lo implementa** formalmente en esta iteración.
* La confiabilidad actual debe sustentarse con los mecanismos realmente verificables en el repositorio: persistencia del broker, procesamiento al-menos-una-vez, DLQ, reintentos e idempotencia del receptor.
* Si PetroAndes evoluciona hacia servicios que actualicen datos de negocio propios y publiquen eventos derivados de esos cambios, entonces sí debe incorporarse Transactional Outbox o una alternativa equivalente de consistencia entre base de datos y bus de eventos.
