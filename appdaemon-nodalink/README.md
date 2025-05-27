# Nodalink AppDaemon Engine

Context-aware automation engine for Home Assistant using AppDaemon.

## Features

- **Context-Aware Processing**: Matches scenarios based on room, time, day type, and conditions
- **Flexible Scenario System**: JSON-based scenario definitions with optional flags
- **Conditional Logic**: Support for conditional entities and fallback scenarios
- **Time Bucketing**: Configurable time-based scenario matching
- **Test Mode**: Safe testing without executing actual actions
- **Comprehensive Logging**: Detailed logging of unmatched scenarios for optimization

## Configuration

All configuration is managed through the shared configuration files that are automatically created on first run.

## Dependencies

This add-on requires the Nodalink API Server to be running for configuration management.
