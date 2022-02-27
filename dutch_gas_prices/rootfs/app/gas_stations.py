"""
Dutch Gas stations API Module
"""
import sys
import json
import logging
import time
from io import BytesIO
import re
from PIL import Image
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pytesseract
from fake_headers import Headers
from geopy import distance
from gas_station import gas_station
from gas_station import get_all_stations
from dgp_common import _read_cached_jsonfile
from dgp_common import get_logger

logger = get_logger(__name__)

def gas_stations(fuel,longitude,latitude,radius):
	"""
	Get the prices of the gas stations within a radius for a specific location
	:param fuel: The fuel type to get the gas price for
	:param longitude: The longitude of the location to get the gas stations for
	:param latitude: The latitude of the location to get the gas stations for
	:param radius: The radius in kilomters to get the gas stations for
	"""

	def is_location_in_radius(lat, lon, station_lat, station_lon, km):
		center_point = [{'lat': lat, 'lng': lon}]
		test_point = [{'lat': station_lat, 'lng': station_lon}]
		radius = float(km) # in kilometer

		center_point_tuple = tuple(center_point[0].values())
		test_point_tuple = tuple(test_point[0].values())

		dis = distance.distance(center_point_tuple, test_point_tuple).km

		if dis <= radius:
			return True # location is within radius
		else:
			return False

	# Main logic
	stationdata = get_all_stations(fuel)

	stations = []
	for station in stationdata:
		"""
		Loop through all stations and find if they are within radius
		"""
		station_lat = str(station['lat'])
		station_latitude = float(station_lat[:2] + "." + station_lat[2:])#quick and dirty conversion of lat lon to float, should not be done this way
		station_lon = str(station['lng'])
		station_longitude = float(station_lon[:1] + "." + station_lon[1:])
		return_value = is_location_in_radius(latitude, longitude, station_latitude, station_longitude, radius)
		if return_value is True:
			gasprices = gas_station(station['id'], fuel) #get the corresponding gas station and its prices
			if 'price' in gasprices:
				stations.append(gasprices)

	return_value = {}
	return_value['gas_stations'] = sorted(stations, key=lambda x: x['price'], reverse=False) #sort on price, cheapest first
	logger.info(f"There are '{len(stations)}' stations within range")
	logger.debug(f"stations: return value '{return_value}'")
	return return_value

if __name__ == '__main__':
	gas_stations(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]), str(sys.argv[4])) #if called upon directly, use gas_stations.py [fueltype] [longitude] [latitude] [radius]
