#!/usr/bin/env bashio
set -e

# Create main config
LOG_LEVEL=$(bashio::config 'log_level')

bashio::log.info "Starting dutch gas prices..."

exec uvicorn --proxy-headers --host 0.0.0.0 --port 5035 --log-level ${LOG_LEVEL} api:app