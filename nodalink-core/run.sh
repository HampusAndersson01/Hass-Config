#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Community Add-on: Nodalink Core
# Starts both AppDaemon and FastAPI services with shared in-memory access
# ==============================================================================

# Source bashio library functions
# shellcheck disable=SC1091
source /usr/lib/bashio/bashio.sh

# Robust logging functions with bashio fallback
log_info() {
    if command -v bashio::log.info >/dev/null 2>&1; then
        bashio::log.info "$@"
    else
        echo "[INFO] $*" >&2
    fi
}

log_notice() {
    if command -v bashio::log.notice >/dev/null 2>&1; then
        bashio::log.notice "$@"
    else
        echo "[NOTICE] $*" >&2
    fi
}

log_warning() {
    if command -v bashio::log.warning >/dev/null 2>&1; then
        bashio::log.warning "$@"
    else
        echo "[WARNING] $*" >&2
    fi
}

log_error() {
    if command -v bashio::log.error >/dev/null 2>&1; then
        bashio::log.error "$@"
    else
        echo "[ERROR] $*" >&2
    fi
}

log_fatal() {
    if command -v bashio::log.fatal >/dev/null 2>&1; then
        bashio::log.fatal "$@"
    else
        echo "[FATAL] $*" >&2
    fi
    exit 1
}

# Get config with fallback
get_config() {
    local key="$1"
    local default="$2"
    
    if command -v bashio::config >/dev/null 2>&1; then
        local value
        value=$(bashio::config "$key" 2>/dev/null)
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

log_notice "🚀 Starting Nodalink Core add-on..."

# Set default values in case config fails to load
declare TIME_ZONE="UTC"
declare API_PORT="8002"
declare API_HOST="0.0.0.0"
declare SCENARIO_FILE="/config/appdaemon/apps/Nodalink/scenarios.json"
declare CONFIG_FILE="/config/appdaemon/apps/Nodalink/config.json"
declare LOG_FILE="/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log"
declare TEST_MODE="false"
declare CORS_ORIGINS="*"

# Get configuration options with robust fallbacks
TIME_ZONE=$(get_config 'time_zone' 'UTC')
API_PORT=$(get_config 'api_port' '8002')
API_HOST=$(get_config 'api_host' '0.0.0.0')
SCENARIO_FILE=$(get_config 'scenario_file' '/config/appdaemon/apps/Nodalink/scenarios.json')
CONFIG_FILE=$(get_config 'config_file' '/config/appdaemon/apps/Nodalink/config.json')
LOG_FILE=$(get_config 'log_file' '/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log')
TEST_MODE=$(get_config 'test_mode' 'false')

# Handle CORS origins with proper parsing
if command -v bashio::config.exists >/dev/null 2>&1 && bashio::config.exists 'cors_origins'; then
    if bashio::config.is_array 'cors_origins'; then
        # It's a JSON array, convert to comma-separated string for CORS middleware
        CORS_ORIGINS=$(bashio::config 'cors_origins | join(",")')
        # If empty, set default
        [ -z "$CORS_ORIGINS" ] && CORS_ORIGINS="*"
    else
        # It's a string option
        CORS_ORIGINS=$(bashio::config 'cors_origins')
    fi
else
    # Not specified or bashio not available
    CORS_ORIGINS="*" 
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

log_info "Starting Nodalink Core (Merged AppDaemon + FastAPI)..."
log_info "Time zone: ${TIME_ZONE}"
log_info "API host: ${API_HOST}"
log_info "API port: ${API_PORT}"
log_info "Scenario file: ${SCENARIO_FILE}"
log_info "Config file: ${CONFIG_FILE}"
log_info "Test mode: ${TEST_MODE}"
log_info "CORS origins: ${CORS_ORIGINS}"

# Create required directories with error handling for each
mkdir -p "$(dirname "${SCENARIO_FILE}")" || {
    log_error "Failed to create directory: $(dirname "${SCENARIO_FILE}")"
    exit 1
}

mkdir -p "$(dirname "${CONFIG_FILE}")" || {
    log_error "Failed to create directory: $(dirname "${CONFIG_FILE}")"
    exit 1
}

mkdir -p "$(dirname "${LOG_FILE}")" || {
    log_error "Failed to create directory: $(dirname "${LOG_FILE}")"
    exit 1
}

log_info "Created required directories"

# Ensure proper permissions
chmod -R 755 "/config/appdaemon/apps/Nodalink" || {
    log_warning "Could not set permissions on /config/appdaemon/apps/Nodalink"
}

# Function to check if a service is healthy
check_service_health() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    local wait_time=2
    
    log_info "Checking if ${service_name} is available on port ${port}..."
    
    while [ "$attempt" -le "$max_attempts" ]; do
        if nc -z localhost "$port" >/dev/null 2>&1; then
            log_info "${service_name} is responding on port ${port} (attempt ${attempt}/${max_attempts})"
            return 0
        fi
        
        # Exponential backoff with cap at 10s
        wait_time=$((wait_time < 10 ? wait_time * 2 : 10))
        
        # Use notice level instead of info for better visibility
        log_notice "Waiting for ${service_name} to be ready (attempt ${attempt}/${max_attempts}, next check in ${wait_time}s)..."
        sleep "$wait_time"
        attempt=$((attempt + 1))
    done
    
    log_error "${service_name} failed to start within expected time"
    return 1
}

# Function to start FastAPI
start_fastapi() {
    log_info "Starting FastAPI server on ${API_HOST}:${API_PORT}..."
    
    cd /usr/share/nodalink-core/api || {
        log_error "Failed to change directory to /usr/share/nodalink-core/api"
        return 1
    }
    
    # Use absolute paths for better reliability
    # Remove exec as we need to return from this function
    /opt/venv/bin/python -m uvicorn main:app \
        --host "${API_HOST}" \
        --port "${API_PORT}" \
        --log-level info \
        --reload \
        --access-log &
    
    return $?
}

# Function to start AppDaemon
start_appdaemon() {
    log_info "Starting AppDaemon..."
    
    cd /usr/share/nodalink-core || {
        log_error "Failed to change directory to /usr/share/nodalink-core"
        return 1
    }
    
    # Use absolute paths for better reliability
    # Remove exec as we need to return from this function
    /opt/venv/bin/appdaemon -c /usr/share/nodalink-core &
    
    return $?
}

# Function to handle shutdown
cleanup() {
    log_info "Shutting down Nodalink Core..."
    
    # Explicitly kill processes by PID if they exist
    if [[ -n "${FASTAPI_PID:-}" ]]; then
        kill "${FASTAPI_PID}" 2>/dev/null || true
        log_info "Sent shutdown signal to FastAPI (PID: ${FASTAPI_PID})"
    fi
    
    if [[ -n "${APPDAEMON_PID:-}" ]]; then
        kill "${APPDAEMON_PID}" 2>/dev/null || true
        log_info "Sent shutdown signal to AppDaemon (PID: ${APPDAEMON_PID})"
    fi
    
    # Also clean up any other background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Wait for graceful shutdown
    sleep 2
    
    # Force kill if needed
    if [[ -n "${FASTAPI_PID:-}" ]] && kill -0 "${FASTAPI_PID}" 2>/dev/null; then
        kill -9 "${FASTAPI_PID}" 2>/dev/null || true
        log_warning "Had to force kill FastAPI process"
    fi
    
    if [[ -n "${APPDAEMON_PID:-}" ]] && kill -0 "${APPDAEMON_PID}" 2>/dev/null; then
        kill -9 "${APPDAEMON_PID}" 2>/dev/null || true
        log_warning "Had to force kill AppDaemon process"
    fi
    
    # Make sure any remaining jobs are killed
    jobs -p | xargs -r kill -9 2>/dev/null || true
    wait
    
    log_info "Nodalink Core shutdown complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGTERM SIGINT EXIT

# Additional sanity checks before starting services
if ! command -v nc >/dev/null 2>&1; then
    log_warning "netcat not found, installing for health checks..."
    apk add --no-cache netcat-openbsd
fi

# Check Python environment
if ! command -v /opt/venv/bin/python >/dev/null 2>&1; then
    log_error "Python virtual environment not found at /opt/venv"
    exit 1
fi

# Check if ports are already in use (avoid port conflicts)
if nc -z localhost "${API_PORT}" >/dev/null 2>&1; then
    log_warning "Port ${API_PORT} is already in use. Check for conflicting services."
    log_fatal "Port ${API_PORT} already in use by another service. Please change the port in your addon configuration."
fi

if nc -z localhost "5050" >/dev/null 2>&1; then
    log_warning "Port 5050 (AppDaemon) is already in use. Check for conflicting services."
    log_fatal "Port 5050 (AppDaemon) already in use by another service."
fi

# Start FastAPI first (AppDaemon will connect to it)
log_notice "Step 1/2: Starting FastAPI server..."
start_fastapi
FASTAPI_PID=$!

if [ -z "$FASTAPI_PID" ] || ! kill -0 "$FASTAPI_PID" 2>/dev/null; then
    log_error "FastAPI process failed to start!"
    cleanup
    log_fatal "Failed to start FastAPI process"
fi

# Wait for FastAPI to be ready
sleep 5
if ! check_service_health "FastAPI" "${API_PORT}"; then
    log_error "FastAPI failed to start properly. Check the API configuration and port availability."
    cleanup
    log_fatal "FastAPI service health check failed"
fi

# Start AppDaemon (it will connect to the shared state)
log_notice "Step 2/2: Starting AppDaemon engine..."
start_appdaemon
APPDAEMON_PID=$!

if [ -z "$APPDAEMON_PID" ] || ! kill -0 "$APPDAEMON_PID" 2>/dev/null; then
    log_error "AppDaemon process failed to start!"
    cleanup
    log_fatal "Failed to start AppDaemon process"
fi

# Wait with better checking for AppDaemon
if ! check_service_health "AppDaemon" "5050"; then
    log_warning "AppDaemon admin interface not responding on expected port."
    # Continue anyway as some setups might have disabled the admin interface
    # but we'll note this in the logs
    log_notice "Continuing startup despite AppDaemon admin interface not being detected."
fi

log_info "-------------------------------------------"
log_info "🚀 Nodalink Core started successfully!"
log_info "📊 FastAPI PID: ${FASTAPI_PID}"
log_info "🤖 AppDaemon PID: ${APPDAEMON_PID}"
log_info "🌐 API accessible at: http://${API_HOST}:${API_PORT}"
log_info "📝 WebSocket endpoint: ws://${API_HOST}:${API_PORT}/ws"
log_info "🔗 Shared in-memory state active for real-time synchronization"
log_info "-------------------------------------------"

# Record successful startup in the add-on's persistent data
mkdir -p /data/nodalink
echo "$(date +%Y-%m-%d\ %H:%M:%S) - Nodalink Core started successfully" >> /data/nodalink/startup_history.log

# Monitor both processes with restart limits to prevent rapid cycling
declare -i fastapi_restarts=0
declare -i appdaemon_restarts=0
declare -i max_restarts=5
declare -i restart_reset_time=3600  # 1 hour in seconds
declare -i last_restart_reset=$(date +%s)

# Core monitoring loop
log_info "Starting process monitoring..."

while true; do
    current_time=$(date +%s)
    
    # Reset restart counters after the specified time
    if [ $((current_time - last_restart_reset)) -ge $restart_reset_time ]; then
        if [ $fastapi_restarts -gt 0 ] || [ $appdaemon_restarts -gt 0 ]; then
            log_notice "Resetting service restart counters (FastAPI: ${fastapi_restarts}, AppDaemon: ${appdaemon_restarts})"
            fastapi_restarts=0
            appdaemon_restarts=0
        fi
        last_restart_reset=$current_time
    fi
    
    # Check if FastAPI is still running
    if ! kill -0 "$FASTAPI_PID" 2>/dev/null; then
        fastapi_restarts=$((fastapi_restarts + 1))
        
        if [ $fastapi_restarts -le $max_restarts ]; then
            log_warning "FastAPI process died, restarting... (Restart ${fastapi_restarts}/${max_restarts})"
            
            # Record the restart in persistent data
            mkdir -p /data/nodalink
            echo "$(date +%Y-%m-%d\ %H:%M:%S) - FastAPI process restarted (${fastapi_restarts}/${max_restarts})" >> /data/nodalink/restart_history.log
            
            start_fastapi
            FASTAPI_PID=$!
            
            # Check if restart was successful
            if [ -z "$FASTAPI_PID" ] || ! kill -0 "$FASTAPI_PID" 2>/dev/null; then
                log_error "Failed to restart FastAPI process!"
            else
                log_notice "FastAPI process restarted successfully with PID ${FASTAPI_PID}"
            fi
        else
            log_error "FastAPI restarted too many times (${fastapi_restarts}/${max_restarts}). Please check the logs for errors."
            log_warning "Continuing to monitor but not restarting FastAPI until the reset period."
            
            # Add failure record
            echo "$(date +%Y-%m-%d\ %H:%M:%S) - CRITICAL: FastAPI restart limit reached (${fastapi_restarts}/${max_restarts})" >> /data/nodalink/restart_history.log
        fi
    fi
    
    # Check if AppDaemon is still running
    if ! kill -0 "$APPDAEMON_PID" 2>/dev/null; then
        appdaemon_restarts=$((appdaemon_restarts + 1))
        
        if [ $appdaemon_restarts -le $max_restarts ]; then
            log_warning "AppDaemon process died, restarting... (Restart ${appdaemon_restarts}/${max_restarts})"
            
            # Record the restart in persistent data
            mkdir -p /data/nodalink
            echo "$(date +%Y-%m-%d\ %H:%M:%S) - AppDaemon process restarted (${appdaemon_restarts}/${max_restarts})" >> /data/nodalink/restart_history.log
            
            start_appdaemon
            APPDAEMON_PID=$!
            
            # Check if restart was successful
            if [ -z "$APPDAEMON_PID" ] || ! kill -0 "$APPDAEMON_PID" 2>/dev/null; then
                log_error "Failed to restart AppDaemon process!"
            else
                log_notice "AppDaemon process restarted successfully with PID ${APPDAEMON_PID}"
            fi
        else
            log_error "AppDaemon restarted too many times (${appdaemon_restarts}/${max_restarts}). Please check the logs for errors."
            log_warning "Continuing to monitor but not restarting AppDaemon until the reset period."
            
            # Add failure record
            echo "$(date +%Y-%m-%d\ %H:%M:%S) - CRITICAL: AppDaemon restart limit reached (${appdaemon_restarts}/${max_restarts})" >> /data/nodalink/restart_history.log
        fi
    fi
    
    # Log a periodic heartbeat to confirm monitoring is active
    if [ $((current_time % 3600)) -lt 30 ]; then 
        log_info "Nodalink Core monitoring heartbeat: FastAPI and AppDaemon processes running"
    fi
    
    # Make sure we don't consume too much CPU with constant checks
    sleep 30
done
