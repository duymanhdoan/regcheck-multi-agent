# Multi-stage build for MCP Server services
# Supports finance, hr, and legal servers via SERVER_TYPE build arg

FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy all source code
COPY src/ ./src/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Server type must be set at runtime
ENV SERVER_TYPE=""

# Expose MCP server port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8082/health')" || exit 1

# Run the appropriate server based on SERVER_TYPE
CMD if [ "$SERVER_TYPE" = "finance" ]; then \
      uvicorn src.finance.main:app --host 0.0.0.0 --port 8082; \
    elif [ "$SERVER_TYPE" = "hr" ]; then \
      uvicorn src.hr.main:app --host 0.0.0.0 --port 8082; \
    elif [ "$SERVER_TYPE" = "legal" ]; then \
      uvicorn src.legal.main:app --host 0.0.0.0 --port 8082; \
    else \
      echo "ERROR: SERVER_TYPE must be set to finance, hr, or legal" && exit 1; \
    fi
