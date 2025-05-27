ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.1
FROM $BUILD_FROM

# Install base packages
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    gcc \
    musl-dev \
    curl \
    && rm -rf /var/cache/apk/*

# Install AppDaemon
RUN pip3 install --no-cache-dir \
    appdaemon==4.4.2 \
    pyyaml \
    jinja2

# Copy add-on files
COPY run.sh /
COPY apps/ /usr/share/appdaemon/apps/
COPY appdaemon.yaml /usr/share/appdaemon/

# Create necessary directories
RUN mkdir -p /config/appdaemon/apps/Nodalink/logs \
    && chmod a+x /run.sh

# Set working directory
WORKDIR /usr/share/appdaemon

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD nc -z localhost 5050 || exit 1

# Start AppDaemon
CMD [ "/run.sh" ]
