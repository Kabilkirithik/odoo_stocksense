# ==============================================================================
# Multi-Stage Dockerfile for StockSense Java Authentication Service
# Optimized for minimal image size, enterprise security, and container performance
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Application Artifact
# ------------------------------------------------------------------------------
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /build

# Copy Maven wrapper and POM first to leverage Docker layer caching
COPY pom.xml mvnw ./
COPY .mvn .mvn/

# Grant execution permissions to Maven wrapper
RUN chmod +x mvnw

# Download dependencies (cached unless pom.xml changes)
RUN ./mvnw dependency:go-offline -B || true

# Copy source code
COPY src src/

# Build optimized production jar (skips tests during image build)
RUN ./mvnw clean package -DskipTests

# ------------------------------------------------------------------------------
# Stage 2: Minimal & Secure Production Runtime
# ------------------------------------------------------------------------------
FROM eclipse-temurin:21-jre-alpine AS runner

# Install wget for Docker healthcheck
RUN apk add --no-cache wget

# Create non-root system user and group for container security (Principle of Least Privilege)
RUN addgroup -S stocksense && adduser -S stocksense -G stocksense

WORKDIR /app

# Copy executable jar from builder stage
COPY --from=builder /build/target/*.jar app.jar

# Grant ownership to non-root user
RUN chown -R stocksense:stocksense /app

# Switch to non-root user
USER stocksense:stocksense

# Expose default HTTP port
EXPOSE 8081

# Container Healthcheck (pings /health endpoint every 30s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD wget -qO- http://localhost:8081/api/v1/auth/health || exit 1

# Optimized JVM memory flags for containers:
# - UseContainerSupport: Detects container cgroups memory limits
# - MaxRAMPercentage=75.0: Allocates up to 75% of container RAM to JVM heap
# - ExitOnOutOfMemoryError: Restarts container cleanly if OOM occurs
ENTRYPOINT ["java", \
  "-XX:+UseContainerSupport", \
  "-XX:MaxRAMPercentage=75.0", \
  "-XX:+ExitOnOutOfMemoryError", \
  "-Djava.security.egd=file:/dev/./urandom", \
  "-jar", "app.jar"]
