# Dockerfile for Langflow Frontend with Custom Components
FROM langflowai/langflow:latest

# Set working directory
WORKDIR /app

# Install additional dependencies if needed
RUN pip install --no-cache-dir \
    httpx \
    boto3

# Copy custom Langflow components
COPY langflow_components /app/langflow_components

# Set environment variable for custom components path
ENV LANGFLOW_COMPONENTS_PATH=/app/langflow_components

# Expose Langflow port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Use the default Langflow entrypoint
CMD ["langflow", "run", "--host", "0.0.0.0", "--port", "7860"]
