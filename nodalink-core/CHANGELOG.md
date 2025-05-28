# Changelog


## [1.0.6] - 2025-05-28
### Fixed
- Resolved logging startup failure (`bashio::log.level.notice: command not found`)
- Updated logging to follow latest best practices for HA add-ons
- Added bashio installation to Dockerfile for proper Home Assistant add-on logging
- Implemented robust logging functions with graceful fallbacks
- Enhanced startup script stability and error handling

## 1.0.5
- Fixed unbound variable error in startup script
- Improved variable initialization and error handling in run.sh
- Enhanced environment variable handling with proper defaults
- Fixed CORS origins configuration parsing
- Improved process management and health checks 

## 1.0.4
- Enhanced startup script with improved error handling and stability
- Added restart limits to prevent restart loops
- Improved service health checks with exponential backoff
- Added startup logging to track add-on history

## 1.0.3
- Initial release with combined AppDaemon + FastAPI services
- Added real-time WebSocket updates
- Unified configuration management