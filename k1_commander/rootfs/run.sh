#!/usr/bin/env bashio
set -e

# Create main config
K1_HOSTNAME=$(bashio::config 'k1_hostname')
LOG_LEVEL=$(bashio::config 'log_level')

if bashio::config.has_value 'mqtt_host'; then
    MQTT_HOST=$(bashio::config 'mqtt_host')
else
    MQTT_HOST=$(bashio::services mqtt "host")
fi

if bashio::config.has_value 'mqtt_port'; then
    MQTT_PORT=$(bashio::config 'mqtt_port')
else
    MQTT_PORT=$(bashio::services mqtt "port")
fi

if bashio::config.has_value 'mqtt_username'; then
    MQTT_USERNAME=$(bashio::config 'mqtt_username')
else
    MQTT_USERNAME=$(bashio::services mqtt "username")
fi

if bashio::config.has_value 'mqtt_password'; then
    MQTT_PASSWORD=$(bashio::config 'mqtt_password')
else
    MQTT_PASSWORD=$(bashio::services mqtt "password")
fi

MQTT_BASE_TOPIC="-b $(bashio::config 'mqtt_base_topic')"

#build the connect string
MQTT_AUTHORIZATION="${MQTT_USERNAME}:${MQTT_PASSWORD}@"

if bashio::config.has_value 'k1_id'; then
    K1_ID="-i $(bashio::config 'k1_id')"
else
    K1_ID=''
fi

export SUPERVISOR_URL="http://supervisor/core"

#log some info
bashio::log.info "Log_level: ${LOG_LEVEL}"
bashio::log.info "hostname: ${K1_HOSTNAME}"
bashio::log.info "k1 id: ${K1_ID}"
bashio::log.info "mqtt_host: ${MQTT_HOST}"
bashio::log.info "mqtt_port: ${MQTT_PORT}"
bashio::log.info "mqtt_base_topic: ${MQTT_BASE_TOPIC}"
bashio::log.debug "mqtt_username: ${MQTT_USERNAME}"
bashio::log.debug "mqtt_password: ${MQTT_PASSWORD}"
bashio::log.debug "mqtt_authorization: ${MQTT_AUTHORIZATION}"
bashio::log.info "Starting K1 Commander..."

#start the addon
elro -k ${K1_HOSTNAME} -m "mqtt://${MQTT_AUTHORIZATION}${MQTT_HOST}:${MQTT_PORT}" ${MQTT_BASE_TOPIC} ${K1_ID} -a
