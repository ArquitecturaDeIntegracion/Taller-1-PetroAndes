# ADR-03: Estandarización de Eventos con CloudEvents y Gobierno del Esquema

**Metadatos**
* **Código:** CITA-ADR-003
* **Fecha:** 2026-09-19
* **Título:** Contrato de Eventos y Gobierno del Esquema
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
PetroAndes posee más de 400.000 tags con nombres y formatos inconsistentes entre distritos. Acoplar los sistemas IT a la sintaxis cruda de cada sensor incrementa el costo de desarrollo y genera fallos catastróficos ante pequeños cambios de hardware ("poison pills"). Se requiere un formato de sobre universal y una regla de evolución de esquema explícita para telemetría y alertas.

## 2. Decisión de Arquitectura
Se estandariza la mensajería con el sobre CloudEvents 1.0 (CNCF, serializado en JSON) para los tres canales del sistema: telemetría OT (MQTT), telemetría normalizada (`it-telemetria-topic`) y alertas (`it-alertas-topic`). El contrato completo se documenta en AsyncAPI 3.0 (canales, mensajes, ejemplos y regla de compatibilidad), y la regla de compatibilidad adoptada para la evolución de los payloads es Backward.

**Estado actual del gobierno de esquema (importante para la sustentación)**
En la implementación actual, el cumplimiento del contrato se aplica por validación de código en los puntos de entrada: `puente.py` valida los campos obligatorios de telemetría antes de envolver en CloudEvents, y `AlertProcessor.java` (`mapAlert`) rechaza hacia `it-alertas-dlq` cualquier CloudEvent de alerta que no tenga `specversion="1.0"`, el type esperado, `datacontenttype="application/json"` o un `nivel_riesgo` fuera del enum permitido. El Schema Registry de Redpanda está desplegado y accesible en el puerto 8081, pero el código del prototipo no registra ni consulta esquemas contra él: la gobernanza es de contrato en código, no de registro centralizado. Se documenta así para evitar afirmar en la sustentación una capacidad no verificable en vivo.

## 3. Justificación Técnico-Económica
* **Desacoplamiento estructural (CloudEvents):** los atributos estándar (`specversion`, `type`, `source`, `datacontenttype`) permiten a los consumidores decidir cómo enrutar sin conocer la sintaxis interna de cada sensor.
* **Prevención de fallos en cascada:** la validación de contrato en el puente y en el enrutador rechaza de inmediato eventos malformados, enviándolos a `it-alertas-dlq` en vez de propagarlos al sistema de negocio.
* **Compatibilidad Backward elegida:** los consumidores (detector, enrutador) deben poder seguir leyendo eventos producidos con una versión más nueva del esquema sin desplegarse al mismo tiempo que el productor; esto es lo que permite evolucionar el puente OT-IT sin coordinar un despliegue simultáneo del detector.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Formatos propietarios** | Publicar payloads JSON libres sin estructura común ni envoltura estándar. | Acopla fuertemente los sistemas IT a la sintaxis de cada sensor y obliga a programar parsing a medida por tipo de dispositivo. |
| **Esquemas sin registro ni validación en código** | Definir esquemas de referencia en documentación, sin ningún control en tiempo de ejecución. | No impide la inyección de datos corruptos o incompatibles; el taller exige explícitamente una regla de compatibilidad exigible, no solo documentada. |

## 5. Implicaciones y Próximos Pasos
* Mantener actualizada la especificación `asyncapi.yaml` como fuente de verdad del contrato (ya cubre los cuatro canales, incluido `it-alertas-dlq`).
* Pendiente antes de la sustentación: decidir si se registra formalmente el JSON Schema del payload de alerta y de telemetría en el Schema Registry (puerto 8081) con la regla Backward configurada allí, para poder demostrarlo en vivo; si no alcanza el tiempo, dejarlo explícito como alcance futuro en el ADR y no como capacidad ya entregada.

