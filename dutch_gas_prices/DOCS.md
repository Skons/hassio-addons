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

MQTT is used to automatically have sensors discovered. There will be a sensor per gas station if a specific gas station based on id is configured. All gas stations that appear within a radius will also appear if publish_all is set to true. And a list of lowest priced gas stations per fuel_type will appear if the radius is used. The sensor.dutch_gas_prices_status will always be there and it will provide information about the processing time.

The following fuel_type can be used in the payloads below.
- euro95
- euro98
- diesel
- lpg

### Gas stations based on location and radius

Create an automation that will send a JSON payload to the correct MQTT topic. After triggering this automation, all gas stations within the specified radius will be parsed. The radius cannot be larger then 15km.

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
      payload_template: '{"fuel_type":"euro95","radius":5,"latitude":{{ state_attr("person.skons", "latitude") }},"longitude":{{ state_attr("person.skons", "longitude") }}, "publish_all":false}'
```

If you want all gas stations within the specified radius to appear in Home Assistant, set publish_all to true. Gas stations with the lowest price will show up as:

```
sensor.gas_station_[fuel_type]_lowest_price_1
sensor.gas_station_[fuel_type]_lowest_price_2
sensor.gas_station_[fuel_type]_lowest_price_3
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

## ToDo

- Better error reporting for the MQTT client

## Troubleshooting

- First check in the log of the addon if the addon is up and running
- Check for log the addon is providing in the log file if things don't work out as expected

## Known Issues

- Secure MQTT communication is not supported
- If [Error -3] appears in the logging, and a DNS server is also running within Home Assistant, try to point HA to an external DNS server
- aarch64 and i386 have not been tested
- zone.home is initialized after the rest sensor, so the first query after a reboot will fail