# Análisis IT/OT: Modelo Purdue, DMZ, IEC 62443
## Solución de Integracion de Telemetría OT/IT para AndesTransporte - PetroAndes S.A.

**Autores:** [Jorge Useche, Jonnathan Caballero, Jairo Villalobos, Juan Roncancio]
**Curso:** ARTI 4212 - Arquitectura de Integración
**Universidad:** Universidad de los Andes
**Última Fecha Modificación:** Septiembre 5 de 2026
**Proyecto:** Taller 1 - Integración OT/IT Dirigida por Eventos en PetroAndes

---

## Resumen

El presente documento tiene como propósito analizar cómo la solución de detección de anomalías en ductos de AndesTransporte (filial de PetroAndes S.A.) implementa principios de:

1. **Modelo Purdue** - Separación jerárquica de 5 niveles de sistemas.
2. **DMZ Industrial (nivel 3.5)** - Frontera controlada entre OT e IT.
3. **IEC 62443** - Estándar global de ciberseguridad industrial a mediante zonas y ductos.

La presente solución resuelve un problema crítico de negocio identificado en el caso de PetroAndes: **"La detección tardía de anomalías en ductos (válvulas ilícitas, fugas) que tarda semanas en sistemas manuales, retrasando la acción operativa."**

---

## 1. Modelo Purdue

### 1.1 ¿Qué es el modelo Purdue?

El **Modelo de Refinerías Purdue** es un marco arquitectónico desarrollado en los años 1990 por la Universidad Purdue en colaboración con el Industry-Purdue University Consortium for Computer Integrated Manufacturing.

**Definición oficial (NIST SP 800-82 Rev. 3, Septiembre 2023)**

El modelo Purdue es una arquitectura jerárquica que organiza los sistemas de una instalación industrial en **niveles claramente diferenciados**, separando la **instrumentación y control físico (OT)** de los **sistemas de gestión y corporativos (IT)**, con el objetivo de limitar el alcance de incidentes de seguridad y proteger aquello que es verdaderamente crítico para la operación.

**Propósito central**

Según la Universidad Purdue y reafirmado por NIST, el modelo responde a una realidad operativa específica: **en tecnología operativa (OT), la disponibilidad es la prioridad máxima**. Si un servidor corporativo falla, el impacto es económico. Si falla un sistema de control de una planta industrial, el impacto puede ser:
- Parada de planta (Pérdidas millonarias)
- Riesgos físicos a personal
- Daño ambiental

El modelo Purdue establece **límites de confianza claros** entre OT e IT para garantizar que errores, ataques o cambios en IT causen paradas operacionales en OT.

### 1.2 Los 5 niveles jerárquicos del modelo Purdue

| Nivel | Nombre | Descripción | Ejemplos en PetroAndes | Latencia | Criticidad |
|-------|-------|-------|-------|-------|-------|
| **0** | Field Instrumentation | Sensores, transmisores, actuadores físicos en el campo | Tags SCADA de presión (PRES_001), caudal (FLOW_002), válvulas | Milisegundos | Crítica |
| **1** | Basic Process Control | PLCs, DCS que ejecutan lazos cerrados de control automático | SCADA de campos, SCADA de ductos, RTUs | Milisegundos a segundos | Crítica |
| **2** | Area Supervisión & Batch | Historiadores, HMIs, sistemas de supervisión local de áreas | Historiador AVEVA PI (1 por refinería, 1 por campo), alarmas, trending | Segundos a minutos | Alta |
| **3** | Operations Management | MES, planificación, análisis operativo (aún en el piso de la planta) | Sistema de nominaciones de transporte, MES de refinerías, historiador coporativo | Minutos a horas | Media |
| **4** | Corporate planning | ERP, finanzas, decisiones de negocio | SAP HPM, ETRM trading, decisiones de portafolio | Horas a días | Media-Baja |
| **5** | External Networks | Conexiones a internet, organismos reguladores, terceros | Reportes a ANH, comunicación con remitentes terceros | Variable | Baja |

### 1.3 Flujos de Información entre niveles

**Flujo descendente (Órdenes, Setpoints):**
```
Nivel 4 (SAP HPM): "Transportar 1.119 kbd esta semana"
    ↓ (Orden de transporte)
Nivel 3 (Sistema de nominaciones): "Station A-B: 450 bpd, Station B-C: 420 bpd"
    ↓ (Programa detallado)
Nivel 2 (Historiador): "Manten presión entre 400 y 510 PSI en Tramo-Centro"
    ↓ (Setpoint)
Nivel 1 (SCADA): "Si presión < 400, alarma crítica"
    ↓ (Lógica)
Nivel 0 (Válvula motorizada): Se abre/cierra automáticamente
```

**Flujo ascendente (Datos, Alertas):**

```
Nivel 0: "Sensor mide 505 PSI"
    ↑ (Lectura RAW)
Nivel 1: "SCADA confirma lectura, sin alarma"
    ↑ (Señal procesada)
Nivel 2: "Historiador almacena última hora, caudal bajó 0.5%"
    ↑ (Datos resumidos, 5 min de rezago)
Nivel 3: "Sistema de balance calcula: pérdidas normales (evaporación), sin anomalías"
    ↑ (KPI Operativo)
Nivel 4 (SAP): "Dashboard: Tramo-Centro al 100% de capacidad, en presupuesto"
    ↑ (Métrica de negocio, días de rezago)
```

**La realidad de PetroAndes antes de la solución**

Según el caso de estudio **"la detección de anomalías en ductos era completamente manual"**

"Las señales de presión y caudal existen en los SCADA y en los historiadores, pero la correlación entre una caida anómala de presión y un descuadre del balance del tramo solo se descubre **"semanas después"**, cuando los analistas concilian manualmente las planillas de medición con los reportes del sistema de nomincaciones y con SAP."

Esto quiere decir, que **el flujo ascendente de datos no era en tiempo real**. Las anomalías que sucedían en Nivel 0-1 no eran visibles en Nivel 3 sino hasta 2-3 semanas después (manual, con rezago).

---