"""Prueba real de Kafka -> Camel -> HTTP; ejecutar con el perfil tests de Compose."""
import json
import os
import time
import uuid
import urllib.request


def main():
    from confluent_kafka import Consumer, Producer

    brokers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
    api = os.getenv("BALANCE_URL", "http://sistema-balance:8000")
    run_id = str(uuid.uuid4())
    producer = Producer({"bootstrap.servers": brokers})
    consumer = Consumer({"bootstrap.servers": brokers, "group.id": "test-" + run_id,
                         "auto.offset.reset": "earliest", "enable.auto.commit": False})
    consumer.subscribe(["it-alertas-dlq"])

    def publish(raw):
        errors = []
        producer.produce("it-alertas-topic", value=raw.encode(),
                         on_delivery=lambda err, msg: errors.append(str(err)) if err else None)
        if producer.flush(15) or errors:
            raise AssertionError(f"Publicacion fallida: {errors}")

    def state():
        with urllib.request.urlopen(api + "/estado/Tramo-Centro", timeout=5) as response:
            return json.load(response)

    def wait_for(predicate, description, timeout=90):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                print("OK:", description, flush=True)
                return
            time.sleep(0.5)
        raise AssertionError("Timeout: " + description)

    event = {"specversion": "1.0", "type": "alerta.seguridad.valvula_ilicita",
             "source": "/petroandes/test", "id": run_id, "datacontenttype": "application/json",
             "data": {"tramo": "Tramo-Centro", "nivel_riesgo": "CRITICO",
                      "descripcion": "Prueba automatica Camel", "presion_actual_psi": 305,
                      "caudal_actual_bpd": 8050}}
    try:
        raw = json.dumps(event)
        publish(raw)
        wait_for(lambda: any(a["id_alerta"] == run_id and a["presion_psi"] == 305
                            and a["caudal_bpd"] == 8050 for a in state()["alertas_activas"]),
                 "alerta Kafka transformada y recibida por HTTP")
        publish(raw)
        # A following valid record acts as a barrier on this single-partition topic.
        barrier = json.loads(raw)
        barrier["id"] = run_id + "-barrier"
        publish(json.dumps(barrier))
        wait_for(lambda: any(a["id_alerta"] == barrier["id"] for a in state()["alertas_activas"]),
                 "Camel proceso el mensaje posterior al duplicado")
        assert sum(a["id_alerta"] == run_id for a in state()["alertas_activas"]) == 1
        print("OK: duplicado descartado", flush=True)

        invalid = "invalid-json-" + run_id
        unknown = json.loads(raw)
        unknown["id"] = run_id + "-404"
        unknown["data"]["tramo"] = "Tramo-Inexistente"
        unknown_raw = json.dumps(unknown)
        publish(invalid)
        publish(unknown_raw)
        pending = {invalid, unknown_raw}

        def dlq_received():
            msg = consumer.poll(0.5)
            if msg is not None:
                if msg.error():
                    raise AssertionError(msg.error())
                failure = json.loads(msg.value())
                original = failure.get("original_event")
                if original in pending:
                    assert failure["attempts"] == (0 if original == invalid else 1)
                    pending.remove(original)
            return not pending

        wait_for(dlq_received, "JSON invalido y HTTP 404 guardados en DLQ")
        print("INTEGRACION CORRECTA. IDs de prueba:", run_id, barrier["id"], flush=True)
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
