# Home Assistant Add-on: Dutch gas prices

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

![Current version][version] ![Project Stage][project-stage-shield]

***This addon is experimental, you could see some unexpected behaviour***

Get the latest gas prices from dutch gas stations.

## About

This addon retreives the latest gas prices from dutch gas stations and sends those prices to an MQTT broker. It is possible to get prices for specific gas stations, or to get prices from gas stations within a certain radius. The data is acquired from https://directlease.nl/tankservice/, but it is only available as an image. Tesseract is used to process those images, so there is no guarantee that the data is correct. The concept is based upon https://github.com/sanderdw/Dutch-Gas-prices-API.

This addon can work on a RPi3, please see known issues in the docs for more information.

## Installation

1. Make sure MQTT is installed
2. Create a snapshot before installing this addon
3. Navigate in your Home Assistant frontend to **Supervisor** -> **Add-on Store** and add this URL as an additional repository: `https://github.com/skons/hassio-addons`
4. Find the "Dutch gas stations" add-on and click the "INSTALL" button.
5. Configure the add-on and click on "START".

## Configuration

Configure MQTT in the addon and create automations to send a payload into this plugin whenever you want.

Please check the **[Documentation](https://github.com/skons/hassio-addons/blob/master/dutch_gas_prices/DOCS.md)** for a complete reference of all configuration options.

## Want to contribute?

Any kind of help or useful input/feedback is appreciated! If you want to create a pull request, please create it against the `dev` branch.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[version]: https://img.shields.io/badge/version-v2023.8.11.1-blue.svg
[ex]: https://img.shields.io/badge/project%20stage-experimental-yellow.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-experimental-yellow.svg
