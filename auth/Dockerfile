# syntax=docker/dockerfile:1

FROM eclipse-temurin:17-jdk-jammy AS build
WORKDIR /app

COPY gradlew gradlew.bat ./
COPY gradle/wrapper gradle/wrapper
RUN chmod +x gradlew

COPY build.gradle settings.gradle ./
COPY src src

RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app

RUN groupadd --system --gid 10001 app \
	&& useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=build /app/build/libs/auth-*-SNAPSHOT.jar /app/app.jar

USER 10001

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
