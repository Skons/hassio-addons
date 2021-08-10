# Home Assistant Add-on: Dutch gas prices

Get information about fuel prices in the netherlands

## Configuration Options

### Option: `log_level`

The `log_level` option controls the level of log output by uvicorn. Possible values are:

- critical
- error
- warning
- info
- debug
- trace

## Home Assistant Sensor

This addon only provides an API. To get the information into Home Assistant, a REST call is needed to query the API.

### Gas stations based on location and radius

First we need a sensor where the attributes is filled with all stations in the specified radius. For the fuel the following can be used
-euro95
-euro98
-diesel
-lpg

```yaml
sensor:
- platform: rest
  name: Gas stations within radius
  scan_interval: 600
  timeout: 180
  resource_template: http://homeassistant.local:5035/api/v1/gas_stations/euro95?radius=5&longitude={{ state_attr("zone.home", "longitude") }}&latitude={{ state_attr("zone.home", "latitude") }}
  method: GET
  json_attributes:
    - gas_stations
  value_template: >
    {{ value_json.gas_stations | length }}
```

Next you will need to create a pyton script to convert the attributes of the REST sensor into sperate entities. Follow this https://www.home-assistant.io/integrations/python_script/ first to get started with python scripts. Then save this script as dutch_gas_prices.py

```python
gas_stations_attributes = hass.states.get('sensor.gas_stations_within_radius').attributes

index = 0
sensor_name = ""
entry = {}
entities = {}
entities['entity_id'] = []
try:
    for item in gas_stations_attributes['gas_stations']:
        if item.get('prijs'):
            entry = {
                "brand" : item.get('brand'),
                "name" : item.get('name'),
                "longitude" : float(item.get('longitude')),
                "latitude" : float(item.get('latitude')),
                "street" : str(item.get('station_street')),
                "address" : str(item.get('station_address')),
                "prijs" : item.get('prijs'),
                "timestamp" : str(item.get('timestamp')),
                "friendly_name" : item.get('name') + " (" + item.get('brand') + ")"
            }
            index= index+1
            sensor_name = 'gasstation.' + str(index)
            entities['entity_id'].append(sensor_name) #used for a group
            hass.states.set(sensor_name, entry['prijs'], entry)
except:
    logger.warn('Error in dutch_gas_prices.py')

#set the group
hass.states.set('group.gasstations', index, entities)
```

This automation will convert the gas stations into separate entities every minute.

```yaml
automation:
- alias: Update gas stations
  trigger:
  - minutes: /1
    platform: time_pattern
  action:
  - service: python_script.dutch_gas_prices
```

### Gas stations based on id

Get the gas information of a specific gas station. To get the ID of the gas station, go to https://directlease.nl/tankservice/ and click the gas station. Right click on the image and click open in new tab. xxxx.png is the id of your station.

```yaml
sensor:
- platform: rest
  name: Gas station
  scan_interval: 600
  resource_template: http://homeassistant.local:5035/api/v1/gas_prices/0000
  method: GET
  json_attributes:
    - station_id
    - euro95
    - euro98
    - diesel
    - lpg
    - ocr_station
    - timestamp
  value_template: >
    {{ value_json.status }}
```

## Troubleshooting

- First check in the log of the addon if the addon is up and running
- Also check for the response the addon is providing in the log file if things don't work out as expected
- To check if there should be results, go to http://homeassistant.local:5035/docs and try to query the addon directly

## Known Issues

- There are cases where the installation causes a crash, after a reboot, you can retry the installation
- If [Error -3] appears in the logging, and a DNS server is also running within Home Assistant, try to point HA to an external DNS server
- aarch64 and i386 have not been tested
- zone.home is initialized after the rest sensor, so the first query after a reboot will fail