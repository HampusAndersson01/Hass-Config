ARG BUILD_FROM
FROM $BUILD_FROM

# Install base packages and bashio
RUN apk add --no-cache \
    python3 \
    python3-dev \
    gcc \
    musl-dev \
    curl \
    netcat-openbsd \
    bash \
    jq \
    git \
    && rm -rf /var/cache/apk/*

# Install bashio for proper Home Assistant add-on logging
# Use multiple fallback methods for better reliability
RUN set -e && \
    (git clone --depth 1 --branch v0.16.2 https://github.com/hassio-addons/bashio.git /tmp/bashio || \
     git clone --depth 1 https://github.com/hassio-addons/bashio.git /tmp/bashio || \
     { mkdir -p /tmp/bashio && \
       curl -fsSL https://github.com/hassio-addons/bashio/archive/refs/heads/main.tar.gz | \
       tar -xz --strip-components=1 -C /tmp/bashio; }) && \
    mkdir -p /usr/lib/bashio && \
    cp -r /tmp/bashio/lib/* /usr/lib/bashio/ && \
    ln -sf /usr/lib/bashio/bashio /usr/bin/bashio && \
    chmod +x /usr/bin/bashio && \
    rm -rf /tmp/bashio

# Create Python virtual environment and activate it
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel

# Install Python dependencies for merged AppDaemon + FastAPI in virtual environment
RUN /opt/venv/bin/pip install --no-cache-dir \
    appdaemon==4.4.2 \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    websockets==12.0 \
    pyyaml \
    jinja2 \
    aiofiles \
    python-multipart

# Update PATH to use virtual environment binaries
ENV PATH="/opt/venv/bin:$PATH"

# Create unified directory structure
RUN mkdir -p /usr/share/nodalink-core/apps \
    && mkdir -p /usr/share/nodalink-core/api \
    && mkdir -p /config/appdaemon/apps/Nodalink/logs

# Copy AppDaemon configuration
COPY appdaemon.yaml /usr/share/nodalink-core/

# Copy merged application files
COPY apps/ /usr/share/nodalink-core/apps/
COPY api/ /usr/share/nodalink-core/api/

# Ensure scenario_utils.py is available in both locations for imports
RUN cp /usr/share/nodalink-core/apps/scenario_utils.py /usr/share/nodalink-core/api/

# Copy startup script
COPY run.sh /
RUN chmod a+x /run.sh

# Set working directory
WORKDIR /usr/share/nodalink-core

# Health check for both AppDaemon and FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8002/health && nc -z localhost 5050 || exit 1

# Labels for Home Assistant add-on
LABEL \
    io.hass.name="Nodalink Core" \
    io.hass.description="Combined AppDaemon + FastAPI core engine for Nodalink" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386" \
    io.hass.type="addon" \
    io.hass.version="1.0.0"

# Start both services
CMD [ "/run.sh" ]
