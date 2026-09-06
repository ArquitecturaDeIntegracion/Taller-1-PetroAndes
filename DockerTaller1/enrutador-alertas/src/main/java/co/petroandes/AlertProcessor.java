package co.petroandes;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import org.apache.camel.Exchange;
import org.apache.camel.Processor;
import org.apache.camel.ProducerTemplate;
import org.apache.camel.component.kafka.KafkaConstants;
import org.apache.camel.component.kafka.consumer.KafkaManualCommit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class AlertProcessor implements Processor {
    private static final Logger LOG = LoggerFactory.getLogger(AlertProcessor.class);
    private final ObjectMapper json = new ObjectMapper();
    private final ProducerTemplate producer;
    private final String http;
    private final String dlq;
    private final long retryDelayMs;

    public AlertProcessor(ProducerTemplate producer, String http, String dlq, long retryDelayMs) {
        this.producer = producer;
        this.http = http;
        this.dlq = dlq;
        this.retryDelayMs = retryDelayMs;
    }

    @Override
    public void process(Exchange exchange) throws Exception {
        String raw = exchange.getMessage().getBody(String.class);
        KafkaManualCommit commit = exchange.getMessage().getHeader(KafkaConstants.MANUAL_COMMIT, KafkaManualCommit.class);
        if (commit == null) {
            throw new IllegalStateException("Falta confirmacion manual de Kafka");
        }
        ObjectNode mapped;
        try {
            mapped = mapAlert(raw);
        } catch (Exception invalid) {
            deadLetter(exchange, raw, "Evento invalido: " + invalid.getMessage(), 0);
            commit.commit();
            return;
        }

        String body = json.writeValueAsString(mapped);
        String error = "";
        int attempts = 0;
        for (int attempt = 1; attempt <= 4; attempt++) {
            attempts = attempt;
            // Separate exchange prevents Kafka/internal headers from reaching the HTTP API.
            Exchange response = producer.request(http, request -> {
                request.getMessage().setBody(body);
                request.getMessage().setHeader(Exchange.CONTENT_TYPE, "application/json");
            });
            Integer status = response.getMessage().getHeader(Exchange.HTTP_RESPONSE_CODE, Integer.class);
            if (response.getException() == null && status != null && status >= 200 && status < 300) {
                commit.commit();
                LOG.info("Alerta {} entregada a balance; offset confirmado", mapped.path("id_alerta").asText());
                return;
            }
            error = response.getException() != null
                ? response.getException().toString() : "HTTP " + status;
            LOG.warn("Entrega fallida, intento {}/4: {}", attempt, error);
            boolean transientFailure = response.getException() != null || status == null
                || status == 408 || status == 429 || status >= 500;
            if (!transientFailure || attempt == 4) {
                break;
            }
            // Keep delivery and commit on the Kafka consumer thread.
            Thread.sleep(retryDelayMs * (1L << (attempt - 1)));
        }
        deadLetter(exchange, raw, error, attempts);
        commit.commit();
    }

    ObjectNode mapAlert(String raw) throws Exception {
        JsonNode event = json.readTree(raw);
        if (event == null || !event.isObject()
            || !"1.0".equals(event.path("specversion").asText())
            || !"alerta.seguridad.valvula_ilicita".equals(event.path("type").asText())
            || !"application/json".equals(event.path("datacontenttype").asText())) {
            throw new IllegalArgumentException("CloudEvent de alerta no valido");
        }
        text(event, "source");
        ObjectNode mapped = json.createObjectNode();
        mapped.put("id_alerta", text(event, "id"));
        JsonNode data = event.path("data");
        for (String field : new String[]{"tramo", "nivel_riesgo", "descripcion"}) {
            mapped.put(field, text(data, field));
        }
        if (!java.util.Set.of("CRITICO", "ALTO", "MEDIO", "BAJO").contains(mapped.path("nivel_riesgo").asText())) {
            throw new IllegalArgumentException("nivel_riesgo no valido");
        }
        mapped.put("presion_psi", number(data, "presion_actual_psi"));
        mapped.put("caudal_bpd", number(data, "caudal_actual_bpd"));
        return mapped;
    }

    private String text(JsonNode node, String field) {
        JsonNode value = node.path(field);
        if (!value.isTextual() || value.asText().isBlank()) {
            throw new IllegalArgumentException("Campo requerido: " + field);
        }
        return value.asText();
    }

    private double number(JsonNode node, String field) {
        JsonNode value = node.path(field);
        if (!value.isNumber() || !Double.isFinite(value.asDouble()) || value.asDouble() < 0) {
            throw new IllegalArgumentException("Numero no valido: " + field);
        }
        return value.asDouble();
    }

    private void deadLetter(Exchange original, String raw, String reason, int attempts) throws Exception {
        ObjectNode failure = json.createObjectNode();
        failure.put("original_event", raw);
        failure.put("error", reason);
        failure.put("attempts", attempts);
        failure.put("failed_at", Instant.now().toString());
        failure.put("topic", original.getMessage().getHeader(KafkaConstants.TOPIC, String.class));
        failure.put("partition", original.getMessage().getHeader(KafkaConstants.PARTITION, String.class));
        failure.put("offset", original.getMessage().getHeader(KafkaConstants.OFFSET, String.class));
        // sendBody propagates failure; synchronous Kafka waits for broker acknowledgement.
        producer.sendBody(dlq, json.writeValueAsString(failure));
        LOG.warn("Alerta enviada a it-alertas-dlq: {}", reason);
    }
}
