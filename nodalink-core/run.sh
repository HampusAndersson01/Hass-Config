#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Community Add-on: Nodalink Core
# Starts both AppDaemon and FastAPI services with shared in-memory access
# ==============================================================================

# Set default values in case config fails to load
declare TIME_ZONE="UTC"
declare API_PORT="8002"
declare API_HOST="0.0.0.0"
declare SCENARIO_FILE="/config/appdaemon/apps/Nodalink/scenarios.json"
declare CONFIG_FILE="/config/appdaemon/apps/Nodalink/config.json"
declare LOG_FILE="/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log"
declare TEST_MODE="false"
declare CORS_ORIGINS="*"

# Get configuration options
TIME_ZONE=$(bashio::config 'time_zone')
API_PORT=$(bashio::config 'api_port')
API_HOST=$(bashio::config 'api_host')
SCENARIO_FILE=$(bashio::config 'scenario_file')
CONFIG_FILE=$(bashio::config 'config_file')
LOG_FILE=$(bashio::config 'log_file')
TEST_MODE=$(bashio::config 'test_mode')

# Handle CORS origins with proper JSON parsing
CORS_RAW=$(bashio::config 'cors_origins')
# Handle the case where it's a JSON array vs a single string
if [[ "${CORS_RAW}" == "[" ]]; then
    # It's a JSON array, get the first element as a default
    CORS_ORIGINS=$(bashio::config 'cors_origins[0]')
else
    # It's either a single string value or not specified
    CORS_ORIGINS="${CORS_RAW:-*}"
fi

# Set environment variables for shared access
export TZ="${TIME_ZONE:-UTC}"
export SCENARIO_FILE="${SCENARIO_FILE:-/config/appdaemon/apps/Nodalink/scenarios.json}"
export CONFIG_FILE="${CONFIG_FILE:-/config/appdaemon/apps/Nodalink/config.json}"
export LOG_FILE="${LOG_FILE:-/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log}"
export TEST_MODE="${TEST_MODE:-false}"
export API_PORT="${API_PORT:-8002}"
export API_HOST="${API_HOST:-0.0.0.0}"
export CORS_ORIGINS="${CORS_ORIGINS:-*}"
export PYTHONPATH="/usr/share/nodalink-core/api:/usr/share/nodalink-core/apps:${PYTHONPATH:-}"

bashio::log.info "Starting Nodalink Core (Merged AppDaemon + FastAPI)..."
bashio::log.info "Time zone: ${TIME_ZONE}"
bashio::log.info "API host: ${API_HOST}"
bashio::log.info "API port: ${API_PORT}"
bashio::log.info "Scenario file: ${SCENARIO_FILE}"
bashio::log.info "Config file: ${CONFIG_FILE}"
bashio::log.info "Test mode: ${TEST_MODE}"
bashio::log.info "CORS origins: ${CORS_ORIGINS}"

# Create required directories with error handling for each
mkdir -p "$(dirname "${SCENARIO_FILE}")" || {
    bashio::log.error "Failed to create directory: $(dirname "${SCENARIO_FILE}")"
    exit 1
}

mkdir -p "$(dirname "${CONFIG_FILE}")" || {
    bashio::log.error "Failed to create directory: $(dirname "${CONFIG_FILE}")"
    exit 1
}

mkdir -p "$(dirname "${LOG_FILE}")" || {
    bashio::log.error "Failed to create directory: $(dirname "${LOG_FILE}")"
    exit 1
}

bashio::log.debug "Created required directories"

# Ensure proper permissions
chmod -R 755 "/config/appdaemon/apps/Nodalink" || {
    bashio::log.warning "Could not set permissions on /config/appdaemon/apps/Nodalink"
}

# Function to check if a service is healthy
check_service_health() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    local wait_time=2
    
    bashio::log.info "Checking if ${service_name} is available on port ${port}..."
    
    while [ "$attempt" -le "$max_attempts" ]; do
        if nc -z localhost "$port" >/dev/null 2>&1; then
            bashio::log.info "${service_name} is responding on port ${port} (attempt ${attempt}/${max_attempts})"
            return 0
        fi
        
        # Increase wait time for subsequent checks (exponential backoff with cap)
        if [ "$wait_time" -lt 10 ]; then
            wait_time=$((wait_time * 1.5))
        fi
        
        bashio::log.info "Waiting for ${service_name} to be ready (attempt ${attempt}/${max_attempts})..."
        sleep $wait_time
        attempt=$((attempt + 1))
    done
    
    bashio::log.error "${service_name} failed to start within expected time"
    return 1
}

# Function to start FastAPI
start_fastapi() {
    bashio::log.info "Starting FastAPI server on ${API_HOST}:${API_PORT}..."
    
    # Use absolute paths instead of cd for better reliability
    # Remove exec as we need to return from this function
    /opt/venv/bin/python -m uvicorn main:app \
        --host "${API_HOST}" \
        --port "${API_PORT}" \
        --log-level info \
        --reload \
        --access-log \
        --app-dir /usr/share/nodalink-core/api
}

# Function to start AppDaemon
start_appdaemon() {
    bashio::log.info "Starting AppDaemon..."
    
    # Use absolute paths instead of cd for better reliability
    # Remove exec as we need to return from this function
    /opt/venv/bin/appdaemon -c /usr/share/nodalink-core
}

# Function to handle shutdown
cleanup() {
    bashio::log.info "Shutting down Nodalink Core..."
    
    # Explicitly kill processes by PID if they exist
    if [[ -n "${FASTAPI_PID:-}" ]]; then
        kill "${FASTAPI_PID}" 2>/dev/null || true
        bashio::log.info "Sent shutdown signal to FastAPI (PID: ${FASTAPI_PID})"
    fi
    
    if [[ -n "${APPDAEMON_PID:-}" ]]; then
        kill "${APPDAEMON_PID}" 2>/dev/null || true
        bashio::log.info "Sent shutdown signal to AppDaemon (PID: ${APPDAEMON_PID})"
    fi
    
    # Also clean up any other background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Wait for graceful shutdown
    sleep 2
    
    # Force kill if needed
    if [[ -n "${FASTAPI_PID:-}" ]] && kill -0 "${FASTAPI_PID}" 2>/dev/null; then
        kill -9 "${FASTAPI_PID}" 2>/dev/null || true
        bashio::log.warning "Had to force kill FastAPI process"
    fi
    
    if [[ -n "${APPDAEMON_PID:-}" ]] && kill -0 "${APPDAEMON_PID}" 2>/dev/null; then
        kill -9 "${APPDAEMON_PID}" 2>/dev/null || true
        bashio::log.warning "Had to force kill AppDaemon process"
    fi
    
    # Make sure any remaining jobs are killed
    jobs -p | xargs -r kill -9 2>/dev/null || true
    wait
    
    bashio::log.info "Nodalink Core shutdown complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGTERM SIGINT EXIT

# Additional sanity checks before starting services
if ! command -v nc >/dev/null 2>&1; then
    bashio::log.warning "netcat not found, installing for health checks..."
    apk add --no-cache netcat-openbsd
fi

# Check Python environment
if ! command -v /opt/venv/bin/python >/dev/null 2>&1; then
    bashio::log.error "Python virtual environment not found at /opt/venv"
    exit 1
fi

# Check if ports are already in use (avoid port conflicts)
if nc -z localhost "${API_PORT}" >/dev/null 2>&1; then
    bashio::log.warning "Port ${API_PORT} is already in use. Check for conflicting services."
fi

if nc -z localhost "5050" >/dev/null 2>&1; then
    bashio::log.warning "Port 5050 (AppDaemon) is already in use. Check for conflicting services."
fi

# Start FastAPI first (AppDaemon will connect to it)
bashio::log.info "Step 1: Starting FastAPI server..."
start_fastapi &
FASTAPI_PID=$!

# Wait for FastAPI to be ready with proper error handling
sleep 5
if ! check_service_health "FastAPI" "${API_PORT}"; then
    bashio::log.error "FastAPI failed to start properly. Check the API configuration and port availability."
    cleanup
    exit 1
fi

# Start AppDaemon (it will connect to the shared state)
bashio::log.info "Step 2: Starting AppDaemon engine..."
start_appdaemon &
APPDAEMON_PID=$!

# Wait with better checking for AppDaemon
sleep 5
if ! nc -z localhost 5050 >/dev/null 2>&1; then
    bashio::log.warning "AppDaemon admin interface not responding yet, waiting a bit longer..."
    sleep 10
fi

bashio::log.info "-------------------------------------------"
bashio::log.info "🚀 Nodalink Core started successfully!"
bashio::log.info "📊 FastAPI PID: ${FASTAPI_PID}"
bashio::log.info "🤖 AppDaemon PID: ${APPDAEMON_PID}"
bashio::log.info "🌐 API accessible at: http://${API_HOST}:${API_PORT}"
bashio::log.info "📝 WebSocket endpoint: ws://${API_HOST}:${API_PORT}/ws"
bashio::log.info "🔗 Shared in-memory state active for real-time synchronization"
bashio::log.info "-------------------------------------------"

# Record successful startup in the add-on's persistent data
mkdir -p /data/nodalink
echo "$(date +%Y-%m-%d\ %H:%M:%S) - Nodalink Core started successfully" >> /data/nodalink/startup_history.log

# Monitor both processes with restart limits to prevent rapid cycling
declare -i fastapi_restarts=0
declare -i appdaemon_restarts=0
declare -i max_restarts=5
declare -i restart_reset_time=3600  # 1 hour in seconds
declare -i last_restart_reset=$(date +%s)

while true; do
    current_time=$(date +%s)
    
    # Reset restart counters after the specified time
    if [ $((current_time - last_restart_reset)) -ge $restart_reset_time ]; then
        if [ $fastapi_restarts -gt 0 ] || [ $appdaemon_restarts -gt 0 ]; then
            bashio::log.info "Resetting restart counters (FastAPI: ${fastapi_restarts}, AppDaemon: ${appdaemon_restarts})"
            fastapi_restarts=0
            appdaemon_restarts=0
        fi
        last_restart_reset=$current_time
    fi
    
    # Check if FastAPI is still running
    if ! kill -0 "$FASTAPI_PID" 2>/dev/null; then
        fastapi_restarts=$((fastapi_restarts + 1))
        
        if [ $fastapi_restarts -le $max_restarts ]; then
            bashio::log.error "FastAPI process died, restarting... (Restart ${fastapi_restarts}/${max_restarts})"
            start_fastapi &
            FASTAPI_PID=$!
            sleep 5
        else
            bashio::log.error "FastAPI restarted too many times (${fastapi_restarts}). Please check the logs for errors."
            bashio::log.error "Continuing to monitor but not restarting FastAPI until the reset period."
        fi
    fi
    
    # Check if AppDaemon is still running
    if ! kill -0 "$APPDAEMON_PID" 2>/dev/null; then
        appdaemon_restarts=$((appdaemon_restarts + 1))
        
        if [ $appdaemon_restarts -le $max_restarts ]; then
            bashio::log.error "AppDaemon process died, restarting... (Restart ${appdaemon_restarts}/${max_restarts})"
            start_appdaemon &
            APPDAEMON_PID=$!
            sleep 10
        else
            bashio::log.error "AppDaemon restarted too many times (${appdaemon_restarts}). Please check the logs for errors."
            bashio::log.error "Continuing to monitor but not restarting AppDaemon until the reset period."
        fi
    fi
    
    # Make sure we don't consume too much CPU with constant checks
    sleep 30
done
