FROM openjdk:17-jdk-slim

WORKDIR /app

# Gradle 빌드를 위한 파일 복사
COPY gradlew .
COPY gradle gradle
COPY build.gradle .
COPY settings.gradle .
COPY src src

# 빌드 권한 부여 및 빌드
RUN chmod +x ./gradlew
RUN ./gradlew bootJar

# JAR 파일 실행
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "build/libs/*.jar"]