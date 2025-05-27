# Nodalink Add-ons Setup Instructions

## Repository Structure

The Nodalink project has been successfully split into three standalone Home Assistant add-ons:

```
Addons/
├── repository.json                    # Add-on repository metadata
├── appdaemon-nodalink/               # Core automation engine
│   ├── config.json                   # Add-on configuration
│   ├── build.yaml                    # Build configuration
│   ├── Dockerfile                    # Container build instructions
│   ├── run.sh                        # Startup script
│   ├── appdaemon.yaml               # AppDaemon configuration template
│   ├── README.md                     # Documentation
│   ├── CHANGELOG.md                  # Version history
│   └── apps/                         # AppDaemon applications
│       ├── scenario_engine.py        # Main automation engine
│       ├── scenario_utils.py         # Utility functions
│       ├── scenarios.json            # Default scenarios
│       └── config.json               # Default configuration
├── nodalink-api/                     # REST API server
│   ├── config.json                   # Add-on configuration
│   ├── build.yaml                    # Build configuration
│   ├── Dockerfile                    # Container build instructions
│   ├── run.sh                        # Startup script
│   ├── main.py                       # FastAPI application
│   ├── scenario_utils.py             # Shared utility functions
│   ├── requirements.txt              # Python dependencies
│   ├── README.md                     # Documentation
│   └── CHANGELOG.md                  # Version history
└── nodalink-frontend/                # Vue.js web interface
    ├── config.json                   # Add-on configuration
    ├── build.yaml                    # Build configuration
    ├── Dockerfile                    # Container build instructions
    ├── run.sh                        # Startup script
    ├── nginx.conf                    # Nginx configuration
    ├── README.md                     # Documentation
    ├── CHANGELOG.md                  # Version history
    └── frontend/                     # Vue.js application
        ├── package.json              # Node.js dependencies
        ├── vite.config.js           # Vite build configuration
        ├── index.html               # HTML template
        └── src/                     # Vue.js source code
            ├── App.vue
            ├── main.js
            ├── stores/
            └── views/
```

## Installation Instructions

### Step 1: Add Repository to Home Assistant

1. Open Home Assistant
2. Go to **Supervisor** → **Add-on Store**
3. Click the **⋮** (three dots) menu in the top right
4. Select **Repositories**
5. Add this URL: `https://github.com/hampusandersson01/hass-config`
6. Click **Add** and close the dialog

### Step 2: Install Add-ons (In Order)

Install the add-ons in this specific order:

#### 1. Nodalink AppDaemon Engine

- Find "Nodalink AppDaemon Engine" in the add-on store
- Click **Install**
- Configure options:
  ```yaml
  time_zone: "Europe/Stockholm" # Your timezone
  test_mode: false
  ```
- Click **Start**
- Enable **Start on boot** and **Watchdog**

#### 2. Nodalink API Server

- Find "Nodalink API Server" in the add-on store
- Click **Install**
- Configure options:
  ```yaml
  port: 8002
  host: "0.0.0.0"
  ```
- Click **Start**
- Enable **Start on boot** and **Watchdog**

#### 3. Nodalink Frontend

- Find "Nodalink Frontend" in the add-on store
- Click **Install**
- Configure options:
  ```yaml
  port: 3000
  api_url: "http://localhost:8002"
  ```
- Click **Start**
- Enable **Start on boot** and **Watchdog**

### Step 3: Access the Interface

1. Open your web browser
2. Navigate to: `http://your-home-assistant-ip:3000`
3. You should see the Nodalink frontend interface

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Server    │    │ AppDaemon Engine│
│   (Port 3000)   │◄──►│   (Port 8002)   │◄──►│   (Internal)    │
│                 │    │                 │    │                 │
│ • Vue.js UI     │    │ • FastAPI       │    │ • Scenario      │
│ • Visual Editor │    │ • REST API      │    │   Processing    │
│ • Analytics     │    │ • WebSocket     │    │ • HA Integration│
│ • Settings      │    │ • Validation    │    │ • Action Exec   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Shared Storage  │
                    │                 │
                    │ • scenarios.json│
                    │ • config.json   │
                    │ • logs/         │
                    └─────────────────┘
```

## Configuration Files

The add-ons share configuration files stored in:

- `/config/appdaemon/apps/Nodalink/scenarios.json` - Scenario definitions
- `/config/appdaemon/apps/Nodalink/config.json` - System configuration
- `/config/appdaemon/apps/Nodalink/logs/` - Log files

## Key Features

### AppDaemon Engine

- ✅ Context-aware automation processing
- ✅ Time-bucket based scenario matching
- ✅ Room and device type mapping
- ✅ Conditional entity support
- ✅ Fallback scenario handling
- ✅ Test mode for safe testing

### API Server

- ✅ RESTful scenario management
- ✅ Configuration management
- ✅ Real-time WebSocket updates
- ✅ Scenario validation
- ✅ Unmatched scenario tracking
- ✅ CORS support

### Frontend

- ✅ Visual node-based editor
- ✅ Real-time analytics dashboard
- ✅ Configuration management UI
- ✅ Responsive modern design
- ✅ Live data synchronization

## Troubleshooting

### Common Issues

1. **Frontend can't connect to API**

   - Check that API server is running on port 8002
   - Verify API URL in frontend configuration

2. **AppDaemon engine not processing scenarios**

   - Check AppDaemon logs in the add-on log tab
   - Verify scenario file exists and is valid JSON

3. **Add-ons fail to start**
   - Check individual add-on logs
   - Ensure ports 3000 and 8002 are not in use
   - Verify configuration syntax

### Log Locations

- AppDaemon Engine: Add-on logs + `/config/appdaemon/logs/`
- API Server: Add-on logs
- Frontend: Add-on logs + browser dev tools

## Next Steps

1. **Configure Room Mappings**: Use the Settings tab to map your rooms to entities
2. **Set Conditional Entities**: Define entities that affect scenario matching
3. **Create Scenarios**: Use the Visual Editor to create your first scenarios
4. **Monitor Performance**: Check the Analytics dashboard for automation insights

The Nodalink add-ons are now ready for use! 🎉
