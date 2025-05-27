#!/usr/bin/with-contenv bashio

# Get configuration from add-on options
PORT=$(bashio::config 'port')
HOST=$(bashio::config 'host')
SCENARIO_FILE=$(bashio::config 'scenario_file')
CONFIG_FILE=$(bashio::config 'config_file')
LOG_FILE=$(bashio::config 'log_file')

# Set environment variables
export SCENARIO_FILE="$SCENARIO_FILE"
export CONFIG_FILE="$CONFIG_FILE"
export LOG_FILE="$LOG_FILE"

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Start the FastAPI server
bashio::log.info "Starting Nodalink API server on ${HOST}:${PORT}"

cd /app
exec uvicorn main:app --host "$HOST" --port "$PORT" --log-level info
