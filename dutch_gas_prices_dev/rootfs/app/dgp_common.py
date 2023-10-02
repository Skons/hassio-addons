"""
Dutch Gas prices Common Functions
"""
import os
import time
import json
import logging
import sys

def _read_cached_jsonfile(filename, cachetime):
	try:
		age_of_file = time.time() - os.path.getmtime(filename)
	except IOError:
		age_of_file = 99999999

	if age_of_file < cachetime:
		with open(filename) as json_file:
			data = json.load(json_file)
			return data
	else:
		return False

def _read_dockerconfig():
	"""
	Read the docker config
	"""
	with open('/data/options.json') as json_file:
		data = json.load(json_file)
		return data

def get_logger(mod_name):
	logger = logging.getLogger(__name__)
	loglevel = os.environ.get("LOG_LEVEL", "DEBUG").upper()
	logging.basicConfig(
		format='[%(asctime)s] %(levelname)-8s: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
		level=loglevel
	)

	return logger
