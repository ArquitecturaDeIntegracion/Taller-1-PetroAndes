# PetroAndes EDA Demo

Demo de integración OT/IT para detectar anomalías de presión y caudal en un ducto.

## Requisitos

- Docker Desktop instalado y en ejecución.
- Docker Compose incluido en Docker Desktop.
- Puertos libres: `1883`, `8000`, `8080`, `8081`, `9092` y `19092`.

No es necesario instalar Python ni crear entornos virtuales. Las dependencias se instalan durante la construcción de las imágenes.

## Inicio rápido

Desde la raíz del proyecto:

```powershell
docker compose up --build
```

El simulador comienza publicando telemetría normal y genera automáticamente cinco lecturas anómalas después de 60 segundos.

Para detener la solución:

```powershell
docker compose down
```

Para borrar también los contenedores detenidos y reconstruir desde cero:

```powershell
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up
```

## Componentes

```text
simulador-ot -> Mosquitto -> puente-dmz -> Redpanda -> detector-anomalias
                                                   -> enrutador-alertas -> sistema-balance
```

- **OT:** el simulador publica telemetría por MQTT en `petroandes/ot/ducto/telemetria`.
- **DMZ:** el puente transforma la telemetría a CloudEvents y la publica en `it-telemetria-topic`.
- **IT:** el detector analiza tres lecturas consecutivas y publica alertas en `it-alertas-topic`.
- **Negocio:** el enrutador convierte la alerta y la envía a la API REST.
- **Balance:** la API mantiene el estado del tramo en memoria.

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
