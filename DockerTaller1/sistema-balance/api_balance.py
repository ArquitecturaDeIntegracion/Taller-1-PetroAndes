from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sqlite3

app = FastAPI(
    title="API de Balance Volumétrico - PetroAndes",
    description="API REST para consolidar el estado de los ductos y recibir alertas tempranas de anomalías.",
    version="1.0.0"
)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}

# Modelo de datos para la alerta (esquema OpenAPI)
class AlertaDucto(BaseModel):
    id_alerta: str
    tramo: str
    nivel_riesgo: str
    descripcion: str
    presion_psi: float
    caudal_bpd: float

# SQLite conserva la deduplicación incluso al resolver o reiniciar el servicio.
# En Docker se guarda en un volumen; las pruebas usan :memory:.
db = sqlite3.connect(os.getenv("BALANCE_DB_PATH", ":memory:"), check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS alertas (
    id_alerta TEXT PRIMARY KEY,
    tramo TEXT NOT NULL,
    nivel_riesgo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    presion_psi REAL NOT NULL,
    caudal_bpd REAL NOT NULL,
    activa INTEGER NOT NULL DEFAULT 1
)""")
db.commit()

@app.post("/alertas", summary="Registrar alerta de anomalía", tags=["Integración"])
async def registrar_alerta(alerta: AlertaDucto):
    """Recibe una alerta desde el bus de eventos y actualiza el estado del balance volumétrico."""
    if alerta.tramo == "Tramo-Centro":
        values = alerta.model_dump()
        existing = db.execute(
            "SELECT id_alerta, tramo, nivel_riesgo, descripcion, presion_psi, caudal_bpd FROM alertas WHERE id_alerta = ?",
            (alerta.id_alerta,),
        ).fetchone()
        if existing:
            if dict(zip(AlertaDucto.model_fields, existing)) != values:
                raise HTTPException(status_code=409, detail="id_alerta ya existe con otro contenido")
            return {"status": "Alerta ya procesada", "duplicada": True}
        with db:
            db.execute(
                "INSERT INTO alertas (id_alerta, tramo, nivel_riesgo, descripcion, presion_psi, caudal_bpd) VALUES (:id_alerta, :tramo, :nivel_riesgo, :descripcion, :presion_psi, :caudal_bpd)",
                values,
            )
        print(f"\n[SISTEMA BALANCE] Alerta registrada para {alerta.tramo}: {alerta.descripcion}")
        return {"status": "Alerta procesada y estado actualizado"}
    raise HTTPException(status_code=404, detail="Tramo no encontrado")

@app.get("/estado/{tramo}", summary="Consultar estado consolidado del tramo", tags=["Monitoreo"])
async def consultar_estado(tramo: str):
    """Expone el estado consolidado del tramo para tableros de control o conciliación."""
    if tramo == "Tramo-Centro":
        rows = db.execute(
            "SELECT id_alerta, tramo, nivel_riesgo, descripcion, presion_psi, caudal_bpd FROM alertas WHERE tramo = ? AND activa = 1 ORDER BY rowid",
            (tramo,),
        ).fetchall()
        return {
            "estado_operativo": "CRITICO_REVISION_REQUERIDA" if rows else "NORMAL",
            "alertas_activas": [dict(zip(AlertaDucto.model_fields, row)) for row in rows],
        }
    raise HTTPException(status_code=404, detail="Tramo no encontrado")

@app.post("/estado/{tramo}/resolver", summary="Resolver alertas y normalizar tramo", tags=["Operación"])
async def resolver_estado(tramo: str):
    """Simula la intervención de un operador que revisa el ducto, soluciona el problema y restablece la normalidad."""
    if tramo == "Tramo-Centro":
        with db:
            db.execute("UPDATE alertas SET activa = 0 WHERE tramo = ?", (tramo,))
        print(f"\n[SISTEMA BALANCE] 🛠️ Mantenimiento completado. El {tramo} vuelve a estado NORMAL.")
        return {"status": f"Tramo {tramo} revisado y normalizado"}
    raise HTTPException(status_code=404, detail="Tramo no encontrado")
