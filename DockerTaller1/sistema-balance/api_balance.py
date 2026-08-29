from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

# Base de datos en memoria para almacenar el estado consolidado
estado_tramos = {
    "Tramo-Centro": {
        "estado_operativo": "NORMAL",
        "alertas_activas": []
    }
}

@app.post("/alertas", summary="Registrar alerta de anomalía", tags=["Integración"])
async def registrar_alerta(alerta: AlertaDucto):
    """Recibe una alerta desde el bus de eventos y actualiza el estado del balance volumétrico."""
    if alerta.tramo in estado_tramos:
        estado_tramos[alerta.tramo]["estado_operativo"] = "CRITICO_REVISION_REQUERIDA"
        estado_tramos[alerta.tramo]["alertas_activas"].append(alerta.model_dump())
        print(f"\n[SISTEMA BALANCE] Alerta registrada para {alerta.tramo}: {alerta.descripcion}")
        return {"status": "Alerta procesada y estado actualizado"}
    raise HTTPException(status_code=404, detail="Tramo no encontrado")

@app.get("/estado/{tramo}", summary="Consultar estado consolidado del tramo", tags=["Monitoreo"])
async def consultar_estado(tramo: str):
    """Expone el estado consolidado del tramo para tableros de control o conciliación."""
    if tramo in estado_tramos:
        return estado_tramos[tramo]
    raise HTTPException(status_code=404, detail="Tramo no encontrado")

@app.post("/estado/{tramo}/resolver", summary="Resolver alertas y normalizar tramo", tags=["Operación"])
async def resolver_estado(tramo: str):
    """Simula la intervención de un operador que revisa el ducto, soluciona el problema y restablece la normalidad."""
    if tramo in estado_tramos:
        estado_tramos[tramo]["estado_operativo"] = "NORMAL"
        # Limpiamos las alertas activas (en un sistema real se moverían a una tabla de histórico)
        estado_tramos[tramo]["alertas_activas"].clear()
        print(f"\n[SISTEMA BALANCE] 🛠️ Mantenimiento completado. El {tramo} vuelve a estado NORMAL.")
        return {"status": f"Tramo {tramo} revisado y normalizado"}
    raise HTTPException(status_code=404, detail="Tramo no encontrado")