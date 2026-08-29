import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "sistema-balance"))

from api_balance import AlertaDucto, consultar_estado, registrar_alerta, resolver_estado


class ApiBalanceTest(unittest.TestCase):
    def setUp(self):
        estado = asyncio.run(consultar_estado("Tramo-Centro"))
        if estado["estado_operativo"] != "NORMAL":
            asyncio.run(resolver_estado("Tramo-Centro"))

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
