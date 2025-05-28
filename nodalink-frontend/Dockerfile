ARG BUILD_FROM
FROM $BUILD_FROM

# Install Node.js and nginx with specific versions for stability
RUN apk add --no-cache \
    nodejs>=18 \
    npm \
    nginx \
    curl \
    python3 \
    make \
    g++ \
    git \
    && rm -rf /var/cache/apk/*

# Set environment variables for Node.js
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV CYPRESS_INSTALL_BINARY=0
ENV HUSKY_SKIP_INSTALL=1

# Set working directory for build
WORKDIR /build

# Copy package files first (for better Docker caching)
COPY frontend/package*.json ./

# Install dependencies with production optimizations
RUN npm ci --no-audit --no-fund --prefer-offline

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
