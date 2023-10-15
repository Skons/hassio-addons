# Home Assistant Add-on: Dutch gas prices

Get information about fuel prices in the netherlands

## Configuration

Add-on configuration:

```yaml
mqtt_host: homeassistant.local
mqtt_port: 1883
mqtt_username: username
mqtt_password: password
ocr:
  contrast_enhance: 2
```

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

The username used to connect to the MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `mqtt_password` (optional)

The password used to connect to the MQTT host. If you are running mosquitto on HA, you do not need to configure this option.

### Option: `ocr.contrast_enhance` (optional)

While preprocessing the fuel station image, the contrast is enhanced. By default this is done by a factor of 2. Results may vary upon changing this value. If tesseract OCR is not performing, change this value to see if better results are achieved. This option changes [ImageEnhance](https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html) of the PIL addin

## Home Assistant Sensor

MQTT is used to automatically have sensors discovered. A sensor per gas station and per `fuel_type` will appear alongside the sensor.dutch_gas_prices_status. The latter one will provide information about the processing time.

The following `fuel_type` can be used in the payloads below.
- euro95
- euro98
- diesel
- lpg
- cng

When LPG is used, a station that provides autogas as fuel will also be returned

### Gas stations based on location and radius

Create an automation that will send a JSON payload to the correct MQTT topic. Replace `person.skons` with an entity that has latitude and longitude attributes.

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

With `to_publish` you can determine how many of the cheapest discovered gas stations, within the defined radius of a location, will show up. Gas stations with the lowest price will show up as:

```
sensor.gas_station_[fuel_type]_lowest_price_1
sensor.gas_station_[fuel_type]_lowest_price_2
sensor.gas_station_[fuel_type]_lowest_price_3
```

This is the JSON payload that can be used:

```json
{
  "fuel_type": "euro95",
  "radius": 5, #in kilometers, maximum 15
  "latitude": 53,
  "longitude": 6,
  "identifier": "uniquename", #Optional
  "to_publish": 3, #Optional, default 3
  "friendly_name_template": "[brand] ([station_street])" #Optional
}
```

To get a notification for the lowest gas station price after the latest price has been retreived, use the following automation. Replace `[fuel_type]` with your fuel type:

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
#### identifier

The identifier is only available for the list of cheapest gas stations. This can be used to get a list associated with a user, car or whatever is needed. By default the sensor will be named `sensor.gas_station_[fuel_type]_lowest_price_1`. When identifier is specified, the sensor name will be `sensor.gas_station_[fuel_type]_[identifier]_lowest_price_1`. Only the characters a-z0-9, with a maximum of 10 characters, can be used.

#### to_publish

The number of cheapest gas stations that will be published to Home Assistant.

#### friendly_name_template

Define if a different friendly name is needed. All the attributes of the sensor can be used by providing them within brackets. For instance when `[station_street]` is used, it will be replaced by the name of the street of the station which could be `Some street 10`. See the attributes of the sensor to see what can be used.

### Gas stations based on id

Get the `fuel_type` price information of a specific gas station. To get the ID of the gas station, go to https://directlease.nl/tankservice/ and click the gas station. Right click on the image and click open in new tab. `####.png` is the id of your station.

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

This is the JSON payload that can be used:

```json
{
  "fuel_type": "euro95",
  "station_id": 1,
  "friendly_name_template": "[brand] ([station_street])" #Optional, change the friendly name by using the attributes of the sensor
}
```

### Friendly name
The friendly name can be configured by adding `friendly_name_template` to the MQTT payload. The value can contain every attribute you want which allows you to have a friendly name you desire. This could look something like below. Please note that not all brands are known.:

```json
"friendly_name_template": "[brand] ([station_street])"

```

Note: the attributes between the sensors from station based on radius and station based on id are different.

## ToDo

- Better error reporting for the MQTT client

## Troubleshooting

- First check in the log of the addon if the addon is up and running
- Enable debug logging to see if there is additional information that could help you fix the problem
- Check for log the addon is providing in the log file if things don't work out as expected. If debug is enabled, please redact the username and password information in the log.

## Known Issues

- On an RPi3 the installation could crash the system, a retry of the installation should fix it
- Secure MQTT communication is not supported
- If [Error -3] appears in the logging, and a DNS server is also running within Home Assistant, try to point HA to an external DNS server
- i386 has not been tested