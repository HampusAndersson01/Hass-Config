# Nodalink Core Add-on

Combined AppDaemon + FastAPI core engine for Nodalink visual automation system.

## Overview

Nodalink Core is a unified Home Assistant add-on that merges the AppDaemon scenario engine with a FastAPI REST API server into a single container. This provides:

- **Shared in-memory access** between the automation engine and API
- **Real-time WebSocket updates** for live scenario data synchronization  
- **Unified configuration management** through a single add-on
- **Improved performance** with direct memory access instead of file-based communication

## Architecture

```
┌─────────────────────────────────────────────┐
│              Nodalink Core                  │
├─────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │ AppDaemon   │◄──►│ FastAPI Server      │ │
│  │ Engine      │    │ (Port 8002)         │ │
│  │             │    │                     │ │
│  │ - Scenarios │    │ - REST API          │ │
│  │ - Automation│    │ - WebSocket         │ │
│  │ - HA Events │    │ - Shared State      │ │
│  └─────────────┘    └─────────────────────┘ │
│            │                   │            │
│            └─── Shared Memory ─┘            │
├─────────────────────────────────────────────┤
│  Shared Volume: /config/appdaemon/apps/Nodalink/ │
│  - scenarios.json (scenario definitions)    │
│  - config.json (room mappings, settings)    │ 
│  - logs/ (unmatched scenarios, debug)       │
└─────────────────────────────────────────────┘
```

## Features

### Core Engine (AppDaemon)
- Context-aware automation execution
- Room-based scenario matching
- Time bucket and conditional logic
- Fallback scenario support
- Real-time sensor monitoring

### API Server (FastAPI)
- RESTful API for scenario management
- WebSocket for real-time updates
- Configuration management endpoints
- Statistics and analytics
- Scenario testing and simulation

### Shared State Integration
- Direct in-memory data sharing
- Live synchronization between engine and API
- WebSocket notifications for all data changes
- Thread-safe operations with proper locking

## Configuration

### Add-on Options

```yaml
api_port: 8002              # FastAPI server port
api_host: "0.0.0.0"         # API bind address
time_zone: "UTC"            # System timezone
scenario_file: "/config/appdaemon/apps/Nodalink/scenarios.json"
config_file: "/config/appdaemon/apps/Nodalink/config.json"
log_file: "/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log"
test_mode: false            # Enable test mode (log only, no execution)
cors_origins: ["*"]         # CORS allowed origins
```

### Volume Mapping

The add-on uses a shared volume at `/config/appdaemon/apps/Nodalink/` for:
- `scenarios.json` - Scenario definitions
- `config.json` - Room mappings and system settings
- `logs/` - Unmatched scenarios and debug logs

## API Endpoints

### Scenarios
- `GET /scenarios` - List all scenarios
- `POST /scenarios` - Create new scenario
- `GET /scenarios/{id}` - Get specific scenario
- `PUT /scenarios/{id}` - Update scenario
- `DELETE /scenarios/{id}` - Delete scenario
- `POST /scenarios/validate` - Validate scenario
- `POST /scenarios/bulk-import` - Import multiple scenarios

### Configuration
- `GET /config` - Get current configuration
- `POST /config` - Update configuration
- `POST /config/validate` - Validate configuration

### Engine Management
- `GET /engine/status` - Get engine status
- `POST /engine/reload` - Reload engine data
- `POST /engine/test-scenario` - Test scenario execution

### Statistics & Monitoring
- `GET /stats` - Get scenario statistics
- `GET /logs` - Get recent log entries
- `DELETE /logs` - Clear logs
- `GET /health` - Health check

### Real-time Updates
- `WS /ws` - WebSocket for live updates

## WebSocket Events

The WebSocket endpoint provides real-time updates for:

```javascript
{
  "type": "scenarios_update",
  "data": {...},
  "timestamp": "2025-05-28T10:30:00Z"
}
```

Event types:
- `init` - Initial state on connection
- `scenarios_update` - Scenario data changed
- `config_update` - Configuration changed
- `engine_reload` - Engine data reloaded
- `status_update` - Engine status changed
- `log_update` - New log entry
- `unmatched_scenario` - Unmatched scenario detected

## Integration with Nodalink Frontend

The Nodalink Frontend add-on connects to this core engine via:
- REST API: `http://supervisor:8002`
- WebSocket: `ws://supervisor:8002/ws`

Frontend configuration:
```yaml
api_url: "http://supervisor:8002"
websocket_url: "ws://supervisor:8002/ws"
```

## Development

### Local Testing

1. Install dependencies:
```bash
pip install -r api/requirements.txt
pip install appdaemon
```

2. Start FastAPI server:
```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

3. Start AppDaemon (in separate terminal):
```bash
appdaemon -c . -D INFO
```

### Docker Build

```bash
docker build -t nodalink-core .
docker run -p 8002:8002 -p 5050:5050 nodalink-core
```

## Troubleshooting

### Common Issues

1. **API not accessible**: Check port 8002 is exposed and not blocked
2. **AppDaemon not connecting**: Verify Home Assistant token in secrets.yaml
3. **Shared state errors**: Check Python path includes both api/ and apps/ directories
4. **WebSocket connection fails**: Ensure CORS origins are properly configured

### Debug Mode

Enable debug logging by setting log level to DEBUG in the add-on configuration.

### Health Checks

- FastAPI: `curl http://localhost:8002/health`
- AppDaemon: `curl http://localhost:5050`

## Migration from Separate Add-ons

If migrating from separate nodalink-api and appdaemon-nodalink add-ons:

1. Export scenarios from old nodalink-api
2. Install nodalink-core add-on
3. Import scenarios via `/scenarios/bulk-import` endpoint
4. Update nodalink-frontend to point to new API URL
5. Remove old add-ons

## Support

For issues and feature requests, please use the GitHub repository issue tracker.
