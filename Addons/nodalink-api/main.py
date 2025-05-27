"""
Nodalink FastAPI Backend
REST API backend for the Vue.js node editor frontend.
"""

from scenario_utils import (
    validate_scenario_id,
    parse_scenario_id,
    build_scenario_id,
    validate_scenarios_file,
    get_scenario_suggestions,
    create_default_scenarios
)
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
import sys
import asyncio
from datetime import datetime
import uvicorn

app = FastAPI(title="Nodalink API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths from environment variables
SCENARIOS_FILE = os.getenv("SCENARIO_FILE", "/config/appdaemon/apps/Nodalink/scenarios.json")
UNMATCHED_LOG_FILE = os.getenv("LOG_FILE", "/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log")
CONFIG_FILE = os.getenv("CONFIG_FILE", "/config/appdaemon/apps/Nodalink/config.json")

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
    time_bucket: str
    day_type: str
    optional_flags: List[str]
    interaction_type: str
    actions: List[Dict[str, Any]]

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
            return {"scenario_id": scenario_id, "message": "Scenario created successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save scenario")
            
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
            return {"message": "Scenario updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save scenario")
            
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
            return {"message": "Scenario deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save scenarios")
            
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
            return {"message": "Configuration updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
            
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

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        while True:
            # Keep connection alive and send periodic updates
            scenarios = load_scenarios()
            await websocket.send_json({
                "type": "scenarios_update",
                "data": scenarios,
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(30)  # Send updates every 30 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
