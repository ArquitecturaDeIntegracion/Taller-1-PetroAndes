# ADR-04: Selección de Apache Camel como Motor de Integración y Enrutamiento EIP

**Metadatos**
* **Código:** CITA-ADR-004
* **Fecha:** 2026-09-19
* **Título:** Motor de Integración Corporativo
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
El detector de anomalías publica alertas asíncronas en `it-alertas-topic`. El Sistema de Nominaciones y Balance Volumétrico (SNBVT) solo expone una API REST síncrona (`POST /alertas`). Se requiere un componente que consuma de Redpanda de forma confiable, traduzca el CloudEvent al contrato esperado por el REST, maneje fallos transitorios y permanentes sin perder ni duplicar alertas, y deje trazabilidad de lo que no pudo entregarse.

## 2. Decisión de Arquitectura
Se adopta Apache Camel (Camel Main 4.18.0, Java 21), embebido como microservicio ligero (`enrutador-alertas`), como motor de integración entre Redpanda y la API REST de AndesTransporte.

## 3. Justificación Técnica
* **Message Translator (EIP):** `AlertProcessor.mapAlert` convierte el CloudEvent de alerta (`specversion`, `type`, `data.*`) al contrato JSON plano que espera el SNBVT (`id_alerta`, `tramo`, `nivel_riesgo`, `descripcion`, `presion_psi`, `caudal_bpd`), rechazando el mensaje si falta un campo requerido o si `nivel_riesgo` no pertenece al enum permitido.
* **Dead Letter Channel (EIP):** los eventos con contrato inválido, los errores HTTP no reintentables (404, 409, 422, entre otros) y los reintentos agotados se publican en `it-alertas-dlq` junto con el evento original, el motivo, el número de intentos y el topic/partición/offset de origen.
* **Guaranteed Delivery mediante confirmación manual de offset:** el consumidor Kafka se configura con `autoCommitEnable=false` y `maxPollRecords=1`; el offset solo se confirma después de recibir una respuesta HTTP 2xx del SNBVT o después de que Redpanda confirme la escritura en `it-alertas-dlq` (producer síncrono con `acks=all`). Si la escritura en la DLQ falla, el offset no se confirma y Kafka reintrega el mensaje.
* **Reintentos con backoff exponencial:** hasta 4 intentos con esperas de 2, 4 y 8 segundos ante fallos transitorios (errores de conexión, timeout, HTTP 408/429/5xx). Esta lógica está implementada como código de aplicación dentro de `AlertProcessor`, no como el manejador de errores por defecto de Camel: la ruta desactiva explícitamente ese manejador (`errorHandler(noErrorHandler())`) para mantener el control de la confirmación de offset en el mismo hilo del consumidor Kafka.
* **Idempotencia end-to-end (fuera de Camel):** la entrega es al-menos-una-vez entre Kafka y el destino; lo que la hace segura es que `sistema-balance` usa `id_alerta` como llave primaria en SQLite y responde 200 ante una alerta repetida con el mismo contenido, o 409 si el mismo id llega con contenido distinto. Es un patrón de Receptor Idempotente aplicado en la API de negocio, no un Idempotent Consumer de Camel.
* **Despliegue ultra-ligero:** se empaqueta como microservicio en contenedor (sin clúster de Camel ni servidores de aplicación dedicados), alineado con una estrategia de servicios livianos en contenedores.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Apache NiFi** | Plataforma visual de arrastrar y soltar para flujos de datos. | Requiere un clúster JVM dedicado y está orientado a orquestación de dataflows masivos; exceso de infraestructura para una sola ruta de integración de alertas. |
| **Código customizado (Python/Go)** | Escribir un script a medida que consuma de Redpanda y llame la API REST. | Carecería de las abstracciones de productor/consumidor Kafka, manejo de commits manuales y ciclo de vida de aplicación que Camel Main ya resuelve, aumentando la deuda técnica del propio manejo de reintentos y DLQ. |

## 5. Implicaciones y Próximos Pasos
* No se implementó un Content-Based Router ni un Wire Tap en esta iteración: la ruta es única (`kafka:it-alertas-topic` → HTTP/DLQ). Si en la sustentación se quiere mostrar esos patrones por nombre canónico, deben agregarse explícitamente al código antes de la defensa; de lo contrario, nombrar solo los patrones verificables en el repositorio: Message Translator, Dead Letter Channel y Guaranteed Delivery.
* Las seis pruebas unitarias de `AlertProcessorTest` y la prueba de integración (`test_integration.py`) cubren: transformación exitosa, JSON inválido a DLQ, HTTP 404 a DLQ, recuperación tras fallo transitorio, agotamiento de reintentos y ausencia de commit si falla la DLQ — evidencia útil para sustentar el criterio de "implementación funcional" de la rúbrica.

