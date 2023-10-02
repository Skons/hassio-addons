#!/usr/bin/with-contenv bashio
set -e

# Create main config
LOG_LEVEL=$(bashio::config 'log_level')
if bashio::config.has_value 'mqtt_host'; then
    MQTT_HOST=$(bashio::config 'mqtt_host')
else
    MQTT_HOST=$(bashio::services mqtt 'host')
fi

if bashio::config.has_value 'mqtt_port'; then
    MQTT_PORT=$(bashio::config 'mqtt_port')
else
    MQTT_PORT=$(bashio::services mqtt 'port')
fi

if bashio::config.has_value 'mqtt_username'; then
    MQTT_USERNAME=$(bashio::config 'mqtt_username')
else
    MQTT_USERNAME=$(bashio::services mqtt 'username')
fi

if bashio::config.has_value 'mqtt_password'; then
    MQTT_PASSWORD=$(bashio::config 'mqtt_password')
else
    MQTT_PASSWORD=$(bashio::services mqtt 'password')
fi

export SUPERVISOR_URL="http://supervisor/core"

#log some info
bashio::log.info "Log_level: ${LOG_LEVEL}"
bashio::log.info "mqtt_host: ${MQTT_HOST}"
bashio::log.info "mqtt_port: ${MQTT_PORT}"
bashio::log.debug "mqtt_username: ${MQTT_USERNAME}"
bashio::log.debug "mqtt_password: ${MQTT_PASSWORD}"
bashio::log.info "Starting dutch gas prices..."

#start the addon
python main.py ${LOG_LEVEL} ${MQTT_HOST} ${MQTT_PORT} ${MQTT_USERNAME} ${MQTT_PASSWORD}