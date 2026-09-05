package co.petroandes;

import org.apache.camel.builder.RouteBuilder;
import org.apache.camel.main.Main;

public final class RouterApplication {
    public static void main(String[] args) throws Exception {
        Main main = new Main();
        main.configure().addRoutesBuilder(new RouteBuilder() {
            @Override
            public void configure() {
                // A failed DLQ publication or commit must return to Kafka without advancing.
                errorHandler(noErrorHandler());
                String brokers = env("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092");
                String input = "kafka:it-alertas-topic?brokers=" + brokers
                    + "&groupId=grupo-enrutador-balance&autoOffsetReset=earliest"
                    + "&autoCommitEnable=false&allowManualCommit=true&breakOnFirstError=true"
                    + "&maxPollRecords=1&maxPollIntervalMs=300000";
                String http = env("API_URL", "http://sistema-balance:8000/alertas")
                    + "?httpMethod=POST&throwExceptionOnFailure=false&followRedirects=false"
                    + "&connectTimeout=5000&responseTimeout=10000&automaticRetriesDisabled=true";
                String dlq = "kafka:it-alertas-dlq?brokers=" + brokers
                    + "&requestRequiredAcks=all&synchronous=true"
                    + "&maxBlockMs=10000&deliveryTimeoutMs=30000&requestTimeoutMs=10000";
                from(input).routeId("alertas-hacia-balance")
                    .process(new AlertProcessor(getContext().createProducerTemplate(), http, dlq, 2000));
            }
        });
        main.run(args);
    }

    private static String env(String name, String fallback) {
        return System.getenv().getOrDefault(name, fallback);
    }
}
