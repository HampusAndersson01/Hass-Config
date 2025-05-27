"""
Nodalink Scenario Engine
A context-aware automation engine for Home Assistant using AppDaemon.
"""

import json
import os
import socket
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import appdaemon.plugins.hass.hassapi as hass
from .scenario_utils import (
    get_time_bucket,
    get_day_type,
    build_scenario_id,
    validate_service_call,
    evaluate_conditions,
    sanitize_entity_id
)


class NodalinkEngine(hass.Hass):
    """Main Nodalink automation engine."""

    def initialize(self):
        """Initialize the Nodalink engine."""
        self.log("🔗 Nodalink Engine initializing...")

        # Load basic file paths from args
        self.scenario_file = self.args.get(
            "scenario_file", "/config/appdaemon/apps/Nodalink/scenarios.json")
        self.log_file = self.args.get(
            "log_file", "/config/appdaemon/apps/Nodalink/logs/unmatched_scenarios.log")
        self.config_file = self.args.get(
            "config_file", "/config/appdaemon/apps/Nodalink/config.json")

        # Load UI-managed configuration
        self.config = self._load_config()

        # Extract configuration values
        self.room_mappings = self._extract_room_mappings()
        self.conditional_entities = self._extract_conditional_entities()
        self.time_bucket_minutes = self.config.get(
            "system_settings", {}).get("time_bucket_minutes", 60)
        self.test_mode = self.config.get(
            "system_settings", {}).get("test_mode", False)
        self.fallback_enabled = self.config.get(
            "system_settings", {}).get("fallback_enabled", True)
        self.allowed_domains = self.config.get("system_settings", {}).get("allowed_domains", [
            "light", "switch", "scene", "script", "automation",
            "media_player", "climate", "cover", "fan", "vacuum"
        ])

        # Set up config file watcher for live reloading
        if self.config.get("system_settings", {}).get("auto_reload_config", True):
            self._setup_config_watcher()

        # Load scenarios
        self.scenarios = self._load_scenarios()

        # Initialize FastAPI UI server if enabled
        ui_enabled = self.args.get("ui_enabled", True)
        if ui_enabled:
            self.launch_ui_server()

        self.log(
            f"✅ Nodalink Engine initialized with {len(self.scenarios)} scenarios")
        if self.test_mode:
            self.log(
                "🧪 Test mode enabled - scenarios will be logged but not executed")

    def is_port_open(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is already in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception as e:
            self.log(f"⚠️ Error checking port {port}: {e}")
            return False

    def launch_ui_server(self):
        """Launch the FastAPI UI server if not already running."""
        ui_port = 8002

        if self.is_port_open(ui_port):
            self.log(f"🌐 FastAPI UI server already running on port {ui_port}")
            return

        try:
            self.log(f"🚀 Starting FastAPI UI server on port {ui_port}...")

            def run_server():
                try:
                    # Check if FastAPI modules are available
                    import uvicorn
                    # Try to import the FastAPI app
                    from .ui.fastapi_vue.main import app

                    uvicorn.run(
                        app,
                        host="0.0.0.0",
                        port=ui_port,
                        log_level="info",
                        access_log=False
                    )
                except ImportError as e:
                    self.log(f"⚠️ FastAPI dependencies not available: {e}")
                    self.log(
                        "FastAPI UI server disabled - install fastapi and uvicorn to enable")
                except Exception as e:
                    self.log(f"❌ Error starting FastAPI server: {e}")

            # Start server in daemon thread to avoid blocking AppDaemon
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            self.log(
                f"✅ FastAPI UI server started on http://0.0.0.0:{ui_port}")

        except Exception as e:
            self.log(f"❌ Failed to start FastAPI UI server: {e}")

    def _load_scenarios(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load scenarios from JSON file."""
        try:
            if os.path.exists(self.scenario_file):
                with open(self.scenario_file, 'r') as f:
                    scenarios = json.load(f)
                    self.log(
                        f"📖 Loaded {len(scenarios)} scenario groups from {self.scenario_file}")
                    return scenarios
            else:
                self.log(f"⚠️ Scenario file not found: {self.scenario_file}")
                return {}
        except Exception as e:
            self.log(f"❌ Error loading scenarios: {e}")
            return {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from UI-managed config.json file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.log(f"📖 Loaded configuration from {self.config_file}")
                    return config
            else:
                self.log(
                    f"⚠️ Config file not found: {self.config_file}, creating default")
                default_config = self._create_default_config()
                self._save_config(default_config)
                return default_config
        except Exception as e:
            self.log(f"❌ Error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration structure."""
        return {
            "_metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "description": "Nodalink system configuration - rooms, sensors, and conditional flags"
            },
            "room_mappings": {},
            "conditional_entities": {},
            "system_settings": {
                "time_bucket_minutes": 60,
                "fallback_enabled": True,
                "test_mode": False,
                "auto_reload_config": True,
                "allowed_domains": [
                    "light", "switch", "scene", "script", "automation",
                    "media_player", "climate", "cover", "fan", "vacuum"
                ]
            }
        }

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.log(f"💾 Configuration saved to {self.config_file}")
        except Exception as e:
            self.log(f"❌ Error saving config: {e}")

    def _extract_room_mappings(self) -> Dict[str, str]:
        """Extract room mappings from config."""
        room_mappings = {}
        for room_key, room_data in self.config.get("room_mappings", {}).items():
            if isinstance(room_data, dict) and "entity_id" in room_data:
                room_mappings[room_key] = room_data["entity_id"]
        return room_mappings

    def _extract_conditional_entities(self) -> Dict[str, str]:
        """Extract conditional entities from config."""
        conditional_entities = {}
        for flag_key, flag_data in self.config.get("conditional_entities", {}).items():
            if isinstance(flag_data, dict) and "entity_id" in flag_data:
                conditional_entities[flag_key] = flag_data["entity_id"]
        return conditional_entities

    def reload_scenarios(self):
        """Reload scenarios from file."""
        self.log("🔄 Reloading scenarios...")
        self.scenarios = self._load_scenarios()
        self.log(f"✅ Reloaded {len(self.scenarios)} scenario groups")

    def reload_config(self):
        """Reload configuration from file."""
        self.log("🔄 Reloading configuration...")
        self.config = self._load_config()
        self.room_mappings = self._extract_room_mappings()
        self.conditional_entities = self._extract_conditional_entities()
        self.log("✅ Configuration reloaded")

    def get_scenario_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded scenarios."""
        total_scenarios = sum(len(scenarios)
                              for scenarios in self.scenarios.values())
        return {
            "scenario_groups": len(self.scenarios),
            "total_scenarios": total_scenarios,
            "room_mappings": len(self.room_mappings),
            "conditional_entities": len(self.conditional_entities),
            "test_mode": self.test_mode
        }

    def simulate_scenario(self, room: str, interaction_type: str = "manual") -> Dict[str, Any]:
        """Simulate a scenario execution without actually executing it."""
        self.log(
            f"🎭 Simulating scenario for room: {room}, interaction: {interaction_type}")

        # Build a simple scenario ID for simulation
        time_bucket = f"{datetime.now().hour:02d}-{(datetime.now().hour + 1) % 24:02d}"
        scenario_id = f"{room}|{time_bucket}|{interaction_type}"

        return {
            "scenario_id": scenario_id,
            "room": room,
            "interaction_type": interaction_type,
            "time_bucket": time_bucket,
            "simulated": True,
            "timestamp": datetime.now().isoformat()
        }

    def is_port_open(self, port: int, host: str = "localhost") -> bool:
        """Check if a port is already in use."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception as e:
            self.log(f"⚠️ Error checking port {port}: {e}")
            return False

    def launch_ui_server(self):
        """Launch the FastAPI UI server if not already running."""
        ui_port = 8002

        if self.is_port_open(ui_port):
            self.log(f"🌐 FastAPI UI server already running on port {ui_port}")
            return

        try:
            self.log(f"🚀 Starting FastAPI UI server on port {ui_port}...")

            def run_server():
                try:
                    import uvicorn
                    uvicorn.run(
                        "apps.Nodalink.ui.fastapi_vue.main:app",
                        host="0.0.0.0",
                        port=ui_port,
                        log_level="info",
                        access_log=False
                    )
                except Exception as e:
                    self.log(f"❌ Error starting FastAPI server: {e}")

            # Start server in daemon thread to avoid blocking AppDaemon
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            self.log(
                f"✅ FastAPI UI server started on http://0.0.0.0:{ui_port}")

        except Exception as e:
            self.log(f"❌ Failed to start FastAPI UI server: {e}")

    def _load_scenarios(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load scenarios from JSON file."""
        try:
            if os.path.exists(self.scenario_file):
                with open(self.scenario_file, 'r') as f:
                    scenarios = json.load(f)
                self.log(
                    f"📁 Loaded {len(scenarios)} scenarios from {self.scenario_file}")
                return scenarios
            else:
                self.log(f"⚠️ Scenario file not found: {self.scenario_file}")
                return {}
        except Exception as e:
            self.log(f"❌ Error loading scenarios: {e}")
            return {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from UI-managed config.json file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                self.log(f"🔧 Loaded configuration from {self.config_file}")
                return config
            else:
                self.log(f"⚠️ Config file not found: {self.config_file}")
                return self._create_default_config()
        except Exception as e:
            self.log(f"❌ Error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration structure."""
        default_config = {
            "_metadata": {
                "version": "1.0.0",
                "created": datetime.now().isoformat(),
                "description": "Nodalink system configuration"
            },
            "room_mappings": {},
            "conditional_entities": {},
            "system_settings": {
                "time_bucket_minutes": 60,
                "fallback_enabled": True,
                "test_mode": False,
                "auto_reload_config": True,
                "allowed_domains": [
                    "light", "switch", "scene", "script", "automation",
                    "media_player", "climate", "cover", "fan", "vacuum"
                ]
            }
        }

        # Save default config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            self.log(f"📝 Created default config file: {self.config_file}")
        except Exception as e:
            self.log(f"❌ Error creating default config: {e}")

        return default_config

    def _extract_room_mappings(self) -> Dict[str, str]:
        """Extract simple room mappings from config for backward compatibility."""
        room_mappings = {}
        config_rooms = self.config.get("room_mappings", {})

        for room_id, room_config in config_rooms.items():
            if isinstance(room_config, dict):
                room_mappings[room_id] = room_config.get("entity_id", "")
            else:
                # Backward compatibility with simple string mappings
                room_mappings[room_id] = room_config

        return room_mappings

    def _extract_conditional_entities(self) -> Dict[str, str]:
        """Extract simple conditional entity mappings from config for backward compatibility."""
        conditional_entities = {}
        config_flags = self.config.get("conditional_entities", {})

        for flag_id, flag_config in config_flags.items():
            if isinstance(flag_config, dict):
                conditional_entities[flag_id] = flag_config.get(
                    "entity_id", "")
            else:
                # Backward compatibility with simple string mappings
                conditional_entities[flag_id] = flag_config

        return conditional_entities

    def _setup_config_watcher(self):
        """Set up file watcher for config changes (simplified approach)."""
        # For now, we'll implement a manual reload method
        # In production, this could watch file modification times
        self.log("🔄 Config auto-reload enabled (manual reload available)")

    def reload_config(self):
        """Manually reload configuration from file."""
        self.log("🔄 Reloading configuration...")

        # Store old mappings for comparison
        old_room_mappings = self.room_mappings.copy()
        old_conditional_entities = self.conditional_entities.copy()

        # Reload config
        self.config = self._load_config()
        self.room_mappings = self._extract_room_mappings()
        self.conditional_entities = self._extract_conditional_entities()
        self.time_bucket_minutes = self.config.get(
            "system_settings", {}).get("time_bucket_minutes", 60)
        self.test_mode = self.config.get(
            "system_settings", {}).get("test_mode", False)
        self.fallback_enabled = self.config.get(
            "system_settings", {}).get("fallback_enabled", True)
        self.allowed_domains = self.config.get("system_settings", {}).get("allowed_domains", [
            "light", "switch", "scene", "script", "automation",
            "media_player", "climate", "cover", "fan", "vacuum"
        ])

        # Check if we need to update listeners
        if old_room_mappings != self.room_mappings:
            self.log("🎯 Room mappings changed, updating listeners...")
            # Remove old listeners
            # Note: AppDaemon doesn't have a direct way to remove specific listeners
            # In a full implementation, you'd track listener handles and remove them

            # Setup new listeners
            for entity_id in self.room_mappings.values():
                if entity_id.startswith("binary_sensor."):
                    self.listen_state(self._handle_presence_change, entity_id)

        self.log("✅ Configuration reloaded successfully")

    def _setup_listeners(self):
        """Setup event listeners for triggers."""
        # Listen to button events
        self.listen_event(self._handle_button_event, "zha_event")
        self.listen_event(self._handle_button_event, "deconz_event")

        # Listen to presence/motion sensors
        for entity_id in self.room_mappings.values():
            if entity_id.startswith("binary_sensor."):
                self.listen_state(self._handle_presence_change, entity_id)

        # Listen to custom Nodalink triggers
        self.listen_event(self._handle_nodalink_event, "nodalink_trigger")

        self.log("🎯 Event listeners configured")

    def _handle_button_event(self, event_name: str, data: Dict[str, Any], kwargs: Dict[str, Any]):
        """Handle button press events."""
        try:
            device_id = data.get("device_id")
            command = data.get("command", "")

            # Map device to room
            room = self._get_room_from_device(device_id)
            if not room:
                self.log(f"🔍 Unknown device: {device_id}")
                return

            # Determine interaction type
            interaction_type = self._map_button_command(command)

            # Process scenario
            self._process_scenario_trigger(
                room=room,
                interaction_type=interaction_type,
                trigger_type="button_press",
                source_entity=device_id
            )

        except Exception as e:
            self.log(f"❌ Error handling button event: {e}")
            self.log(traceback.format_exc())

    def _handle_presence_change(self, entity: str, attribute: str, old: str, new: str, kwargs: Dict[str, Any]):
        """Handle presence/motion sensor changes."""
        try:
            if new != "on":
                return

            # Map entity to room
            room = self._get_room_from_entity(entity)
            if not room:
                return

            # Process scenario
            self._process_scenario_trigger(
                room=room,
                interaction_type="presence_detected",
                trigger_type="presence",
                source_entity=entity
            )

        except Exception as e:
            self.log(f"❌ Error handling presence change: {e}")
            self.log(traceback.format_exc())

    def _handle_nodalink_event(self, event_name: str, data: Dict[str, Any], kwargs: Dict[str, Any]):
        """Handle custom Nodalink trigger events."""
        try:
            room = data.get("room", "unknown")
            interaction_type = data.get("interaction_type", "custom")
            trigger_type = data.get("trigger_type", "manual")

            self._process_scenario_trigger(
                room=room,
                interaction_type=interaction_type,
                trigger_type=trigger_type,
                source_entity="nodalink_manual"
            )

        except Exception as e:
            self.log(f"❌ Error handling Nodalink event: {e}")

    def _process_scenario_trigger(self, room: str, interaction_type: str, trigger_type: str, source_entity: str):
        """Process a scenario trigger and execute matching actions."""
        try:
            # Get current context
            current_time = datetime.now()
            time_bucket = get_time_bucket(
                current_time, self.time_bucket_minutes)
            day_type = get_day_type(current_time)

            # Evaluate conditional flags
            optional_flags = self._evaluate_optional_flags()

            # Build scenario ID
            scenario_id = build_scenario_id(
                room=room,
                time_bucket=time_bucket,
                day_type=day_type,
                optional_flags=optional_flags,
                interaction_type=interaction_type
            )

            self.log(f"🎯 Processing trigger: {scenario_id}")

            # Find and execute matching scenario
            actions = self._find_matching_scenario(scenario_id)

            if actions:
                self.log(
                    f"✅ Found {len(actions)} actions for scenario: {scenario_id}")
                self._execute_actions(actions, scenario_id)
            else:
                # Log unmatched scenario
                self._log_unmatched_scenario(scenario_id, {
                    "room": room,
                    "time_bucket": time_bucket,
                    "day_type": day_type,
                    "optional_flags": optional_flags,
                    "interaction_type": interaction_type,
                    "trigger_type": trigger_type,
                    "source_entity": source_entity,
                    "timestamp": current_time.isoformat()
                })

        except Exception as e:
            self.log(f"❌ Error processing scenario trigger: {e}")
            self.log(traceback.format_exc())

    def _find_matching_scenario(self, scenario_id: str) -> Optional[List[Dict[str, Any]]]:
        """Find matching scenario with fallback logic."""
        # Try exact match first
        if scenario_id in self.scenarios:
            return self.scenarios[scenario_id]

        if not self.fallback_enabled:
            return None

        # Parse scenario ID for fallback matching
        parts = scenario_id.split("|")
        if len(parts) < 2:
            return None

        room = parts[0]
        time_bucket = parts[1]
        day_type = parts[2] if len(parts) > 2 else ""
        optional_flags = parts[3] if len(parts) > 3 else ""
        interaction_type = parts[4] if len(parts) > 4 else ""

        # Fallback hierarchy
        fallback_patterns = []

        # Remove interaction type
        if interaction_type:
            fallback_id = f"{room}|{time_bucket}|{day_type}|{optional_flags}"
            fallback_patterns.append(fallback_id.rstrip("|"))

        # Remove optional flags
        if optional_flags:
            fallback_id = f"{room}|{time_bucket}|{day_type}"
            fallback_patterns.append(fallback_id.rstrip("|"))

        # Remove day type
        if day_type:
            fallback_id = f"{room}|{time_bucket}"
            fallback_patterns.append(fallback_id)

        # Room only
        fallback_patterns.append(room)

        # Try fallback patterns
        for pattern in fallback_patterns:
            if pattern in self.scenarios:
                self.log(
                    f"🔄 Using fallback scenario: {pattern} for {scenario_id}")
                return self.scenarios[pattern]

        return None

    def _execute_actions(self, actions: List[Dict[str, Any]], scenario_id: str):
        """Execute a list of actions."""
        for i, action in enumerate(actions):
            try:
                if self.test_mode:
                    self.log(f"🧪 TEST MODE - Would execute: {action}")
                    continue

                # Validate action
                if not validate_service_call(action):
                    self.log(
                        f"❌ Invalid service call in scenario {scenario_id}: {action}")
                    continue

                domain = action.get("domain", action.get(
                    "service", "").split(".")[0])
                if domain not in self.allowed_domains:
                    self.log(f"🚫 Domain not allowed: {domain}")
                    continue

                # Execute service call
                service = action.get(
                    "service", f"{domain}.{action.get('action', 'turn_on')}")
                entity_id = action.get("entity_id", "")
                data = action.get("data", {})

                if entity_id:
                    entity_id = sanitize_entity_id(entity_id)
                    data["entity_id"] = entity_id

                self.log(f"🎬 Executing: {service} with data: {data}")
                self.call_service(service, **data)

            except Exception as e:
                self.log(
                    f"❌ Error executing action {i} in scenario {scenario_id}: {e}")

    def _evaluate_optional_flags(self) -> List[str]:
        """Evaluate conditional entities to determine active flags."""
        flags = []

        for flag_name, entity_id in self.conditional_entities.items():
            try:
                state = self.get_state(entity_id)
                if state == "on":
                    flags.append(flag_name)
            except Exception as e:
                self.log(
                    f"⚠️ Error evaluating flag {flag_name} ({entity_id}): {e}")

        return sorted(flags)  # Sort for consistent scenario IDs

    def _get_room_from_device(self, device_id: str) -> Optional[str]:
        """Map device ID to room name."""
        for room, mapped_device in self.room_mappings.items():
            if mapped_device == device_id:
                return room
        return None

    def _get_room_from_entity(self, entity_id: str) -> Optional[str]:
        """Map entity ID to room name."""
        for room, mapped_entity in self.room_mappings.items():
            if mapped_entity == entity_id:
                return room
        return None

    def _map_button_command(self, command: str) -> str:
        """Map button command to interaction type."""
        command_map = {
            "single": "single_press",
            "double": "double_press",
            "hold": "long_press",
            "release": "release",
            "1_single": "single_press",
            "1_double": "double_press",
            "1_hold": "long_press"
        }
        return command_map.get(command, command)

    def _log_unmatched_scenario(self, scenario_id: str, context: Dict[str, Any]):
        """Log unmatched scenarios for analysis."""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

            log_entry = {
                "scenario_id": scenario_id,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }

            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            self.log(f"📝 Logged unmatched scenario: {scenario_id}")

        except Exception as e:
            self.log(f"❌ Error logging unmatched scenario: {e}")

    def reload_scenarios(self):
        """Reload scenarios from file (for UI integration)."""
        self.scenarios = self._load_scenarios()
        self.log(f"🔄 Reloaded {len(self.scenarios)} scenarios")

    def get_scenario_stats(self) -> Dict[str, Any]:
        """Get statistics about scenarios (for UI)."""
        return {
            "total_scenarios": len(self.scenarios),
            "rooms": list(set(s.split("|")[0] for s in self.scenarios.keys())),
            "last_reload": datetime.now().isoformat()
        }

    def simulate_scenario(self, room: str, interaction_type: str = "manual") -> Dict[str, Any]:
        """Simulate a scenario trigger (for testing)."""
        """Simulate scenario execution for testing purposes."""
        original_test_mode = self.test_mode
        self.test_mode = True

        try:
            self._process_scenario_trigger(
                room=room,
                interaction_type=interaction_type,
                trigger_type="simulation",
                source_entity="nodalink_simulator"
            )
            return {"status": "success", "message": f"Simulated scenario for {room}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            self.test_mode = original_test_mode
