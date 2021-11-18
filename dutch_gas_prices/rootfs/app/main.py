import logging
import os
import threading
import sys
from pathlib import Path
from time import sleep
from mqtt_client import start_mqtt_client
from dgp_common import get_logger

def start(loglevel, mqtthost, mqttport, mqttusername=None, mqttpassword=None):
	os.environ["LOG_LEVEL"] = loglevel.upper()
	logger = get_logger(__name__)

	logger.info("DGP initialized, launching client")
	while True: #keep alive loop
		start_mqtt_client(mqtthost,mqttport,mqttusername,mqttpassword)
		logger.info("mqtt client has stopped, trying again in 10 seconds")
		sleep(10)

if __name__ == "__main__":
	#if called upon directly, use main.py [loglevel] [mqtt_server] [mqtt_port] or main.py [loglevel] [mqtt_server] [mqtt_port] [mqtt_username] [mqtt_password]
	if len(sys.argv) > 4:
		start(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3]),str(sys.argv[4]),str(sys.argv[5]))
	else:
		start(str(sys.argv[1]),str(sys.argv[2]),str(sys.argv[3])) 
