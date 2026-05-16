# ============================================
# Stage 1: Build Backend JAR with Maven
# ============================================
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY backend/pom.xml .
COPY backend/src ./src
COPY backend/.mvn ./.mvn
COPY backend/mvnw .
COPY backend/settings.xml /root/.m2/settings.xml

# 使用阿里云 Maven 镜像加速国内构建
RUN mvn clean package -DskipTests -B -T 2C

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
