# ============================================
# Stage 1: Build Backend JAR with Maven
# ============================================
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY backend/pom.xml .
COPY backend/src ./src
COPY backend/.mvn ./.mvn
COPY backend/mvnw .

RUN mvn clean package -DskipTests -B

# ============================================
# Stage 2: Run JAR with JRE
# ============================================
FROM eclipse-temurin:17-jre

WORKDIR /app
COPY --from=builder /build/target/*.jar app.jar

# 使用环境变量覆盖 application.yml 中的配置
ENV DB_USERNAME=${DB_USERNAME}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENV JWT_EXPIRATION=${JWT_EXPIRATION}

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
