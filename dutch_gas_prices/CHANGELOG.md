# Changelog

## 2021.11.8.1

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