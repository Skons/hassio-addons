# Home Assistant Add-on: Dutch gas prices

Get information about fuel prices in the netherlands

## Configuration Options

### Option: `log_level`

The `log_level` option controls the level of logging. Possible values are:

- critical
- error
- warning
- info
- debug

### Option: `mqtt_host`

The DNS or IP address of your MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `mqtt_port`

The port number of your MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `mqtt_username`

The username used to connect to the MQTT host

### Option: `mqtt_password`

The password used to connect to the MQTT host

## Home Assistant Sensor

MQTT is used to automatically have sensors discovered. A sensor per gas station and per fuel_type will appear alongside the sensor.dutch_gas_prices_status. The latter one will provide information about the processing time.

The following fuel_type can be used in the payloads below.
- euro95
- euro98
- diesel
- lpg

### Gas stations based on location and radius

Create an automation that will send a JSON payload to the correct MQTT topic

```yaml
automation:
- alias: Update gas stations
  trigger:
    - platform: time_pattern
      minutes: 5 #every 5 minute past whole
  action:
  - service: mqtt.publish
    data:
      topic: 'dgp/gas_stations'
      payload_template: '{"fuel_type":"euro95","radius":5,"latitude":{{ state_attr("person.skons", "latitude") }},"longitude":{{ state_attr("person.skons", "longitude") }}, "to_publish":3}'
```

With to_publish you can determine how many of the discovered gas stations will show up, the default is 3. Gas stations with the lowest price will show up as:

```
sensor.gas_station_[fuel_type]_lowest_price_1
sensor.gas_station_[fuel_type]_lowest_price_2
sensor.gas_station_[fuel_type]_lowest_price_3
```

This is what can be used as payload:

```json
{
  "fuel_type": "euro95",
  "radius": 5, #in kilometers, maximum 15
  "latitude": 6,
  "longitude": 53,
  "to_publish": 3 #Optional, default 3,
  "friendly_name_template": "[brand] ([station_street])" #Optional, change the friendly name by using the attributes
}
```

To get a notification for the lowest gas station price after the latest price has been retreived, use the following automation:

```yaml
- alias: Notify lowest price gas station
  trigger:
  - platform: state
    entity_id: sensor.gas_station_[fuel_type]_lowest_price_1
  action:
  - service: notify.mobile_app_ios
    data:
      title: Cheapest gas station
      message: 'Gas costs € {{ states.sensor.gas_station_[fuel_type]_lowest_price_1.state }} at {{ state_attr("sensor.gas_station_[fuel_type]_lowest_price_1","station_street") }}. '
      data:
        url: https://www.google.com/maps/search/?api=1&query={{ state_attr("sensor.gas_station_[fuel_type]_lowest_price_1","latitude") }},{{ state_attr("sensor.gas_station_[fuel_type]_lowest_price_1", "longitude") }}
```

### Gas stations based on id

Get the fuel_type information of a specific gas station. To get the ID of the gas station, go to https://directlease.nl/tankservice/ and click the gas station. Right click on the image and click open in new tab. ####.png is the id of your station.

```yaml
automation:
- alias: Update gas station
  trigger:
    - platform: time_pattern
      minutes: 5 #every 5 minute past whole
  action:
  - service: mqtt.publish
    data:
      topic: 'dgp/gas_station'
      payload: '{"station_id":####,"fuel_type":"euro95"}'
```

This is what can be used as payload:

```json
{
  "fuel_type": "euro95",
  "station_id": 1,
  "friendly_name_template": "[brand] ([station_street])" #Optional, change the friendly name by using the attributes
}
```

### Friendly name
The friendly name can be configured by adding "friendly_name_template" to the MQTT payload. The value can contain every attribute you want which allows you to have a friendly name you desire. This could look something like this:

```json
"friendly_name_template": "[brand] ([station_street])"

```

Note: the attributes between the sensors from station based on radius and station based on id are different.

## ToDo

- Better error reporting for the MQTT client

## Troubleshooting

- First check in the log of the addon if the addon is up and running
- Check for log the addon is providing in the log file if things don't work out as expected

## Known Issues

- On an RPi3 the installation could crash the system, a retry of the installation should fix it
- Secure MQTT communication is not supported
- If [Error -3] appears in the logging, and a DNS server is also running within Home Assistant, try to point HA to an external DNS server
- aarch64 and i386 have not been tested
- zone.home is initialized after the rest sensor, so the first query after a reboot will fail