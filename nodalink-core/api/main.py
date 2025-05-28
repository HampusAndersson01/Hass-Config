"""
Nodalink FastAPI Backend - Integrated with AppDaemon
REST API backend for the Vue.js node editor frontend.
Combined with AppDaemon engine for shared in-memory access.
"""

from scenario_utils import (
    validate_scenario_id,
    parse_scenario_id,
    build_scenario_id,
    validate_scenarios_file,
    get_scenario_suggestions,
    create_default_scenarios
)
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
import sys
import asyncio
from datetime import datetime
import logging
import threading

# Get CORS origins from environment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Shared state between AppDaemon and FastAPI
class SharedState:
    """Shared state container for AppDaemon and FastAPI communication"""
    def __init__(self):
        self.scenarios = {}
        self.config = {}
        self.engine_instance = None
        self.lock = threading.RLock()
        self.stats = {
            "total_scenarios": 0,
            "total_actions": 0,
            "rooms": [],
            "time_buckets": [],
            "interaction_types": []
        }
        self.engine_status = {
            "running": False,
            "scenarios_loaded": 0,
            "last_execution": None,
            "last_config_update": None
        }
        self.logs = []
        self.unmatched_scenarios = []
        self.websocket_connections = set()
    
    def set_engine_instance(self, engine):
        """Set reference to AppDaemon engine instance for direct access"""
        with self.lock:
            self.engine_instance = engine
            self.engine_status["running"] = True
            self.engine_status["scenarios_loaded"] = len(getattr(engine, 'scenarios', {}))
    
    def update_scenarios(self, scenarios):
        """Update scenarios and notify WebSocket clients"""
        with self.lock:
            self.scenarios = scenarios
            self._update_stats()
            self._notify_websocket_clients("scenarios_update", scenarios)
    
    def update_config(self, config):
        """Update configuration and notify WebSocket clients"""
        with self.lock:
            self.config = config
            self.engine_status["last_config_update"] = datetime.now().isoformat()
            self._notify_websocket_clients("config_update", config)
    
    def update_engine_status(self, status):
        """Update engine status"""
        with self.lock:
            self.engine_status.update(status)
            self._notify_websocket_clients("status_update", self.engine_status)
    
    def add_log_entry(self, level, message, data=None):
        """Add log entry and notify WebSocket clients"""
        with self.lock:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "data": data
            }
            self.logs.append(log_entry)
            # Keep only last 1000 entries
            if len(self.logs) > 1000:
                self.logs = self.logs[-1000:]
            self._notify_websocket_clients("log_update", log_entry)
    
    def add_unmatched_scenario(self, scenario_data):
        """Add unmatched scenario and notify WebSocket clients"""
        with self.lock:
            self.unmatched_scenarios.append(scenario_data)
            # Keep only last 500 entries
            if len(self.unmatched_scenarios) > 500:
                self.unmatched_scenarios = self.unmatched_scenarios[-500:]
            self._notify_websocket_clients("unmatched_scenario", scenario_data)
    
    def reload_engine_data(self):
        """Reload data from engine instance if available"""
        if self.engine_instance:
            with self.lock:
                try:
                    # Force reload from engine
                    self.engine_instance.reload_scenarios()
                    self.engine_instance.reload_config()
                    
                    # Update shared state
                    self.scenarios = getattr(self.engine_instance, 'scenarios', {})
                    self.config = getattr(self.engine_instance, 'config', {})
                    self._update_stats()
                    
                    # Notify clients
                    self._notify_websocket_clients("engine_reload", {
                        "scenarios": self.scenarios,
                        "config": self.config,
                        "timestamp": datetime.now().isoformat()
                    })
                    return True
                except Exception as e:
                    logging.error(f"Failed to reload engine data: {e}")
                    return False
        return False
    
    def execute_scenario_test(self, room: str, interaction_type: str = "manual"):
        """Execute a test scenario through the engine"""
        if self.engine_instance and hasattr(self.engine_instance, 'simulate_scenario'):
            try:
                result = self.engine_instance.simulate_scenario(room, interaction_type)
                self._notify_websocket_clients("scenario_test", result)
                return result
            except Exception as e:
                logging.error(f"Failed to execute scenario test: {e}")
                return {"error": str(e)}
        return {"error": "Engine not available"}
    
    def add_websocket_connection(self, websocket):
        """Add WebSocket connection"""
        self.websocket_connections.add(websocket)
    
    def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        self.websocket_connections.discard(websocket)
    
    def _notify_websocket_clients(self, event_type: str, data: Any):
        """Notify all connected WebSocket clients"""
        if not self.websocket_connections:
            return
        
        message = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients (in background to avoid blocking)
        disconnected = set()
        for websocket in self.websocket_connections.copy():
            try:
                asyncio.create_task(websocket.send_json(message))
            except Exception:
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.discard(websocket)
    
    def _update_stats(self):
        """Update statistics based on current scenarios"""
        rooms = set()
        time_buckets = set()
        interaction_types = set()
        total_actions = 0
        
        for scenario_group in self.scenarios.values():
            for scenario in scenario_group:
                if isinstance(scenario, dict):
                    scenario_id = scenario.get("scenario_id", "")
                    parts = scenario_id.split("|")
                    if len(parts) > 0 and parts[0]:
                        rooms.add(parts[0])
                    if len(parts) > 1 and parts[1]:
                        time_buckets.add(parts[1])
                    if len(parts) > 4 and parts[4]:
                        interaction_types.add(parts[4])
                    
                    actions = scenario.get("actions", [])
                    total_actions += len(actions)
        
        self.stats.update({
            "total_scenarios": sum(len(group) for group in self.scenarios.values()),
            "total_actions": total_actions,
            "rooms": sorted(list(rooms)),
            "time_buckets": sorted(list(time_buckets)),
            "interaction_types": sorted(list(interaction_types))
        })

# Global shared state instance
shared_state = SharedState()

app = FastAPI(title="Nodalink Core API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths from environment variables
SCENARIOS_FILE = os.getenv(
    "SCENARIO_FILE", "/config/appdaemon/apps/Nodalink/scenarios.json")
UNMATCHED_LOG_FILE = os.getenv(
    "LOG_FILE", "/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log")
CONFIG_FILE = os.getenv(
    "CONFIG_FILE", "/config/appdaemon/apps/Nodalink/config.json")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Add to shared state
        shared_state.add_websocket_connection(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # Remove from shared state
        shared_state.remove_websocket_connection(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Pydantic models
class ScenarioAction(BaseModel):
    service: str
    entity_id: str
    data: Dict[str, Any] = {}

class ScenarioRequest(BaseModel):
    room: str
    time_bucket: str = ""
    day_type: str = ""
    optional_flags: List[str] = []
    interaction_type: str = ""
    actions: List[ScenarioAction]

class ScenarioResponse(BaseModel):
    scenario_id: str
    room: str
    time_bucket: str = ""
    day_type: str = ""
    optional_flags: List[str] = []
    interaction_type: str = ""
    actions: List[Dict[str, Any]]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ValidationResponse(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str] = []

class RoomMapping(BaseModel):
    label: str
    entity_id: str
    entity_type: str
    description: str = ""

class ConditionalEntity(BaseModel):
    label: str
    entity_id: str
    entity_type: str
    description: str = ""
    icon: str = ""

class SystemSettings(BaseModel):
    time_bucket_minutes: int = 60
    fallback_enabled: bool = True
    test_mode: bool = False
    auto_reload_config: bool = True
    allowed_domains: List[str] = []

class ConfigRequest(BaseModel):
    room_mappings: List[RoomMapping] = []
    conditional_entities: List[ConditionalEntity] = []
    system_settings: SystemSettings = SystemSettings()

class EngineStatus(BaseModel):
    running: bool
    scenarios_loaded: int
    last_execution: Optional[str] = None
    last_config_update: Optional[str] = None

class StatsResponse(BaseModel):
    total_scenarios: int
    total_actions: int
    rooms: List[str]
    time_buckets: List[str]
    interaction_types: List[str]

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    data: Optional[Dict[str, Any]] = None

class ScenarioTestRequest(BaseModel):
    room: str
    interaction_type: str = "manual"

# Utility functions


def load_scenarios() -> Dict[str, Any]:
    """Load scenarios from file."""
    try:
        if os.path.exists(SCENARIOS_FILE):
            with open(SCENARIOS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading scenarios: {e}")
        return {}


def save_scenarios(scenarios: Dict[str, Any]) -> bool:
    """Save scenarios to file."""
    try:
        os.makedirs(os.path.dirname(SCENARIOS_FILE), exist_ok=True)
        with open(SCENARIOS_FILE, 'w') as f:
            json.dump(scenarios, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving scenarios: {e}")
        return False


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            "room_mappings": [],
            "conditional_entities": [],
            "system_settings": {
                "time_bucket_minutes": 60,
                "fallback_enabled": True,
                "test_mode": False,
                "auto_reload_config": True,
                "allowed_domains": []
            }
        }
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# API endpoints


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/scenarios")
async def get_scenarios():
    """Get all scenarios."""
    scenarios = load_scenarios()
    return {"scenarios": scenarios}


@app.post("/scenarios")
async def create_scenario(scenario: ScenarioRequest):
    """Create a new scenario."""
    try:
        scenarios = load_scenarios()

        # Build scenario ID
        scenario_id = build_scenario_id(
            scenario.room,
            scenario.time_bucket,
            scenario.day_type,
            scenario.optional_flags,
            scenario.interaction_type
        )

        # Convert actions to dict format
        actions = [action.dict() for action in scenario.actions]

        # Store scenario
        scenarios[scenario_id] = {
            "room": scenario.room,
            "time_bucket": scenario.time_bucket,
            "day_type": scenario.day_type,
            "optional_flags": scenario.optional_flags,
            "interaction_type": scenario.interaction_type,
            "actions": actions,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if save_scenarios(scenarios):
            # Update shared state
            shared_state.update_scenarios(scenarios)
            await manager.broadcast({
                "type": "scenarios_update",
                "data": scenarios,
                "timestamp": datetime.now().isoformat()
            })
            return {"scenario_id": scenario_id, "message": "Scenario created successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save scenario")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get a specific scenario."""
    scenarios = load_scenarios()
    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario_data = scenarios[scenario_id]
    return ScenarioResponse(
        scenario_id=scenario_id,
        **scenario_data
    )


@app.put("/scenarios/{scenario_id}")
async def update_scenario(scenario_id: str, scenario: ScenarioRequest):
    """Update an existing scenario."""
    try:
        scenarios = load_scenarios()

        if scenario_id not in scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")

        # Convert actions to dict format
        actions = [action.dict() for action in scenario.actions]

        # Update scenario
        scenarios[scenario_id].update({
            "room": scenario.room,
            "time_bucket": scenario.time_bucket,
            "day_type": scenario.day_type,
            "optional_flags": scenario.optional_flags,
            "interaction_type": scenario.interaction_type,
            "actions": actions,
            "updated_at": datetime.now().isoformat()
        })

        if save_scenarios(scenarios):
            # Update shared state
            shared_state.update_scenarios(scenarios)
            await manager.broadcast({
                "type": "scenarios_update",
                "data": scenarios,
                "timestamp": datetime.now().isoformat()
            })
            return {"message": "Scenario updated successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save scenario")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    try:
        scenarios = load_scenarios()

        if scenario_id not in scenarios:
            raise HTTPException(status_code=404, detail="Scenario not found")

        del scenarios[scenario_id]

        if save_scenarios(scenarios):
            # Update shared state
            shared_state.update_scenarios(scenarios)
            await manager.broadcast({
                "type": "scenarios_update",
                "data": scenarios,
                "timestamp": datetime.now().isoformat()
            })
            return {"message": "Scenario deleted successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save scenarios")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scenarios/validate")
async def validate_scenario(scenario: ScenarioRequest):
    """Validate a scenario without saving it."""
    try:
        errors = []
        warnings = []

        # Validate scenario ID components
        if not scenario.room:
            errors.append("Room is required")

        if not scenario.actions:
            errors.append("At least one action is required")

        # Validate actions
        for i, action in enumerate(scenario.actions):
            if not action.service:
                errors.append(f"Action {i+1}: Service is required")
            if not action.entity_id:
                errors.append(f"Action {i+1}: Entity ID is required")

        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        return ValidationResponse(
            valid=False,
            errors=[str(e)],
            warnings=[]
        )


@app.get("/config")
async def get_config():
    """Get current configuration."""
    config = load_config()
    return config


@app.post("/config")
async def update_config(config: ConfigRequest):
    """Update configuration."""
    try:
        config_dict = {
            "room_mappings": [mapping.dict() for mapping in config.room_mappings],
            "conditional_entities": [entity.dict() for entity in config.conditional_entities],
            "system_settings": config.system_settings.dict()
        }

        if save_config(config_dict):
            # Update shared state
            shared_state.update_config(config_dict)
            await manager.broadcast({
                "type": "config_update",
                "data": config_dict,
                "timestamp": datetime.now().isoformat()
            })
            return {"message": "Configuration updated successfully"}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to save configuration")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unmatched-scenarios")
async def get_unmatched_scenarios():
    """Get unmatched scenarios from log file."""
    try:
        unmatched = []
        if os.path.exists(UNMATCHED_LOG_FILE):
            with open(UNMATCHED_LOG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        unmatched.append(line)
        return {"unmatched_scenarios": unmatched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suggestions")
async def get_suggestions():
    """Get scenario suggestions based on unmatched scenarios."""
    try:
        suggestions = get_scenario_suggestions(UNMATCHED_LOG_FILE)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Engine management endpoints
@app.get("/engine/status", response_model=EngineStatus)
async def get_engine_status():
    """Get current engine status."""
    return shared_state.engine_status

@app.post("/engine/reload")
async def reload_engine():
    """Reload engine data from files."""
    try:
        success = shared_state.reload_engine_data()
        if success:
            return {"message": "Engine data reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload engine data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/engine/test-scenario")
async def test_scenario(test_request: ScenarioTestRequest):
    """Execute a test scenario."""
    try:
        result = shared_state.execute_scenario_test(
            test_request.room, 
            test_request.interaction_type
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get current statistics."""
    return shared_state.stats

@app.get("/logs")
async def get_logs(limit: int = 100):
    """Get recent log entries."""
    try:
        logs = shared_state.logs[-limit:] if limit > 0 else shared_state.logs
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/logs")
async def clear_logs():
    """Clear all log entries."""
    try:
        with shared_state.lock:
            shared_state.logs.clear()
        return {"message": "Logs cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Scenarios bulk operations
@app.post("/scenarios/bulk-import")
async def bulk_import_scenarios(scenarios_data: Dict[str, Any]):
    """Import multiple scenarios at once."""
    try:
        current_scenarios = load_scenarios()
        
        # Validate scenarios format
        validation_result = validate_scenarios_file(scenarios_data)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid scenarios format: {validation_result['errors']}"
            )
        
        # Merge with existing scenarios
        current_scenarios.update(scenarios_data)
        
        if save_scenarios(current_scenarios):
            shared_state.update_scenarios(current_scenarios)
            await manager.broadcast({
                "type": "scenarios_bulk_update",
                "data": current_scenarios,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "message": f"Successfully imported {len(scenarios_data)} scenarios",
                "total_scenarios": len(current_scenarios)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save scenarios")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/scenarios")
async def delete_all_scenarios():
    """Delete all scenarios."""
    try:
        if save_scenarios({}):
            shared_state.update_scenarios({})
            await manager.broadcast({
                "type": "scenarios_cleared",
                "data": {},
                "timestamp": datetime.now().isoformat()
            })
            return {"message": "All scenarios deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear scenarios")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuration validation
@app.post("/config/validate")
async def validate_config(config: ConfigRequest):
    """Validate configuration without saving."""
    try:
        errors = []
        warnings = []
        
        # Validate room mappings
        room_labels = set()
        for mapping in config.room_mappings:
            if mapping.label in room_labels:
                errors.append(f"Duplicate room label: {mapping.label}")
            room_labels.add(mapping.label)
            
            if not mapping.entity_id:
                errors.append(f"Room '{mapping.label}': Entity ID is required")
        
        # Validate conditional entities
        entity_labels = set()
        for entity in config.conditional_entities:
            if entity.label in entity_labels:
                errors.append(f"Duplicate entity label: {entity.label}")
            entity_labels.add(entity.label)
        
        # Validate system settings
        if config.system_settings.time_bucket_minutes <= 0:
            errors.append("Time bucket minutes must be positive")
        
        return ValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    except Exception as e:
        return ValidationResponse(
            valid=False,
            errors=[str(e)],
            warnings=[]
        )

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        # Send initial state immediately
        initial_state = {
            "type": "init",
            "data": {
                "scenarios": shared_state.scenarios,
                "config": shared_state.config,
                "stats": shared_state.stats,
                "engine_status": shared_state.engine_status,
                "logs": shared_state.logs[-100:]  # Last 100 log entries
            },
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(initial_state)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, requests, etc.)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                
                # Handle client requests
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif data.get("type") == "get_current_state":
                    current_state = {
                        "type": "current_state",
                        "data": {
                            "scenarios": shared_state.scenarios,
                            "config": shared_state.config,
                            "stats": shared_state.stats,
                            "engine_status": shared_state.engine_status,
                            "logs": shared_state.logs[-100:]
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_json(current_state)
                    
            except asyncio.TimeoutError:
                # Send periodic ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

# Startup event to initialize shared state
@app.on_event("startup")
async def startup_event():
    """Initialize shared state on startup."""
    logger.info("Initializing Nodalink Core API...")
    
    # Load initial data
    scenarios = load_scenarios()
    config = load_config()
    
    # Update shared state
    shared_state.update_scenarios(scenarios)
    shared_state.update_config(config)
    
    # Create default scenarios if none exist
    if not scenarios:
        logger.info("No scenarios found, creating defaults...")
        default_scenarios = create_default_scenarios()
        if save_scenarios(default_scenarios):
            shared_state.update_scenarios(default_scenarios)
    
    shared_state.add_log_entry("INFO", "Nodalink Core API started successfully")
    logger.info("Nodalink Core API initialized successfully")

# Function to be called by AppDaemon engine
def get_shared_state():
    """Get shared state instance for AppDaemon integration."""
    return shared_state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
