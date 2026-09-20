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
Se estandariza la mensajería de la capa IT con un sobre JSON basado en CloudEvents 1.0 (CNCF) para los canales `it-telemetria-topic` e `it-alertas-topic`. La telemetría OT que viaja por MQTT (`petroandes/ot/ducto/telemetria`) se mantiene como JSON plano y es normalizada por el puente antes de publicarse en Redpanda. El contrato completo se documenta en AsyncAPI 3.0 (canales, mensajes, ejemplos y regla de compatibilidad), y la regla de compatibilidad adoptada para la evolución de los payloads es Backward a nivel documental.

**Estado actual del gobierno de esquema (importante para la sustentación)**
En la implementación actual, el cumplimiento del contrato es parcial y se concentra sobre todo en el flujo de alertas. `puente.py` transforma la telemetría MQTT a un sobre JSON con atributos `specversion`, `type`, `source` y `datacontenttype`, pero hoy no valida explícitamente los campos obligatorios del payload OT ni registra esquemas en el Schema Registry. En cambio, `AlertProcessor.java` (`mapAlert`) sí rechaza hacia `it-alertas-dlq` cualquier alerta que no tenga `specversion="1.0"`, el `type` esperado, `datacontenttype="application/json"` o un `nivel_riesgo` fuera del enum permitido. El Schema Registry de Redpanda está desplegado y accesible en el puerto 8081, pero el código del prototipo no registra ni consulta esquemas contra él: la gobernanza efectiva es de contrato documentado en AsyncAPI y validación en código solo donde está implementada. Se documenta así para evitar afirmar en la sustentación una capacidad no verificable en vivo.

## 3. Justificación Técnico-Económica
* **Desacoplamiento estructural en IT:** los atributos del sobre (`specversion`, `type`, `source`, `datacontenttype`) permiten a los consumidores de Redpanda decidir cómo enrutar sin conocer la sintaxis cruda del mensaje OT original.
* **Prevención parcial de fallos en cascada:** la validación de contrato está implementada de forma verificable en el enrutador de alertas, que rechaza eventos inválidos hacia `it-alertas-dlq`; en telemetría, la normalización existe pero la validación estricta del payload OT sigue siendo trabajo pendiente.
* **Compatibilidad Backward definida como política de contrato:** la intención arquitectónica es que los consumidores (detector, enrutador) puedan seguir leyendo eventos producidos con una versión más nueva del esquema sin despliegues coordinados, pero esta regla aún no se hace cumplir automáticamente mediante Schema Registry en el prototipo actual.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Formatos propietarios** | Publicar payloads JSON libres sin estructura común ni envoltura estándar. | Acopla fuertemente los sistemas IT a la sintaxis de cada sensor y obliga a programar parsing a medida por tipo de dispositivo. |
| **Esquemas sin registro ni validación en código** | Definir esquemas de referencia en documentación, sin ningún control en tiempo de ejecución. | No impide la inyección de datos corruptos o incompatibles; el taller exige explícitamente una regla de compatibilidad exigible, no solo documentada. |

## 5. Implicaciones y Próximos Pasos
* Mantener actualizada la especificación `asyncapi.yaml` como fuente de verdad del contrato (ya cubre los cuatro canales, incluido `it-alertas-dlq`).
* Pendiente antes de la sustentación: decidir si se registra formalmente el JSON Schema del payload de alerta y de telemetría en el Schema Registry (puerto 8081) con la regla Backward configurada allí, para poder demostrarlo en vivo.
* Si no se implementa esa integración a tiempo, sostener explícitamente que la compatibilidad Backward es una política arquitectónica documentada y no una capacidad automatizada ya entregada por la plataforma.
* También queda pendiente endurecer `puente.py` con validación explícita de campos obligatorios y completar el sobre de telemetría con todos los atributos requeridos si se desea afirmar cumplimiento estricto de CloudEvents 1.0 para ese flujo.
