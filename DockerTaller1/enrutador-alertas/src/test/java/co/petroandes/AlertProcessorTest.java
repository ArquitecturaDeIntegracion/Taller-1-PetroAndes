package co.petroandes;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.apache.camel.Exchange;
import org.apache.camel.ProducerTemplate;
import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.component.kafka.KafkaConstants;
import org.apache.camel.component.kafka.consumer.KafkaManualCommit;
import org.apache.camel.impl.DefaultCamelContext;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AlertProcessorTest {
    private static final String VALID = """
        {"specversion":"1.0","type":"alerta.seguridad.valvula_ilicita",
         "source":"/petroandes/it/detector","datacontenttype":"application/json","id":"test-id",
         "data":{"tramo":"Tramo-Centro","nivel_riesgo":"CRITICO","descripcion":"Prueba",
         "presion_actual_psi":305,"caudal_actual_bpd":8050}}
        """;
    private DefaultCamelContext context;
    private ProducerTemplate producer;
    private final AtomicInteger requests = new AtomicInteger();
    private final AtomicInteger commits = new AtomicInteger();
    private final AtomicReference<String> failure = new AtomicReference<>();
    private final AtomicReference<String> received = new AtomicReference<>();
    private int status = 200;
    private int failFirst = 0;
    private boolean dlqBroken = false;
    private boolean networkBroken = false;

    @BeforeEach
    void setup() throws Exception {
        context = new DefaultCamelContext();
        producer = context.createProducerTemplate();
        context.addRoutes(new RouteBuilder() {
            public void configure() {
                errorHandler(noErrorHandler());
                from("direct:http").process(e -> {
                    received.set(e.getMessage().getBody(String.class));
                    int count = requests.incrementAndGet();
                    if (networkBroken) throw new java.io.IOException("Conexion interrumpida");
                    e.getMessage().setHeader(Exchange.HTTP_RESPONSE_CODE, count <= failFirst ? 503 : status);
                });
                from("direct:dlq").process(e -> {
                    if (dlqBroken) throw new IllegalStateException("Broker caido");
                    failure.set(e.getMessage().getBody(String.class));
                    assertEquals(0, commits.get(), "No confirmar antes de guardar en DLQ");
                });
                from("direct:input").process(new AlertProcessor(producer, "direct:http", "direct:dlq", 0));
            }
        });
        context.start();
    }

    @AfterEach
    void close() throws Exception {
        producer.stop();
        context.stop();
    }

    private Exchange send(String body) {
        return producer.request("direct:input", e -> {
            e.getMessage().setBody(body);
            e.getMessage().setHeader(KafkaConstants.MANUAL_COMMIT, (KafkaManualCommit) () -> commits.incrementAndGet());
        });
    }

    @Test void mapsAndCommitsSuccessfulDelivery() throws Exception {
        assertNull(send(VALID).getException());
        var body = new ObjectMapper().readTree(received.get());
        assertEquals("test-id", body.path("id_alerta").asText());
        assertEquals(305, body.path("presion_psi").asInt());
        assertEquals(8050, body.path("caudal_bpd").asInt());
        assertEquals(6, body.size());
        assertEquals(1, commits.get());
        assertNull(failure.get());
    }

    @Test void retriesTransientFailure() {
        failFirst = 2;
        assertNull(send(VALID).getException());
        assertEquals(3, requests.get());
        assertEquals(1, commits.get());
        assertNull(failure.get());
    }

    @Test void sendsPermanentHttpFailureWithoutRetry() {
        status = 422;
        assertNull(send(VALID).getException());
        assertEquals(1, requests.get());
        assertNotNull(failure.get());
        assertEquals(1, commits.get());
    }

    @Test void preservesMalformedOriginalInDlq() throws Exception {
        assertNull(send("not-json").getException());
        assertEquals("not-json", new ObjectMapper().readTree(failure.get()).path("original_event").asText());
        assertEquals(0, requests.get());
        assertEquals(1, commits.get());
    }

    @Test void exhaustedNetworkFailureGoesToDlq() {
        networkBroken = true;
        assertNull(send(VALID).getException());
        assertEquals(4, requests.get());
        assertNotNull(failure.get());
        assertEquals(1, commits.get());
    }

    @Test void failedDlqDoesNotCommit() {
        dlqBroken = true;
        assertNotNull(send("not-json").getException());
        assertEquals(0, commits.get());
    }
}
