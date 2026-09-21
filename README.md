# Taller-1-PetroAndes

<p align="center">
  <img src="https://github.com/user-attachments/assets/24c28243-db13-46cd-892d-57686460ab01" alt="Arquitectura de integración PetroAndes" width="200" />
</p>

Repositorio del Taller 1 de PetroAndes.

## Índice del contenido solicitado en el enunciado

### Enunciado base
- [Enunciado del taller](./enunciado-taller1.md)

### Entregables principales
- [README de pasos para reproducir el ejercicio](./DockerTaller1/README.md)
- [Infraestructura con Docker Compose](./DockerTaller1/docker-compose.yaml)
- [Contrato de eventos AsyncAPI 3.0](./DockerTaller1/asyncapi.yaml)
- [ADRs de arquitectura](./ADRs/)
- [Diagrama C4](./C4%20Diagram/Arquitectura%20de%20Integración%20Taller%201.drawio)
- [Análisis Purdue, DMZ e IEC 62443](./Purdue%20Analysis/)

### Implementación funcional
- [Simulación OT](./DockerTaller1/simulador-ot/)
- [Puente OT->IT por DMZ](./DockerTaller1/puente-dmz-python/)
- [Detector de anomalías](./DockerTaller1/detector-anomalias/)
- [Flujo de integración / enrutamiento de alertas](./DockerTaller1/enrutador-alertas/)
- [API REST del sistema de balance](./DockerTaller1/sistema-balance/)
- [Pruebas automáticas](./DockerTaller1/tests/)

## Mapa del repositorio

| Requerimiento | Ubicación en el repositorio |
| --- | --- |
| Diseño arquitectónico y calidad de los ADRs | [ADRs](./ADRs/), [Diagrama C4](./C4%20Diagram/Arquitectura%20de%20Integración%20Taller%201.drawio) |
| Contrato AsyncAPI/CloudEvents y gobierno del esquema | [AsyncAPI](./DockerTaller1/asyncapi.yaml), [ADR-03](./ADRs/ADR-03%20-%20Estandarización%20de%20Eventos%20con%20CloudEvents%20y%20Gobierno%20del%20Esquema.md) |
| Implementación funcional (broker, MQTT, puente, flujo, detección) | [Docker Compose](./DockerTaller1/docker-compose.yaml), [simulador-ot](./DockerTaller1/simulador-ot/), [puente-dmz-python](./DockerTaller1/puente-dmz-python/), [detector-anomalias](./DockerTaller1/detector-anomalias/), [enrutador-alertas](./DockerTaller1/enrutador-alertas/), [sistema-balance](./DockerTaller1/sistema-balance/), [tests](./DockerTaller1/tests/) |
| Calidad del análisis IT/OT (Purdue, DMZ, IEC 62443) | [Purdue Analysis](./Purdue%20Analysis/), [ADR-02](./ADRs/ADR-02%20-%20Posicionamiento%20Seguro%20del%20Puente%20de%20Integración%20OT-IT.md) |
| Sustentación | [Guía de ejecución y validación](./DockerTaller1/README.md), [Enunciado](./enunciado-taller1.md#sustentación) |

## Detalle por requerimiento del enunciado

### Análisis y diseño
- **Diagrama C4 (contexto y contenedores):** [C4 Diagram](./C4%20Diagram/Arquitectura%20de%20Integración%20Taller%201.drawio)
- **Modelo Purdue, DMZ industrial y conductos IEC 62443:** [Purdue Analysis](./Purdue%20Analysis/)
- **ADRs con decisiones y alternativas descartadas:** [ADRs](./ADRs/)
- **Contrato de eventos con AsyncAPI, CloudEvents y compatibilidad:** [AsyncAPI](./DockerTaller1/asyncapi.yaml) y [ADR-03](./ADRs/ADR-03%20-%20Estandarización%20de%20Eventos%20con%20CloudEvents%20y%20Gobierno%20del%20Esquema.md)

### Parte práctica
- **Broker de eventos, consola y schema registry:** [docker-compose.yaml](./DockerTaller1/docker-compose.yaml)
- **Broker MQTT y generador de datos sintéticos:** [simulador-ot](./DockerTaller1/simulador-ot/) y [mosquitto.conf](./DockerTaller1/mosquitto.conf)
- **Puente OT→IT con normalización a CloudEvents:** [puente-dmz-python](./DockerTaller1/puente-dmz-python/)
- **Consumidor con detección de anomalías:** [detector-anomalias](./DockerTaller1/detector-anomalias/)
- **Integración con negocio y API REST/OpenAPI:** [enrutador-alertas](./DockerTaller1/enrutador-alertas/) y [sistema-balance](./DockerTaller1/sistema-balance/)
- **Instrucciones reproducibles de ejecución:** [README técnico](./DockerTaller1/README.md)
- **Pruebas de soporte para la demostración:** [tests](./DockerTaller1/tests/)
