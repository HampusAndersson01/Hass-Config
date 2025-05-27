ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.1
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY scenario_utils.py .
COPY run.sh /

# Create necessary directories
RUN mkdir -p /data \
    && chmod a+x /run.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Set entrypoint
ENTRYPOINT ["/run.sh"]
