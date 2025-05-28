#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Community Add-on: Nodalink Core
# Starts both AppDaemon and FastAPI services with shared in-memory access
# ==============================================================================

# Get configuration options
TIME_ZONE=$(bashio::config 'time_zone')
API_PORT=$(bashio::config 'api_port')
API_HOST=$(bashio::config 'api_host')
SCENARIO_FILE=$(bashio::config 'scenario_file')
CONFIG_FILE=$(bashio::config 'config_file')
LOG_FILE=$(bashio::config 'log_file')
TEST_MODE=$(bashio::config 'test_mode')
CORS_ORIGINS=$(bashio::config 'cors_origins')

# Set environment variables for shared access
export TZ="${TIME_ZONE}"
export SCENARIO_FILE="${SCENARIO_FILE}"
export CONFIG_FILE="${CONFIG_FILE}"
export LOG_FILE="${LOG_FILE}"
export TEST_MODE="${TEST_MODE}"
export API_PORT="${API_PORT}"
export API_HOST="${API_HOST}"
export CORS_ORIGINS="${CORS_ORIGINS}"
export PYTHONPATH="/usr/share/nodalink-core/api:/usr/share/nodalink-core/apps:${PYTHONPATH}"

bashio::log.info "Starting Nodalink Core (Merged AppDaemon + FastAPI)..."
bashio::log.info "Time zone: ${TIME_ZONE}"
bashio::log.info "API host: ${API_HOST}"
bashio::log.info "API port: ${API_PORT}"
bashio::log.info "Scenario file: ${SCENARIO_FILE}"
bashio::log.info "Config file: ${CONFIG_FILE}"
bashio::log.info "Test mode: ${TEST_MODE}"
bashio::log.info "CORS origins: ${CORS_ORIGINS}"

# Create required directories
mkdir -p "$(dirname "${SCENARIO_FILE}")"
mkdir -p "$(dirname "${CONFIG_FILE}")"
mkdir -p "$(dirname "${LOG_FILE}")"
mkdir -p "/config/appdaemon/apps/Nodalink/logs"

# Ensure proper permissions
chmod -R 755 "/config/appdaemon/apps/Nodalink"

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:${port}/health" >/dev/null 2>&1; then
            bashio::log.info "${service_name} is healthy (attempt ${attempt}/${max_attempts})"
            return 0
        fi
        bashio::log.info "Waiting for ${service_name} to be ready (attempt ${attempt}/${max_attempts})..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    bashio::log.error "${service_name} failed to start within expected time"
    return 1
}

# Function to start FastAPI
start_fastapi() {
    bashio::log.info "Starting FastAPI server on ${API_HOST}:${API_PORT}..."
    cd /usr/share/nodalink-core/api
    exec /opt/venv/bin/python -m uvicorn main:app \
        --host "${API_HOST}" \
        --port "${API_PORT}" \
        --log-level info \
        --reload \
        --access-log
}

# Function to start AppDaemon
start_appdaemon() {
    bashio::log.info "Starting AppDaemon..."
    cd /usr/share/nodalink-core
    exec /opt/venv/bin/appdaemon -c /usr/share/nodalink-core
}

# Function to handle shutdown
cleanup() {
    bashio::log.info "Shutting down Nodalink Core..."
    # Kill background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    # Wait for graceful shutdown
    sleep 2
    # Force kill if needed
    jobs -p | xargs -r kill -9 2>/dev/null || true
    wait
    bashio::log.info "Nodalink Core shutdown complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGTERM SIGINT EXIT

# Start FastAPI first (AppDaemon will connect to it)
bashio::log.info "Step 1: Starting FastAPI server..."
start_fastapi &
FASTAPI_PID=$!

# Wait for FastAPI to be ready
sleep 5
if ! check_service_health "FastAPI" "${API_PORT}"; then
    bashio::log.error "FastAPI failed to start properly"
    exit 1
fi

# Start AppDaemon (it will connect to the shared state)
bashio::log.info "Step 2: Starting AppDaemon engine..."
start_appdaemon &
APPDAEMON_PID=$!

# Wait a bit for AppDaemon to initialize and connect
sleep 10

bashio::log.info "🚀 Nodalink Core started successfully!"
bashio::log.info "📊 FastAPI PID: ${FASTAPI_PID}"
bashio::log.info "🤖 AppDaemon PID: ${APPDAEMON_PID}"
bashio::log.info "🌐 API accessible at: http://${API_HOST}:${API_PORT}"
bashio::log.info "📝 WebSocket endpoint: ws://${API_HOST}:${API_PORT}/ws"
bashio::log.info "🔗 Shared in-memory state active for real-time synchronization"

# Monitor both processes
while true; do
    # Check if FastAPI is still running
    if ! kill -0 $FASTAPI_PID 2>/dev/null; then
        bashio::log.error "FastAPI process died, restarting..."
        start_fastapi &
        FASTAPI_PID=$!
        sleep 5
    fi
    
    # Check if AppDaemon is still running
    if ! kill -0 $APPDAEMON_PID 2>/dev/null; then
        bashio::log.error "AppDaemon process died, restarting..."
        start_appdaemon &
        APPDAEMON_PID=$!
        sleep 10
    fi
    
    sleep 30
done
