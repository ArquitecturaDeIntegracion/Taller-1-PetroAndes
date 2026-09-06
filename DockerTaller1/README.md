# PetroAndes EDA Demo

Demo de integración OT/IT para detectar anomalías de presión y caudal en un ducto.

## Requisitos

- Docker Desktop instalado y en ejecución.
- Docker Compose incluido en Docker Desktop.
- Puertos libres: `1883`, `8000`, `8080`, `8081`, `9092` y `19092`.

No es necesario instalar Python, Java ni Maven en el equipo. Las dependencias se instalan durante la construcción de las imágenes; se necesita Internet para esa primera construcción. El flujo se ejecuta íntegramente en Docker local.

## Inicio rápido

Desde la raíz del proyecto:

```powershell
docker compose up --build
```

El simulador comienza publicando telemetría normal y genera automáticamente cinco lecturas anómalas después de 60 segundos.

Para detener la solución:

```powershell
docker compose down -v
```

Para borrar también los contenedores detenidos y reconstruir desde cero:

```powershell
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up
```

## Componentes

```text
simulador-ot -> Mosquitto -> puente-dmz -> Redpanda (it-telemetria-topic)
                                         -> detector-anomalias
                                         -> Redpanda (it-alertas-topic)
                                         -> enrutador-alertas (Apache Camel)
                                              -> sistema-balance (HTTP)
                                              -> it-alertas-dlq (errores)
```

- **OT:** el simulador publica telemetría por MQTT en `petroandes/ot/ducto/telemetria`.
- **DMZ:** el puente transforma la telemetría a CloudEvents y la publica en `it-telemetria-topic`.
- **IT:** el detector analiza tres lecturas consecutivas y publica alertas en `it-alertas-topic`.
- **Negocio:** Apache Camel Main 4.18.0 / Java 21 consume Kafka, valida y convierte la alerta, y la envía a la API REST.
- **Balance:** FastAPI guarda alertas en SQLite, dentro del volumen `balance-data`, y deduplica por `id_alerta` incluso después de resolverlas o reiniciar.
- **Persistencia:** Redpanda almacena eventos y offsets en `redpanda-data`. `docker compose down` conserva ambos volúmenes. `docker compose down -v` elimina los datos de la demostración.

La API simula el estado operativo del tramo; no calcula volúmenes de entrada/salida.

## Integración Apache Camel

Resumen de implementación y resultados verificados: [implementacion-apache-camel.md](docs/implementacion-apache-camel.md).

El servicio conserva el nombre `enrutador-alertas`, su red `it-network`, el grupo Kafka `grupo-enrutador-balance` y las variables `KAFKA_BOOTSTRAP_SERVERS` y `API_URL`. Su implementación Python fue reemplazada por Java. El Dockerfile compila y ejecuta las pruebas Maven antes de crear el contenedor final.

- Entrada: `it-alertas-topic` en `redpanda:9092`.
- Destino: `POST http://sistema-balance:8000/alertas`.
- Mapeo: `id` → `id_alerta`; `data.tramo`, `nivel_riesgo`, `descripcion` conservan sus nombres; `presion_actual_psi` → `presion_psi`; `caudal_actual_bpd` → `caudal_bpd`.
- Éxito: HTTP 2xx. Se confirma el offset manualmente después de la respuesta.
- Fallos transitorios: conexión, timeout, HTTP 408, 429 o 5xx. Hasta cuatro intentos en total, con esperas de 2, 4 y 8 segundos; timeout de conexión de 5 s y respuesta de 10 s.
- JSON/contrato inválido: va directamente a `it-alertas-dlq`. Otros errores HTTP (por ejemplo 404, 409 o 422) van allí sin reintentos.
- DLQ: conserva `original_event` como texto, motivo, intentos, fecha y topic/partición/offset. Se confirma el mensaje original únicamente después del acuse del broker. Si falla la DLQ, Kafka vuelve a intentar el mensaje sin confirmar.
- Procesamiento secuencial (`maxPollRecords=1`) para mantener la confirmación en el hilo consumidor. Cuando no existe un offset previo se usa `earliest`.

La entrega es al menos una vez entre Kafka y el destino/DLQ; la deduplicación persistente evita registrar dos veces la misma alerta. Un ID repetido con contenido diferente responde HTTP 409. El tópico de errores requiere revisión y reenvío explícito: no se reproduce automáticamente. Un cambio de enrutador no recupera mensajes que el antiguo consumidor ya confirmó.

## Pruebas automáticas en Docker

```powershell
docker compose up -d --build
docker compose --profile tests run --build --rm integration-tests
```

La prueba publica eventos reales en Redpanda y verifica transformación HTTP, deduplicación, JSON inválido y envío a DLQ ante HTTP 404. Termina con `INTEGRACION CORRECTA` y código 0. Deja dos alertas de prueba activas e imprime sus IDs. Las seis pruebas Java del build cubren también recuperación transitoria, agotamiento de reintentos y ausencia de commit si falla la DLQ.

Para ejecutar las pruebas de API sin instalar dependencias en el equipo:

```powershell
docker compose run --rm --no-deps -v "${PWD}/tests:/tests:ro" sistema-balance python -m unittest discover -s /tests -p test_api.py
```

## Prueba de indisponibilidad y recuperación

Con el flujo iniciado, detener temporalmente la API y reiniciar el simulador para generar otra anomalía a los 60 segundos:

```powershell
docker compose stop sistema-balance
docker compose restart simulador-ot
docker compose logs -f enrutador-alertas
```

La nueva alerta agota cuatro intentos y se guarda en `it-alertas-dlq`. Consultarla en la consola Redpanda (`http://localhost:8080`), seleccionando ese tópico. Después:

```powershell
docker compose start sistema-balance
docker compose restart simulador-ot
```

La siguiente anomalía debe entregarse normalmente. Para recuperar la alerta anterior, copiar el valor de `original_event` de la DLQ y publicarlo como JSON en `it-alertas-topic` desde la consola. No publicar el sobre completo de la DLQ. Mantener el `id` permite deduplicar si el POST anterior sí había llegado.

Para comprobar persistencia, consultar el estado, reiniciar `sistema-balance` y volver a consultarlo: las alertas deben permanecer. Resolver el tramo y reenviar el mismo evento tampoco debe reactivarlo.

## URLs

- API Swagger: <http://localhost:8000/docs>
- Estado inicial: <http://localhost:8000/estado/Tramo-Centro>
- Consola Redpanda: <http://localhost:8080>

Para resolver el tramo después de una alerta:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/estado/Tramo-Centro/resolver
```

El estado debe volver a `NORMAL`.

## Anomalía

En Docker, el Compose establece:

- `AUTO_ANOMALY_AFTER_SECONDS=60`
- `ANOMALY_READINGS=5`

## Validación rápida

Consultar el estado:

```powershell
Invoke-RestMethod http://localhost:8000/estado/Tramo-Centro
```

Después de la anomalía debe mostrar `CRITICO_REVISION_REQUERIDA` y una alerta activa.

Ver los logs del flujo:

```powershell
docker compose logs -f simulador-ot puente-dmz detector-anomalias enrutador-alertas sistema-balance
```

Ejecutar la prueba de API localmente:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## Troubleshooting

- Si un servicio reinicia, revisar `docker compose logs <servicio>`.
- Si los puertos están ocupados, detener el proceso que los usa y repetir `docker compose up --build`.
- Si se modifican dependencias, repetir `docker compose build --no-cache`.
- Si el navegador no abre la API, comprobar que `sistema-balance` esté `healthy` con `docker compose ps`.

Mosquitto está configurado con acceso anónimo únicamente para esta demostración local. Esta configuración no debe utilizarse en producción sin autenticación, autorización, TLS y una política de red restrictiva.
