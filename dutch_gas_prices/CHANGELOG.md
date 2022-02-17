# Changelog

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