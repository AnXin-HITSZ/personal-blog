FROM qdrant/qdrant:v1.12.5

USER root
RUN apk add --no-cache curl
USER qdrant

HEALTHCHECK --start-period=30s --interval=15s --timeout=10s --retries=3 \
  CMD curl -sf http://localhost:6333/healthz || exit 1
