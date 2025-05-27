#!/usr/bin/with-contenv bashio

# Get configuration from add-on options
PORT=$(bashio::config 'port')
API_URL=$(bashio::config 'api_url')

# Update Nginx configuration with dynamic port
sed -i "s/listen 80;/listen $PORT;/" /etc/nginx/nginx.conf

# Log startup information
bashio::log.info "Starting Nodalink Frontend on port ${PORT}"
bashio::log.info "API URL configured as: ${API_URL}"

# Test nginx configuration
nginx -t

# Start Nginx
exec nginx -g "daemon off;"
