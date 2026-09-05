FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn -B package

FROM eclipse-temurin:21-jre-jammy
WORKDIR /app
COPY --from=build /build/target/enrutador-camel.jar ./app.jar
USER 10001
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
