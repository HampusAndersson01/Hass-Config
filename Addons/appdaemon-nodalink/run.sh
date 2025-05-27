#!/usr/bin/with-contenv bashio

# Read configuration options
TIME_ZONE=$(bashio::config 'time_zone')
SCENARIO_FILE=$(bashio::config 'scenario_file')
CONFIG_FILE=$(bashio::config 'config_file')
LOG_FILE=$(bashio::config 'log_file')
TEST_MODE=$(bashio::config 'test_mode')

# Set timezone
if [ -n "$TIME_ZONE" ]; then
    export TZ="$TIME_ZONE"
fi

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Copy Nodalink apps if they don't exist
if [ ! -f "$SCENARIO_FILE" ] || [ ! -f "$CONFIG_FILE" ]; then
    bashio::log.info "Copying Nodalink files to config directory..."
    mkdir -p /config/appdaemon/apps/Nodalink/logs
    
    if [ ! -f "$SCENARIO_FILE" ]; then
        cp /usr/share/appdaemon/apps/scenarios.json "$SCENARIO_FILE"
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        cp /usr/share/appdaemon/apps/config.json "$CONFIG_FILE"
    fi
fi

# Create AppDaemon configuration
cat > /usr/share/appdaemon/appdaemon.yaml << EOF
secrets: /config/secrets.yaml
appdaemon:
  latitude: !secret latitude
  longitude: !secret longitude
  elevation: !secret elevation
  time_zone: $TIME_ZONE
  plugins:
    HASS:
      type: hass
      ha_url: http://supervisor/core
      token: !secret appdaemon_key
      
http:
  url: http://127.0.0.1:5050

admin:
  title: AppDaemon
  stats_update: realtime

api:

hadashboard:

logs:
  main_log:
    filename: /config/appdaemon/logs/appdaemon.log
    log_generations: 3
    log_size: 1000000
  access_log:
    filename: /config/appdaemon/logs/access.log
  error_log:
    filename: /config/appdaemon/logs/error.log

apps:
  nodalink_engine:
    module: scenario_engine
    class: NodalinkEngine
    scenario_file: $SCENARIO_FILE
    config_file: $CONFIG_FILE
    log_file: $LOG_FILE
    test_mode: $TEST_MODE
    ui_enabled: false
EOF

bashio::log.info "Starting Nodalink AppDaemon Engine..."
bashio::log.info "Scenario file: $SCENARIO_FILE"
bashio::log.info "Config file: $CONFIG_FILE"
bashio::log.info "Test mode: $TEST_MODE"

# Start AppDaemon
exec appdaemon -c /usr/share/appdaemon
