# Nodalink API Server

FastAPI REST server for managing Nodalink scenarios and configuration.

## Features

- **RESTful API**: Complete CRUD operations for scenarios
- **Configuration Management**: Manage room mappings and conditional entities
- **Real-time Updates**: WebSocket support for live data
- **Scenario Validation**: Validate scenarios before saving
- **Unmatched Tracking**: Monitor and suggest improvements for unmatched scenarios
- **CORS Support**: Cross-origin requests for frontend integration

## API Endpoints

- `GET /scenarios` - List all scenarios
- `POST /scenarios` - Create new scenario  
- `GET /scenarios/{id}` - Get specific scenario
- `PUT /scenarios/{id}` - Update scenario
- `DELETE /scenarios/{id}` - Delete scenario
- `POST /scenarios/validate` - Validate scenario
- `GET /config` - Get configuration
- `POST /config` - Update configuration
- `GET /unmatched-scenarios` - Get unmatched scenarios
- `GET /suggestions` - Get scenario suggestions
- `GET /health` - Health check
- `WS /ws` - WebSocket for real-time updates

## Dependencies

This add-on shares configuration files with the AppDaemon Engine add-on.
