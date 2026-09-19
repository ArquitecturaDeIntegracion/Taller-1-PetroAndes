# ADR-02: Posicionamiento Seguro del Puente de Integración OT-IT (IDMZ Nivel 3.5)

**Metadatos**
* **Código:** CITA-ADR-002
* **Fecha:** 2026-09-19
* **Título:** Ubicación de la DMZ y Conductos IEC 62443
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
La integración de señales de sensores físicos (Nivel 2/3 - OT) con sistemas de análisis corporativo (Nivel 4 - IT) introduce riesgos de ciberseguridad industrial. En cumplimiento del Modelo Purdue y de IEC 62443, ningún sistema de la red corporativa o de nube IT puede iniciar conexiones directas ni escribir sobre la red de control industrial. Se requiere definir la ubicación física/lógica del componente Puente OT-IT y la dirección del flujo de comunicación.

## 2. Decisión de Arquitectura
El Puente OT-IT (`puente-dmz-python/puente.py`) se ubica en la Zona Desmilitarizada Industrial (IDMZ, Nivel 3.5), materializada como una red Docker independiente (`dmz-network`). El puente es el único componente que pertenece simultáneamente a `ot-network` (donde vive Mosquitto) y a `dmz-network`; ningún otro servicio del proyecto toca `ot-network`. Todo tráfico es saliente desde el puente: se suscribe (pull) al broker MQTT en el Nivel 3 y publica (push) hacia Redpanda en `it-network`/`dmz-network`. Redpanda está conectado tanto a `dmz-network` como a `it-network` para recibir la publicación del puente sin exponer nunca la red OT a los consumidores de negocio (detector, enrutador, API de balance), que solo se conectan a `it-network`.

## 3. Justificación Técnica
* **Aislamiento físico y lógico (IEC 62443):** la segmentación por redes Docker (`ot-network` / `dmz-network` / `it-network`) evita que una vulnerabilidad en IT se propague a Mosquitto o a los sensores simulados.
* **Conductos orientados a la seguridad:** el puente inicia sesiones de salida hacia MQTT (Nivel 3) y hacia Redpanda (Nivel 4); no existe ningún listener entrante en el puente ni un canal de retorno IT→OT en el código, por lo que un firewall real podría bloquear el 100% del tráfico entrante hacia `ot-network`.
* **Doble pertenencia de red controlada de Redpanda:** que Redpanda participe de `dmz-network` e `it-network` no reabre el conducto OT→IT: solo el puente puede escribir en el tópico de telemetría, y ningún servicio de `it-network` tiene ruta de red hacia `ot-network` ni hacia Mosquitto.
* **Mínimo privilegio operativo:** el puente solo lee telemetría y publica; no existe código que traduzca alertas o comandos de negocio hacia MQTT.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Conexión directa IT-OT** | Permitir que el motor de analítica en IT lea directamente del historiador AVEVA PI en OT. | Viola el Modelo Purdue y IEC 62443; expone el SCADA a denegación de servicio y a compromisos desde la red corporativa. |
| **Push directo de OT a IT** | Un agente instalado en el Nivel 3 (OT) publica telemetría directamente hacia Redpanda en la nube IT. | Obliga a abrir puertos de salida directos desde la red de control hacia IT, saltándose la inspección y el búfer que ofrece la IDMZ. |

## 5. Implicaciones y Próximos Pasos
* En producción: abrir en el firewall perimetral solo el puerto 1883/8883 (MQTT, saliente desde la IDMZ hacia OT) y el 9092 (Kafka, saliente desde la IDMZ hacia IT); en la demo, `mosquitto.conf` usa `allow_anonymous true` y no hay TLS, lo cual debe señalarse explícitamente en la sustentación como limitación aceptada solo para el entorno local.
* `puente-dmz` corre con `restart: on-failure` para tolerar reinicios de Mosquitto o de Redpanda durante el arranque del compose.

