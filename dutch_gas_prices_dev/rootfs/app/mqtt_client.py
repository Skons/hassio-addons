import json
import jsonschema
from jsonschema import validate
import os
import threading
import sys
import datetime
from datetime import  timezone
import threading
import requests
from pathlib import Path
from time import sleep
from gas_station import gas_station
from gas_stations import gas_stations
from dgp_common import get_logger

import paho.mqtt.client as mqtt
import base64

logger = get_logger(__name__)
mqtt_client = None

#JSON schema's
gas_stations_schema = {
	"type": "object",
	"properties": {
		"fuel_type": { 
			"type": "string",
			"enum": ["euro95","euro98","diesel","cng","lpg"] 
		},
		"identifier": { 
			"type": "string",
			"pattern": "^[a-z0-9]{0,10}$"
		},
		"radius": {
			"type": "integer",
			"minimum": 1,
			"maximum": 15,
		},
		"longitude": {"type": "number"},
		"latitude": {"type": "number"},
		"to_publish": {
			"type": "integer",
			"minimum": 1
		},
		"friendly_name_template": {"type": "string"},
	},
	"required": ["fuel_type", "radius","longitude","latitude"]
}

gas_station_schema = {
	"type": "object",
	"properties": {
		"fuel_type": { 
			"type": "string",
			"enum": ["euro95","euro98","diesel","cng","lpg"] 
		},
		"station_id": {"type": "integer"},
		"friendly_name_template": {"type": "string"},
	},
	"required": ["fuel_type", "station_id"]
}

def on_connect(client, userdata, flags, rc):
	"""
	This function handles the MQTT client connect
	:param client: The MQTT client
	:param userdata: The userdata is user defined data which isn’t normally used.
	:param flags: Flags for paho mqtt
	:param rc: The response code
	"""
	logger.info("Connected with result code {0}".format(str(rc)))
	mqtt_topics = [("dgp/gas_station",0),("dgp/gas_stations",0)]
	client.subscribe(mqtt_topics)

def on_disconnect(client, userdata, rc):
	"""
	This function handles the MQTT client disconnects
	:param client: The MQTT client
	:param userdata: The userdata is user defined data which isn’t normally used.
	:param rc: The response code
	"""
	if rc != 0:
		timeout = 15
		logger.error(f"mqtt client lost connection. Will try to reconnect once in {timeout}s.")
		sleep(timeout)
		logger.debug("Trying to reconnect")
		client.reconnect()

def on_message(client, userdata, message):
	"""
	This function handles the MQTT messages
	:param client: The MQTT client
	:param userdata: The userdata is user defined data which isn’t normally used.
	:param message: The message published
	"""
	global is_discovered_topic,is_discovered_status_topic
	payload = message.payload.decode("utf-8","ignore")
	if message.topic == 'dgp/gas_station': #process a single gas station
		dgp_station_status = {}
		dgp_station_status['request_start'] = datetime.datetime.utcnow()
		dgp_station_status['request_type'] = 'gas_station'
		logger.info(f"Received payload '{payload}' on topic '{message.topic}'")
		json_payload = None
		try:
			json_payload = json.loads(payload)
		except Exception as exception_info:
			logger.error(f"Unable to process gas_station payload '{payload}' with error: '{exception_info}'")

		boolGetStation = False
		if json_payload is not None:
			boolGetStation = True
			try:
				validate(instance=json_payload, schema=gas_station_schema)
			except jsonschema.exceptions.ValidationError as err:
				boolGetStation = False
				logger.error(f"Unable to validate payload '{payload}' for gas_station with error: '{err}'")

		if boolGetStation:
			try:
				result = gas_station(int(json_payload['station_id']),json_payload['fuel_type'])
				if 'station_id' in result:
					dgp_station_status['number_of_stations'] = len(result)
					t = threading.Thread(target=publish_station, args=(client,json_payload,result,dgp_station_status))
					t.start() #start multithreading of the station processing, on_message needs to be free
				else:
					logger.warning(f"Gas station with id '{json_payload['station_id']}' was not found")
			except Exception as exception_info:
				logger.error(f"Unable to process stationid '{json_payload['station_id']}' with fuel_type '{json_payload['fuel_type']}', error: '{exception_info}'")

	elif message.topic == 'dgp/gas_stations': #process gas stations within a radius
		dgp_stations_status = {}
		dgp_stations_status['request_start'] = datetime.datetime.utcnow()
		dgp_stations_status['request_type'] = 'gas_stations'
		logger.info(f"Received payload '{payload}' on topic '{message.topic}'")
		json_payload = None
		try:
			json_payload = json.loads(payload)
		except Exception as exception_info:
			logger.error(f"Unable to process gas_stations payload '{payload}' with error: '{exception_info}'")

		boolGetStations = False
		if json_payload is not None:
			boolGetStations = True
			try:
				validate(instance=json_payload, schema=gas_stations_schema)
			except jsonschema.exceptions.ValidationError as err:
				boolGetStations = False
				logger.error(f"unable to validate payload '{payload}' for gas_stations with error: '{err}'")

		if boolGetStations:
			#start the request, processing and publishing in a seperate request, it could take long
			t = threading.Thread(target=publish_stations, args=(client,json_payload,dgp_stations_status))
			t.start() #do not wait, on_message must be free

	elif message.topic.startswith("homeassistant/sensor/dgp_gas_station/"): #just register the topic where a publish has taken place
		logger.debug(f"on_message: received the topic '{message.topic}'")
		is_discovered_topic = message.topic
	elif message.topic.startswith("homeassistant/sensor/dgp/"): #just register the topic where a publish has taken place
		logger.debug(f"on_message: received the topic '{message.topic}'")
		is_discovered_status_topic = message.topic
	else:
		logger.info(f"Unkown topic '{message.topic}'")

def publish_station(client,station_request,station_info,status=None,lowestprice=0):
	"""
	publish the station to home assistant
	:param client: The MQTT client
	:param station_request: The request used to get the station data
	:param station_info: The station from gas_station.py or gas_stations.py
	:param status: status object used for publis_status()
	:param lowestprice: if is 0, the station will be published. Any other number will publish the number of lowest price stations
	"""
	global is_discovered_topic
	is_discovered_topic = None

	logger.info(f"publishing station_id {station_info['station_id']} to mqtt")

	stationtopic = f"{station_info['station_id']}_{station_info['fuel_type']}"
	sensorname = f"gas_station_{station_info['station_id']}_{station_info['fuel_type']}"
	if lowestprice > 0:
		stationtopic = f"{station_info['fuel_type']}_lowestprice_{lowestprice}"
		sensorname = f"gas_station_{station_info['fuel_type']}_lowest_price_{lowestprice}"
		if 'identifier' in station_request: #add identifier to the sensor
			stationtopic = f"{station_info['fuel_type']}_{station_request['identifier']}_lowestprice_{lowestprice}"
			sensorname = f"gas_station_{station_info['fuel_type']}_{station_request['identifier']}_lowest_price_{lowestprice}"

	topic = f"homeassistant/sensor/dgp_gas_station/{stationtopic}/config"
	client.subscribe(topic)
	#send the sensor as autodiscover to home assistant
	result_ad = client.publish(
		topic,
		json.dumps(
			{
				"name": f"gas_station_{stationtopic}",
				"icon": "mdi:fuel",
				"state_topic": f"homeassistant/sensor/dgp_gas_station/{stationtopic}/state",
				"json_attributes_topic": f"homeassistant/sensor/dgp_gas_station/{stationtopic}/attr",
				"unit_of_measurement": "€",
				"unique_id": f"gas_station_{stationtopic}",
			}
		)
	)

	#the messages are queued by paho, and it seems to be impossible to flush them. With this hacky method we wait until the new sensor shows up in it's HA discovery topic
	#when it shows up we can continue. if we do now wait until the sensor is discovered, it will show up with state unknown
	counter = 0
	while topic != is_discovered_topic:
		sleep(1) #do not stress the CPU
		counter += 1
		logger.debug(f"publish_station: Waiting for discovery on topic '{topic}'")
		if counter > 5:
			logger.warning(f"publish_station: the sensor has not shown up in the topic '{topic}', the state can show up as 'unkown'")
			break

	client.unsubscribe(topic) #unsubscribe, it is no longer needed

	#Append friendly_name if there is a template provided
	friendly_name = "[brand] ([station_street])"
	if 'friendly_name_template' in station_request:
		friendly_name = station_request['friendly_name_template']

	for key in station_info.keys():
		friendly_name = friendly_name.replace(f"[{key}]",f"{station_info[key]}")
	station_info["friendly_name"] = friendly_name

	#send all information,
	#result_state = mqtt_client.publish(f"homeassistant/sensor/dgp_gas_station/{stationtopic}/state",station_info['price'])
	#result_attrs = mqtt_client.publish(f"homeassistant/sensor/dgp_gas_station/{stationtopic}/attr",json.dumps(station_info))

	try:
		logger.debug(f"publish_station: Publish station data for station id '{station_info['station_id']}'.")
		mqtt_client.publish(f"dgp/{station_info['station_id']}/{station_info['fuel_type']}",station_info['price'])
		mqtt_client.publish(f"dgp/{station_info['station_id']}/timestamp",datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat())
		if station_info['image']:
			with open(station_info['image'],'rb') as file:
				#filecontent = file.read() # byte array
				filecontent = "data:image/png;base64," + str(base64.b64encode(file.read()))[2:-1]
			mqtt_client.publish(f"dgp/{station_info['station_id']}/image",filecontent)
			mqtt_client.publish(f"dgp/{station_info['station_id']}/image_timestamp",str(datetime.datetime.fromtimestamp(os.path.getmtime(station_info['image']), tz=timezone.utc).isoformat()))
		if station_info['prepped_image']:
			with open(station_info['prepped_image'],'rb') as file:
				#filecontent = file.read() # byte array
				filecontent = "data:image/png;base64," + str(base64.b64encode(file.read()))[2:-1]
			mqtt_client.publish(f"dgp/{station_info['station_id']}/prepped_image",filecontent)
			mqtt_client.publish(f"dgp/{station_info['station_id']}/prepped_image_timestamp",str(datetime.datetime.fromtimestamp(os.path.getmtime(station_info['prepped_image']), tz=timezone.utc).isoformat()))
	except Exception as exception_info:
		logger.error(f"publish_station: Unable to publish data for station id '{station_info['station_id']}' with error: '{exception_info}'")

	#it is not possible to publish the friendly_name over MQTT, therefore the home assistant api is used
	#discovery is still done with mqtt
	supervisor_url = os.environ.get("SUPERVISOR_URL")
	sensor_url = f"{supervisor_url}/api/states/sensor.{sensorname}"
	supervisor_token = os.environ.get("SUPERVISOR_TOKEN")
	station_info['icon'] = "mdi:fuel" #icon is lost with direct publishing, resend it
	station_info['unit_of_measurement'] = "€" #unit of measurement is lost with direct publishing, resend it
	if supervisor_token is None:
		logger.warning("publish_station: Unable to find the environment variable SUPERVISOR_TOKEN")
	elif supervisor_url is None:
		logger.warning("publish_station: Unable to find the environment variable SUPERVISOR_URL")
	else:
		logger.debug(f"publish_station: Setting sensor values to url '{sensor_url}' with token")
		obj = {}
		obj["state"] = station_info['price']
		ok = station_info.pop("image", None)
		ok = station_info.pop("prepped_image", None)
		obj["attributes"] = station_info

		headers = {}
		headers["Authorization"] = f"Bearer {supervisor_token}"
		headers["Content-Type"] = "application/json"

		try:
			g = requests.get(sensor_url, headers=headers, timeout=10)
			logger.debug('publish_station: get = %s',g)
			r = requests.post(sensor_url, json=obj, headers=headers, timeout=10)
			logger.debug('publish_station: Status Code  = %s',r.status_code)
			return r.status_code
		except requests.exceptions.RequestException as e:  # This is the correct syntax
			logger.error('%s', e)
			return ""

	logger.debug(
		f"publish_station: Autodiscover '{bool(result_ad.rc == mqtt.MQTT_ERR_SUCCESS)}'"
	)

	logger.info(f"publishing station_id {station_info['station_id']} done")

	if status is not None:
		publish_status(client,status)

def publish_stations(client,station_request,status):
	"""
	publish all stations to home assistant
	:param client: The MQTT client
	:param station_request: The request used to get the stations data
	:param status: status object used for publis_status()
	"""
	try:
		result = gas_stations(station_request['fuel_type'],station_request['longitude'],station_request['latitude'],int(station_request['radius']))
		if 'gas_stations' in result:
			if isinstance(result['gas_stations'], list):
				status['number_of_stations'] = len(result['gas_stations'])
				logger.info("publishing stations to mqtt")
				counter = 1
				range = 3
				if "to_publish" in station_request:
					range = int(station_request["to_publish"])

				logger.debug(f"publish_stations: Publishing the top '{range}' lowest price gas stations")
				for item in result['gas_stations']:
					if counter <= range:
						publish_station(mqtt_client,station_request,item, None,counter) #publish also for lowest_price_[counter]
					counter += 1

				logger.info("publishing stations done")
			else:
				logger.error(f"No gas stations where found in the longitude '{station_request['longitude']}' and latitude '{station_request['latitude']}'")
		else:
			logger.warning("publish_stations: The result of gas stations does not have the property gas_stations")
	except Exception as exception_info:
		logger.error(f"Unable to process station_request payload '{station_request}' with error: '{exception_info}'")

	publish_status(client,status)

def publish_status(client,status):
	"""
	publish the status of the request to home assistant as a sensor
	:param client: The MQTT client
	:param status: status object
	"""
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
		logger.debug(f"publish_status: Waiting for discovery on topic '{topic}'")
		if counter > 5:
			logger.warning(f"publish_status: the sensor has not shown up in the topic '{topic}', the state can show up as 'unkown'")
			break

	client.unsubscribe(topic) #unsubscribe, it is no longer needed

	processing_end = datetime.datetime.utcnow()
	status['processing_time'] = round(processing_end.timestamp() - status['request_start'].timestamp(),2)
	status['request_start'] = str(status['request_start'].replace(tzinfo=datetime.timezone.utc).isoformat())
	status['icon'] = "mdi:fuel"

	#send all information
	result_state = mqtt_client.publish(f"homeassistant/sensor/dgp/status/state",status['processing_time'])
	result_attrs = mqtt_client.publish(f"homeassistant/sensor/dgp/status/attr",json.dumps(status))

	logger.debug(
		f"publish_status: Autodiscover '{bool(result_ad.rc == mqtt.MQTT_ERR_SUCCESS)}', "
		f"State '{bool(result_state.rc == mqtt.MQTT_ERR_SUCCESS)}' and "
		f"Attributes '{bool(result_attrs.rc == mqtt.MQTT_ERR_SUCCESS)}'"
	)

	logger.info("publishing status done")

def start_mqtt_client(mqtthost, mqttport, mqttusername=None, mqttpassword=None):
	"""
	Initialize the MQTT client
	:param mqtthost: The host or ip of the MQTT instance
	:param mqttport: The port of the MQTT instance
	:param mqttusername: The username for authentication
	:param mqttpassword: The password for authentication
	"""
	global mqtt_client

	logger.info("Connecting mqtt")
	mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "dutch_gas_prices")
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
