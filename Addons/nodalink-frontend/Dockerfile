ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.1
FROM $BUILD_FROM

# Install Node.js and nginx
RUN apk add --no-cache \
    nodejs \
    npm \
    nginx \
    curl \
    && rm -rf /var/cache/apk/*

# Set working directory for build
WORKDIR /build

# Copy package.json and install dependencies
COPY frontend/package.json .
RUN npm install

# Copy frontend source code
COPY frontend/ .

# Build the Vue.js application
RUN npm run build

# Set up Nginx
RUN mkdir -p /var/www/html
RUN cp -r dist/* /var/www/html/

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY run.sh /

# Create necessary directories and set permissions
RUN mkdir -p /var/log/nginx \
    && mkdir -p /var/tmp/nginx \
    && mkdir -p /run/nginx \
    && chmod a+x /run.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Clean up build files
RUN rm -rf /build

# Set entrypoint
ENTRYPOINT ["/run.sh"]
