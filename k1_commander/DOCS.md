# Home Assistant Add-on: K1 Commander

K1 Commander runs ELRO Connects which will command the SF40GA system.

## Configuration

Add-on configuration:

```yaml
k1_hostname: ELRO_K1
k1_id: ST_xxxxxxxxxxxx
mqtt_host: homeassistant.local
mqtt_port: 1883
mqtt_username: username
mqtt_password: password
mqtt_base_topic: base_topic
```

### Option: `k1_hostname` (required)

The hostname or ip of the K1 connector.

### Option: `k1_id` (required)

The ID of the K1 connector (format is ST_xxxxxxxxxxxx).

### Option: `log_level`

The `log_level` option controls the level of logging. Possible values are:

- critical
- error
- warning
- info
- debug

### Option: `mqtt_host` (optional)

The DNS or IP address of your MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `mqtt_port` (optional)

The port number of your MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `mqtt_username` (optional)

The username used to connect to the MQTT host

### Option: `mqtt_password` (optional)

The password used to connect to the MQTT host

### Option: `mqtt_base_topic` (required)

The base topic used for MQTT