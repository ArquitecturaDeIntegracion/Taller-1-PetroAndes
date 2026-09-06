import asyncio
import sys
import unittest
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "sistema-balance"))

os.environ["BALANCE_DB_PATH"] = ":memory:"
from api_balance import AlertaDucto, consultar_estado, registrar_alerta, resolver_estado, db
from fastapi import HTTPException


class ApiBalanceTest(unittest.TestCase):
    def setUp(self):
        with db:
            db.execute("DELETE FROM alertas")

    def test_duplicado_no_reactiva_alerta_resuelta(self):
        alerta = AlertaDucto(id_alerta="duplicada", tramo="Tramo-Centro",
                            nivel_riesgo="CRITICO", descripcion="Prueba", presion_psi=305, caudal_bpd=8050)
        asyncio.run(registrar_alerta(alerta))
        self.assertTrue(asyncio.run(registrar_alerta(alerta))["duplicada"])
        self.assertEqual(len(asyncio.run(consultar_estado("Tramo-Centro"))["alertas_activas"]), 1)
        asyncio.run(resolver_estado("Tramo-Centro"))
        self.assertTrue(asyncio.run(registrar_alerta(alerta))["duplicada"])
        self.assertEqual(asyncio.run(consultar_estado("Tramo-Centro"))["estado_operativo"], "NORMAL")

    def test_id_reutilizado_con_otro_contenido(self):
        alerta = AlertaDucto(id_alerta="conflicto", tramo="Tramo-Centro",
                            nivel_riesgo="CRITICO", descripcion="Prueba", presion_psi=305, caudal_bpd=8050)
        asyncio.run(registrar_alerta(alerta))
        with self.assertRaises(HTTPException) as error:
            asyncio.run(registrar_alerta(alerta.model_copy(update={"presion_psi": 310})))
        self.assertEqual(error.exception.status_code, 409)

    def test_alerta_y_resolucion(self):
        alerta = AlertaDucto(
            id_alerta="test-alerta",
            tramo="Tramo-Centro",
            nivel_riesgo="CRITICO",
            descripcion="Prueba de humo",
            presion_psi=305.0,
            caudal_bpd=8050.0,
        )

        asyncio.run(registrar_alerta(alerta))
        estado_alerta = asyncio.run(consultar_estado("Tramo-Centro"))
        self.assertEqual(estado_alerta["estado_operativo"], "CRITICO_REVISION_REQUERIDA")
        self.assertEqual(len(estado_alerta["alertas_activas"]), 1)

        asyncio.run(resolver_estado("Tramo-Centro"))
        estado_normal = asyncio.run(consultar_estado("Tramo-Centro"))
        self.assertEqual(estado_normal["estado_operativo"], "NORMAL")
        self.assertEqual(estado_normal["alertas_activas"], [])


if __name__ == "__main__":
    unittest.main()
