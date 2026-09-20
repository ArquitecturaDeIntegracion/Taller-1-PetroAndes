# ADR-01: Selección de la Plataforma de Streaming de Eventos

**Metadatos**
* **Código:** CITA-ADR-001
* **Fecha:** 2026-09-19
* **Título:** Selección de Broker de Eventos
* **Estatus:** ACEPTADO
* **Autor:** Equipo de Arquitectura CITA — Grupo 1 (Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio)
* **Aprobador:** Comité de Arquitectura PetroAndes

## 1. Contexto y Definición del Problema
AndesTransporte (filial de PetroAndes S.A.) opera una red de 9.000 km de oleoductos y poliductos que transportan 1.119 kbd. La infraestructura enfrenta pérdidas críticas por hurto de hidrocarburos mediante válvulas ilícitas (más de 400 halladas en el último año). Los sistemas SCADA e historiadores (AVEVA PI System) capturan más de 400.000 señales operativas de caudal y presión, pero el cruce entre una caída anómala de presión y un descuadre de balance solo se descubre semanas después, durante conciliación manual. Se requiere una plataforma de eventos que ingiera, almacene de forma inmutable y distribuya la telemetría hacia un motor de detección de anomalías en tiempo casi real.

## 2. Decisión de Arquitectura
Se adopta Redpanda (imagen v25.2.2, modo dev-container de un solo nodo para el prototipo) como el bróker de eventos central del Nivel 4 (IT), junto con su consola de administración (Redpanda Console) y su Schema Registry nativo (puerto 8081). El clúster aloja tres tópicos: `it-telemetria-topic`, `it-alertas-topic` e `it-alertas-dlq`, creados de forma idempotente por un contenedor de inicialización (`redpanda-init`) antes de levantar el resto de servicios.

## 3. Justificación Técnica
* **Compatibilidad 100% con la API de Kafka:** permite usar el ecosistema de clientes de Kafka (`confluent-kafka` en Python, `camel-kafka` en Java) sin administrar clústeres complejos.
* **Alto desempeño y baja latencia de cola:** arquitectura thread-per-core (Seastar) en C++, sin pausas de recolección de basura de la JVM.
* **Simplicidad operacional:** un único binario con consenso Raft interno; el docker-compose del prototipo lo despliega como un solo contenedor, adecuado para la demo local exigida por el taller.
* **Cumplimiento de estándares:** expone un Schema Registry nativo en el puerto 8081. En esta iteración el puerto está expuesto pero el gobierno de esquemas se resuelve por validación de contrato en el código del puente y del enrutador (ver ADR-03); dejar el registro operando desde el inicio evita una migración de bróker si el equipo decide activarlo formalmente.

## 4. Alternativas Evaluadas y Descarte

| Alternativa | Descripción | Razón de descarte |
| :--- | :--- | :--- |
| **Apache Kafka** | Plataforma de streaming distribuida líder en Java. | Alta complejidad operacional: requiere JVM tuning y administración de ZooKeeper/KRaft, elevando el costo de propiedad para un prototipo de curso. |
| **RabbitMQ** | Bróker de mensajería tradicional basado en AMQP. | Carece de un log de eventos persistente e inmutable a gran escala, limitando la capacidad de reprocesar telemetría histórica ante fallos del detector. |

## 5. Implicaciones y Próximos Pasos
* Los tres tópicos se crean con `--partitions 1 --replicas 1`, coherente con un clúster de un solo nodo y un único tramo de ducto simulado (Tramo-Centro): garantiza orden total de los eventos sin necesidad de clave de partición.
* Trabajo futuro (fuera del alcance de este taller): al incorporar más tramos o sensores, particionar `it-telemetria-topic` e `it-alertas-topic` por la clave tramo, de modo que el orden se preserve por tramo mientras se habilita paralelismo de consumo entre tramos distintos.
* Aumentar replicas al escalar a un clúster multinodo, ya que `replicas=1` no tolera la caída del único bróker.
