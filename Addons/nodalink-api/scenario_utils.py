"""
Nodalink Scenario Utilities
Utility functions for context parsing, ID building, and validation.
"""

import re
import json
from datetime import datetime, time
from typing import List, Dict, Any, Optional, Union
import calendar


def get_time_bucket(current_time: datetime, bucket_minutes: int = 60) -> str:
    """
    Convert current time to a time bucket string.

    Args:
        current_time: Current datetime
        bucket_minutes: Minutes per bucket (default 60)

    Returns:
        Time bucket string like "08-09" or "14-15"
    """
    hour = current_time.hour

    if bucket_minutes == 60:
        # Hour-based buckets
        next_hour = (hour + 1) % 24
        return f"{hour:02d}-{next_hour:02d}"

    elif bucket_minutes == 30:
        # 30-minute buckets
        minute = current_time.minute
        if minute < 30:
            start_min = 0
            end_min = 30
        else:
            start_min = 30
            end_min = 0
            hour = (hour + 1) % 24
        return f"{current_time.hour:02d}:{start_min:02d}-{hour:02d}:{end_min:02d}"

    elif bucket_minutes == 15:
        # 15-minute buckets
        minute = current_time.minute
        bucket_start = (minute // 15) * 15
        bucket_end = bucket_start + 15
        end_hour = hour

        if bucket_end == 60:
            bucket_end = 0
            end_hour = (hour + 1) % 24

        return f"{hour:02d}:{bucket_start:02d}-{end_hour:02d}:{bucket_end:02d}"

    else:
        # Custom bucket size
        total_minutes = hour * 60 + current_time.minute
        bucket_index = total_minutes // bucket_minutes
        start_minutes = bucket_index * bucket_minutes
        end_minutes = start_minutes + bucket_minutes

        start_hour = start_minutes // 60
        start_min = start_minutes % 60
        end_hour = end_minutes // 60
        end_min = end_minutes % 60

        return f"{start_hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}"


def get_day_type(current_time: datetime) -> str:
    """
    Determine day type (weekday/weekend).

    Args:
        current_time: Current datetime

    Returns:
        "weekday" or "weekend"
    """
    weekday = current_time.weekday()  # Monday = 0, Sunday = 6
    return "weekend" if weekday >= 5 else "weekday"


def build_scenario_id(
    room: str,
    time_bucket: str,
    day_type: str = "",
    optional_flags: Optional[List[str]] = None,
    interaction_type: str = ""
) -> str:
    """
    Build a scenario ID from components.

    Args:
        room: Room name
        time_bucket: Time bucket string
        day_type: Day type (weekday/weekend)
        optional_flags: List of optional flags
        interaction_type: Type of interaction

    Returns:
        Scenario ID string like "kitchen|08-09|weekday|christmas_mode|single_press"
    """
    components = [room, time_bucket]

    if day_type:
        components.append(day_type)

    if optional_flags:
        flags_str = "+".join(sorted(optional_flags))
        components.append(flags_str)

    if interaction_type:
        components.append(interaction_type)

    return "|".join(components)


def parse_scenario_id(scenario_id: str) -> Dict[str, Any]:
    """
    Parse a scenario ID into its components.

    Args:
        scenario_id: Scenario ID string

    Returns:
        Dictionary with parsed components
    """
    parts = scenario_id.split("|")

    result = {
        "room": parts[0] if len(parts) > 0 else "",
        "time_bucket": parts[1] if len(parts) > 1 else "",
        "day_type": parts[2] if len(parts) > 2 else "",
        "optional_flags": parts[3].split("+") if len(parts) > 3 and parts[3] else [],
        "interaction_type": parts[4] if len(parts) > 4 else ""
    }

    return result


def validate_scenario_id(scenario_id: str) -> Dict[str, Any]:
    """
    Validate a scenario ID format.

    Args:
        scenario_id: Scenario ID to validate

    Returns:
        Dictionary with validation result and errors
    """
    errors = []

    if not scenario_id:
        errors.append("Scenario ID cannot be empty")
        return {"valid": False, "errors": errors}

    parts = scenario_id.split("|")

    # Check minimum requirements
    if len(parts) < 2:
        errors.append("Scenario ID must have at least room and time_bucket")

    # Validate room
    room = parts[0] if len(parts) > 0 else ""
    if not room or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', room):
        errors.append(
            "Room must be a valid identifier (letters, numbers, underscore)")

    # Validate time bucket
    time_bucket = parts[1] if len(parts) > 1 else ""
    if not time_bucket or not re.match(r'^\d{2}[-:]\d{2}(-\d{2}[-:]\d{2})?$', time_bucket):
        errors.append("Time bucket must be in format HH-HH or HH:MM-HH:MM")

    # Validate day type
    if len(parts) > 2 and parts[2]:
        day_type = parts[2]
        if day_type not in ["weekday", "weekend"]:
            errors.append("Day type must be 'weekday' or 'weekend'")

    # Validate optional flags
    if len(parts) > 3 and parts[3]:
        flags = parts[3].split("+")
        for flag in flags:
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', flag):
                errors.append(f"Invalid flag format: {flag}")

    # Validate interaction type
    if len(parts) > 4 and parts[4]:
        interaction_type = parts[4]
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', interaction_type):
            errors.append("Interaction type must be a valid identifier")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "components": parse_scenario_id(scenario_id) if len(errors) == 0 else None
    }


def validate_service_call(action: Dict[str, Any]) -> bool:
    """
    Validate a Home Assistant service call.

    Args:
        action: Action dictionary

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(action, dict):
        return False

    # Check for required fields
    service = action.get(
        "service") or f"{action.get('domain', '')}.{action.get('action', '')}"

    if not service or "." not in service:
        return False

    domain, service_name = service.split(".", 1)

    # Validate domain format
    if not re.match(r'^[a-z_][a-z0-9_]*$', domain):
        return False

    # Validate service name format
    if not re.match(r'^[a-z_][a-z0-9_]*$', service_name):
        return False

    return True


def sanitize_entity_id(entity_id: str) -> str:
    """
    Sanitize entity ID to prevent injection attacks.

    Args:
        entity_id: Entity ID to sanitize

    Returns:
        Sanitized entity ID
    """
    if not entity_id:
        return ""

    # Remove any characters that aren't alphanumeric, underscore, or dot
    sanitized = re.sub(r'[^a-zA-Z0-9_.]', '', entity_id)

    # Ensure it has the correct format (domain.entity)
    if "." not in sanitized:
        return ""

    domain, entity = sanitized.split(".", 1)

    # Validate domain and entity parts
    if not re.match(r'^[a-z_][a-z0-9_]*$', domain):
        return ""

    if not re.match(r'^[a-zA-Z0-9_]+$', entity):
        return ""

    return f"{domain}.{entity}"


def evaluate_conditions(conditions: List[Dict[str, Any]], hass_instance) -> bool:
    """
    Evaluate a list of conditions.

    Args:
        conditions: List of condition dictionaries
        hass_instance: Home Assistant instance for state checking

    Returns:
        True if all conditions pass, False otherwise
    """
    if not conditions:
        return True

    for condition in conditions:
        try:
            condition_type = condition.get("condition", "state")

            if condition_type == "state":
                entity_id = condition.get("entity_id")
                expected_state = condition.get("state")

                if not entity_id or expected_state is None:
                    return False

                current_state = hass_instance.get_state(entity_id)
                if current_state != expected_state:
                    return False

            elif condition_type == "numeric_state":
                entity_id = condition.get("entity_id")
                above = condition.get("above")
                below = condition.get("below")

                if not entity_id:
                    return False

                try:
                    current_value = float(hass_instance.get_state(entity_id))

                    if above is not None and current_value <= above:
                        return False

                    if below is not None and current_value >= below:
                        return False

                except (ValueError, TypeError):
                    return False

            elif condition_type == "time":
                after = condition.get("after")
                before = condition.get("before")
                current_time = datetime.now().time()

                if after and current_time < time.fromisoformat(after):
                    return False

                if before and current_time > time.fromisoformat(before):
                    return False

            # Add more condition types as needed

        except Exception as e:
            # Log error in production
            return False

    return True


def generate_time_buckets(bucket_minutes: int = 60) -> List[str]:
    """
    Generate all possible time buckets for a given bucket size.

    Args:
        bucket_minutes: Minutes per bucket

    Returns:
        List of time bucket strings
    """
    buckets = []

    if bucket_minutes == 60:
        # Hour-based buckets
        for hour in range(24):
            next_hour = (hour + 1) % 24
            buckets.append(f"{hour:02d}-{next_hour:02d}")

    elif bucket_minutes == 30:
        # 30-minute buckets
        for hour in range(24):
            buckets.append(f"{hour:02d}:00-{hour:02d}:30")
            next_hour = (hour + 1) % 24
            buckets.append(f"{hour:02d}:30-{next_hour:02d}:00")

    elif bucket_minutes == 15:
        # 15-minute buckets
        for hour in range(24):
            for quarter in range(4):
                start_min = quarter * 15
                end_min = start_min + 15
                end_hour = hour

                if end_min == 60:
                    end_min = 0
                    end_hour = (hour + 1) % 24

                buckets.append(
                    f"{hour:02d}:{start_min:02d}-{end_hour:02d}:{end_min:02d}")

    return buckets


def get_scenario_suggestions(unmatched_log_file: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get scenario suggestions from unmatched log entries.

    Args:
        unmatched_log_file: Path to unmatched scenarios log
        limit: Maximum number of suggestions

    Returns:
        List of scenario suggestions
    """
    suggestions = {}

    try:
        with open(unmatched_log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    scenario_id = entry.get("scenario_id", "")

                    if scenario_id in suggestions:
                        suggestions[scenario_id]["count"] += 1
                        suggestions[scenario_id]["last_seen"] = entry.get(
                            "timestamp", "")
                    else:
                        suggestions[scenario_id] = {
                            "scenario_id": scenario_id,
                            "count": 1,
                            "first_seen": entry.get("timestamp", ""),
                            "last_seen": entry.get("timestamp", ""),
                            "context": entry.get("context", {})
                        }

                except json.JSONDecodeError:
                    continue

    except FileNotFoundError:
        return []

    # Sort by frequency and recency
    sorted_suggestions = sorted(
        suggestions.values(),
        key=lambda x: (x["count"], x["last_seen"]),
        reverse=True
    )

    return sorted_suggestions[:limit]


def export_scenarios_to_csv(scenarios: Dict[str, List[Dict[str, Any]]], output_file: str):
    """
    Export scenarios to CSV format for analysis.

    Args:
        scenarios: Scenarios dictionary
        output_file: Output CSV file path
    """
    import csv

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'scenario_id', 'room', 'time_bucket', 'day_type',
            'optional_flags', 'interaction_type', 'action_count', 'actions'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for scenario_id, actions in scenarios.items():
            components = parse_scenario_id(scenario_id)

            writer.writerow({
                'scenario_id': scenario_id,
                'room': components['room'],
                'time_bucket': components['time_bucket'],
                'day_type': components['day_type'],
                'optional_flags': '+'.join(components['optional_flags']),
                'interaction_type': components['interaction_type'],
                'action_count': len(actions),
                'actions': json.dumps(actions)
            })


def create_default_scenarios() -> Dict[str, List[Dict[str, Any]]]:
    """
    Create a set of default scenarios for common use cases.

    Returns:
        Dictionary of default scenarios
    """
    return {
        # Living room presence detection during evening
        "living_room|18-19|weekday|presence_detected": [
            {
                "service": "light.turn_on",
                "entity_id": "light.living_room",
                "data": {"brightness": 180, "color_temp": 300}
            }
        ],

        # Kitchen morning routine
        "kitchen|07-08|weekday|single_press": [
            {
                "service": "scene.turn_on",
                "entity_id": "scene.kitchen_morning"
            },
            {
                "service": "media_player.play_media",
                "entity_id": "media_player.kitchen_speaker",
                "data": {
                    "media_content_id": "morning_playlist",
                    "media_content_type": "playlist"
                }
            }
        ],

        # Bedroom night mode
        "bedroom|22-23|night_mode|presence_detected": [
            {
                "service": "light.turn_on",
                "entity_id": "light.bedroom_nightlight",
                "data": {"brightness": 20, "rgb_color": [255, 100, 100]}
            }
        ],

        # Office focus mode
        "office|focus_mode|single_press": [
            {
                "service": "light.turn_on",
                "entity_id": "light.office_desk",
                "data": {"brightness": 255, "color_temp": 250}
            },
            {
                "service": "switch.turn_off",
                "entity_id": "switch.office_music"
            }
        ]
    }


def validate_scenarios_file(scenarios: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Validate an entire scenarios file.

    Args:
        scenarios: Scenarios dictionary to validate

    Returns:
        Validation result with errors and warnings
    """
    errors = []
    warnings = []

    for scenario_id, actions in scenarios.items():
        # Validate scenario ID
        id_validation = validate_scenario_id(scenario_id)
        if not id_validation["valid"]:
            errors.extend(
                [f"Scenario '{scenario_id}': {error}" for error in id_validation["errors"]])

        # Validate actions
        if not isinstance(actions, list):
            errors.append(f"Scenario '{scenario_id}': Actions must be a list")
            continue

        if not actions:
            warnings.append(f"Scenario '{scenario_id}': No actions defined")
            continue

        for i, action in enumerate(actions):
            if not validate_service_call(action):
                errors.append(
                    f"Scenario '{scenario_id}': Invalid action {i}: {action}")

    # Check for duplicate scenarios (might indicate mistakes)
    action_signatures = {}
    for scenario_id, actions in scenarios.items():
        signature = json.dumps(actions, sort_keys=True)
        if signature in action_signatures:
            warnings.append(
                f"Scenarios '{scenario_id}' and '{action_signatures[signature]}' have identical actions")
        else:
            action_signatures[signature] = scenario_id

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_scenarios": len(scenarios),
        "total_actions": sum(len(actions) for actions in scenarios.values())
    }
