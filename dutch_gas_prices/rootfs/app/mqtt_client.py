import json
import jsonschema
from jsonschema import validate
import os
import threading
import sys
import datetime
import threading
from pathlib import Path
from time import sleep
from gas_station import gas_station
from gas_stations import gas_stations
from dgp_common import get_logger

import paho.mqtt.client as mqtt

logger = get_logger(__name__)
mqtt_client = None

#JSON schema's
gas_stations_schema = {
	"type": "object",
	"properties": {
		"fuel_type": { 
			"type": "string",
			"enum": ["euro95","euro98","diesel","autogas"] 
		},
		"radius": {
			"type": "integer",
			"minimum": 1,
			"maximum": 15,
		},
		"longitude": {"type": "number"},
		"latitude": {"type": "number"},
		"publish_all": {"type": "boolean"},
	},
	"additionalProperties": False,
	"minProperties": 4
}

gas_station_schema = {
	"type": "object",
	"properties": {
		"fuel_type": { 
			"type": "string",
			"enum": ["euro95","euro98","diesel","autogas"] 
		},
		"station_id": {"type": "integer"},
	},
	"additionalProperties": False,
	"minProperties": 2
}

def on_connect(client, userdata, flags, rc):
	logger.info("Connected with result code {0}".format(str(rc)))
	mqtt_topics = [("dgp/gas_station",0),("dgp/gas_stations",0)]
	client.subscribe(mqtt_topics)

def on_disconnect(client, userdata, rc):
	if rc != 0:
		timeout = 15
		logger.error(f"mqtt client lost connection. Will try to reconnect once in {timeout}s.")
		sleep(timeout)
		logger.debug("Trying to reconnect")
		client.reconnect()

def on_message(client, userdata, message):
	global is_discovered_topic,is_discovered_status_topic
	payload = message.payload.decode("utf-8","ignore")
	if message.topic == 'dgp/gas_station': #process a single gas station
		dgp_station_status = {}
		dgp_station_status['request_start'] = datetime.datetime.utcnow()
		dgp_station_status['request_type'] = 'gas_station'
		logger.info(f"Received payload on topic '{message.topic}'")
		try:
			data = json.loads(payload)
		except Exception as exception_info:
			logger.error(f"Unable to process payload: '{exception_info}'")

		boolGetStation = True
		try:
			validate(instance=data, schema=gas_station_schema)
		except jsonschema.exceptions.ValidationError as err:
			boolGetStation = False
			logger.error(f"unable to validate payload for gas_station with error '{err}'")

		if boolGetStation:
			try:
				result = gas_station(int(data['station_id']),data['fuel_type'])
				if 'station_id' in result:
					dgp_station_status['number_of_stations'] = len(result)
					t = threading.Thread(target=publish_station, args=(client,result,dgp_station_status))
					t.start() #do not wait, on_message needs to be free
				else:
					logger.warning("There was no gas station in the result")
			except Exception as exception_info:
				logger.error(f"Unable to process stationid '{data['station_id']}' with fuel_type '{data['fuel_type']}' '{exception_info}'")

	elif message.topic == 'dgp/gas_stations': #process gas stations within a radius
		dgp_stations_status = {}
		dgp_stations_status['request_start'] = datetime.datetime.utcnow()
		dgp_stations_status['request_type'] = 'gas_stations'
		logger.info(f"Received payload on topic '{message.topic}'")
		try:
			data = json.loads(payload)
		except Exception as exception_info:
			logger.error(f"Unable to process payload: '{exception_info}'")

		boolGetStations = True
		try:
			validate(instance=data, schema=gas_stations_schema)
		except jsonschema.exceptions.ValidationError as err:
			boolGetStations = False
			logger.error(f"unable to validate payload for gas_stations with error '{err}'")

		if boolGetStations:
			try:
				result = gas_stations(data['fuel_type'],data['longitude'],data['latitude'],int(data['radius']))
				if 'gas_stations' in result:
					if isinstance(result['gas_stations'], list):
						dgp_stations_status['number_of_stations'] = len(result['gas_stations'])
						t = threading.Thread(target=publish_stations, args=(client,result['gas_stations'],data['publish_all'],dgp_stations_status))
						t.start() #do not wait, on_message must be free
					else:
						logger.error("There are no gas stations retunred")
				else:
					logger.warning("The result of gas stations does not have gas_stations")
			except Exception as exception_info:
				logger.error(f"Unable to process payload '{data}' with error '{exception_info}'")

	elif message.topic.startswith("homeassistant/sensor/dgp_gasstation/"): #just register the topic where a publish has taken place
		logger.debug(f"on_message: received the topic '{message.topic}'")
		is_discovered_topic = message.topic
	elif message.topic.startswith("homeassistant/sensor/dgp/"): #just register the topic where a publish has taken place
		logger.debug(f"on_message: received the topic '{message.topic}'")
		is_discovered_status_topic = message.topic
	else:
		logger.info(f"Unkown topic '{message.topic}'")

def publish_station(client,station_info,status=None,lowestprice=0):
	global is_discovered_topic
	is_discovered_topic = None

	logger.info(f"publishing station_id {station_info['station_id']} to mqtt")

	stationtopic = f"{station_info['station_id']}_{station_info['fuel_type']}"
	stationname = f"Gas station {station_info['station_street']} {station_info['fuel_type']}"
	if lowestprice > 0:
		stationtopic = f"{station_info['fuel_type']}_lowestprice_{lowestprice}"
		stationname = f"Gas station {station_info['fuel_type']} lowest price {lowestprice}"

	topic = f"homeassistant/sensor/dgp_gasstation/{stationtopic}/config"
	client.subscribe(topic)
	#send the sensor as autodiscover to home assistant
	result_ad = client.publish(
		topic,
		json.dumps(
			{
				"name": stationname,
				"icon": "mdi:fuel",
				"state_topic": f"homeassistant/sensor/dgp_gasstation/{stationtopic}/state",
				"json_attributes_topic": f"homeassistant/sensor/dgp_gasstation/{stationtopic}/attr",
				"unit_of_measurement": "€",
				"unique_id": f"gasstation_{stationtopic}",
			}
		)
	)

	#the messages are queued by paho, and it seems to be impossible to flush them. With this hacky method we wait until the new sensor shows up in it's HA discovery topic
	#when it shows up we can continue. if we do now wait until the sensor is discovered, it will show up with state unknown
	counter = 0
	while topic != is_discovered_topic:
		sleep(1) #do not stress the CPU
		counter += 1
		logger.debug(f"publish: Waiting for discovery on topic '{topic}'")
		if counter > 5:
			logger.warning(f"publish: the sensor has not shown up in the topic '{topic}', the state can show up as 'unkown'")
			break

	client.unsubscribe(topic) #unsubscribe, it is no longer needed

	#send all information
	result_state = mqtt_client.publish(f"homeassistant/sensor/dgp_gasstation/{stationtopic}/state",station_info['price'])
	result_attrs = mqtt_client.publish(f"homeassistant/sensor/dgp_gasstation/{stationtopic}/attr",json.dumps(station_info))

	logger.debug(
		f"publish: Autodiscover '{bool(result_ad.rc == mqtt.MQTT_ERR_SUCCESS)}', "
		f"State '{bool(result_state.rc == mqtt.MQTT_ERR_SUCCESS)}' and "
		f"Attributes '{bool(result_attrs.rc == mqtt.MQTT_ERR_SUCCESS)}'"
	)

	logger.info(f"publishing station_id {station_info['station_id']} done")
	if status is not None:
		publish_status(client,status)

def publish_stations(client,stations_info,publish_all,status):
	logger.info("publishing stations to mqtt")
	counter = 1
	for item in stations_info:
		if publish_all is True:
			publish_station(client,item)
		if counter < 4:
			publish_station(mqtt_client,item, None,counter) #publish also for lowest_price_[counter]
		counter += 1

	logger.info("publishing stations done")

	publish_status(client,status)

def publish_status(client,status):
	global is_discovered_status_topic
	is_discovered_status_topic = None

	logger.info("publishing status to mqtt")

	topic = f"homeassistant/sensor/dgp/status/config"
	client.subscribe(topic)
	result_ad = client.publish(
		topic,
		json.dumps(
			{
				"name": "Dutch gas prices status",
				"icon": "mdi:fuel",
				"state_topic": f"homeassistant/sensor/dgp/status/state",
				"json_attributes_topic": f"homeassistant/sensor/dgp/status/attr",
				"unit_of_measurement": "seconds",
				"unique_id": f"dgp_status",
			}
		)
	)

	#the messages are queued by paho, and it seems to be impossible to flush them. With this hacky method we wait until the new sensor shows up in it's HA discovery topic
	#when it shows up we can continue. if we do now wait until the sensor is discovered, it will show up with state unknown
	counter = 0
	while topic != is_discovered_status_topic:
		sleep(1) #do not stress the CPU
		counter += 1
		logger.debug(f"publish: Waiting for discovery on topic '{topic}'")
		if counter > 5:
			logger.warning(f"publish: the sensor has not shown up in the topic '{topic}', the state can show up as 'unkown'")
			break

	client.unsubscribe(topic) #unsubscribe, it is no longer needed

	processing_end = datetime.datetime.utcnow()
	status['processing_time'] = round(processing_end.timestamp() - status['request_start'].timestamp(),2)
	status['request_start'] = str(status['request_start'].replace(tzinfo=datetime.timezone.utc).isoformat())

	#send all information
	result_state = mqtt_client.publish(f"homeassistant/sensor/dgp/status/state",status['processing_time'])
	result_attrs = mqtt_client.publish(f"homeassistant/sensor/dgp/status/attr",json.dumps(status))

	logger.debug(
		f"publish: Autodiscover '{bool(result_ad.rc == mqtt.MQTT_ERR_SUCCESS)}', "
		f"State '{bool(result_state.rc == mqtt.MQTT_ERR_SUCCESS)}' and "
		f"Attributes '{bool(result_attrs.rc == mqtt.MQTT_ERR_SUCCESS)}'"
	)

	logger.info("publishing status done")

def start_mqtt_client(mqtthost, mqttport, mqttusername=None, mqttpassword=None):
	global mqtt_client

	logger.info("Connecting mqtt")
	mqtt_client = mqtt.Client("dutch_gas_prices")
	if mqttusername:
		mqtt_client.username_pw_set(username=mqttusername, password=mqttpassword)
	mqtt_client.on_connect = on_connect
	mqtt_client.on_message = on_message
	mqtt_client.on_disconnect = on_disconnect
	mqtt_client.connect(host=mqtthost, port=int(mqttport))
	mqtt_client.loop_forever()
if __name__ == "__main__":
	#if called upon directly, use mqtt_client.py [mqtt_server] [mqtt_port] or mqtt_client.py [mqtt_server] [mqtt_port] [mqtt_username] [mqtt_password]
	if len(sys.argv) > 3:
		start_mqtt_client(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]),str(sys.argv[4]))
	else:
		start_mqtt_client(str(sys.argv[1]),str(sys.argv[2]))
