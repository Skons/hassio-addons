# Changelog

## 2023.8.11.1
- Fixed issue [#50](https://github.com/Skons/hassio-addons/issues/50)

## 2023.8.7.1
- Fixed issue [#51](https://github.com/Skons/hassio-addons/issues/51)
- Hopefully fixed issue [#50](https://github.com/Skons/hassio-addons/issues/50)
- Fixed issue [#52](https://github.com/Skons/hassio-addons/issues/52)

## 2023.4.26.1

- Fixed issue [#44](https://github.com/Skons/hassio-addons/issues/44)
- The image, and the image edited for tesseract, are now send to the MQTT topic dgp/[station-id]

## 2023.4.21.1

- Fixed issue [#45](https://github.com/Skons/hassio-addons/issues/45)
- Switched to base-python image version 10.1.2
- Switched from config.json to config.yaml
- MQTT Username and Password provided by the supervisor can now be used
- Introduced apparmor.txt

## 2023.4.16.1

- Fixed issue [#40](https://github.com/Skons/hassio-addons/issues/40)
- Improved logging

## 2022.3.25.1

- Added the ability to use a unique identifier for the cheapest gas station sensors
- Documentation updates

## 2022.3.21.1

- Fixed the error Unable to process payload '...' with error: ''<' not supported between instances of 'NoneType' and 'float''
- LPG (autogas) is now correctly supported
- CNG as fueltype is added

## 2022.2.27.1

- Fixed bug when station id is unknown
- When the price per liter is higher then €10, it will be marked as unable to read
- Improved logging

## 2022.2.16.1

**Important**: The sensor name for a single gas station is changed to its id instead of the street address

- Single gas stations sensor name is changed to the id of the station
- Unit of measurement is now always set
- Sensor attributes for a single station is now the same as for a within radius request
- Friendly name for single gas stations is now default "[brand] ([station_street])"
- Error reporting updates
- Documentation improvements


## 2022.1.2.1

- Interaction with the tankservice website is more reliable
- Improved OCR, superscript digits are now recognized

## 2021.11.10.1

**Important**: This addon no longer relies on uvicorn and fastapi, it now makes use of MQTT. This chanage is **breaking** please read the docs

- Switched to MQTT
- The sensors are renamed

## 2021.11.2.1

- Documentation updates
- Added request_start, request_end and request_duration for the gas_stations api call
- Fixed error 17 when trying to install DGP

## 2021.8.10.1

- Documentation updates
- Centralised multiple functions
- OCR will now retreive the street and address. This is not functioning properly yet. The logo should not be OCR'ed, to prevent this the location of the logo in the picture is assumed. Expect errornous addresses.

**Important**: The property OCR_Station is not used anymore, station_street and station_address have taken its place

## 2021.7.16.3

- Documentation updates
- Added arguments parsing for direct calling .py files

## 2021.7.16.2

- Documentation updates
- Fixed a bug in gas_prices.py

## 2021.7.16.1

- First release