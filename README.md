# Home Assistant Configuration & Nodalink Add-ons

This repository contains my Home Assistant configuration files and the Nodalink Home Assistant Add-ons.

## Nodalink Add-ons

This repository serves as a custom Home Assistant add-on repository containing three add-ons that provide a complete context-aware automation solution:

### 🔗 Nodalink AppDaemon Engine
The core automation engine that processes scenarios and executes actions based on context.

### 🚀 Nodalink API Server  
FastAPI REST server for managing scenarios and configuration.

### 🎨 Nodalink Frontend
Modern Vue.js web interface for visual scenario editing.

## Add-on Installation

1. In Home Assistant, go to **Supervisor** → **Add-on Store**
2. Click the **⋮** menu and select **Repositories**
3. Add this repository URL: `https://github.com/hampusandersson01/hass-config`
4. The Nodalink add-ons will appear in your add-on store

Install the add-ons in this order:
1. Nodalink AppDaemon Engine
2. Nodalink API Server  
3. Nodalink Frontend

After installation, access the web interface at `http://your-ha-ip:3000`

## Home Assistant Configuration

The `config/` and `appdaemon/` directories contain my personal Home Assistant setup.
