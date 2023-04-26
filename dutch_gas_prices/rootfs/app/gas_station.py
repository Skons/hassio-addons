"""
Dutch Gas prices API Module
"""
import sys
import json
import time, datetime
import logging
from io import BytesIO
import re
from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import math
import pytesseract
from fake_headers import Headers
from dgp_common import _read_cached_jsonfile
from dgp_common import get_logger
from dgp_common import _read_dockerconfig
import pathlib
from os import path

# Settings
CACHE_TIME = 3600
CACHE_TIME_STATIONS = 86400 #24h, could be longer, stations don't come and go very often

logger = get_logger(__name__)
logging.getLogger('PIL').setLevel(logging.WARNING)
cache_path = str(pathlib.Path(__file__).parent.resolve()) + '/cache/'

logger.debug(f"gas_station: Cachepath is '{cache_path}'")

def get_all_stations(fuel):
	"""
	Get all the gas stations from the tankservice app
	:param fuel: The fuel type to get the stations for
	"""

	if fuel == "lpg": #switch to the fuel that the api uses
		fuel = "autogas"

	url = f'https://tankservice.app-it-up.com/Tankservice/v1/places?fmt=web&fuel={fuel}'

	def _write_allstationdata():
		"""
		Query the api and cache the results to a json file
		"""
		headers = Headers(headers=True).generate()

		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries=retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)
		response = session.get(url, headers=headers)
		if response.status_code == 200:
			data = response.json()

			with open(cache_path + f'{fuel}.json', 'w') as outfile:
					json.dump(data, outfile)
		else:
			logger.error(f"_write_allstationdata: statuscode '{response.status_code}'")
			logger.error(f"_write_allstationdata: Used header '{headers}'")
			ip_addr = requests.get('https://api.ipify.org').text
			logger.error(f"_write_allstationdata: Used IP '{ip_addr}'")
			logger.error(f"_write_allstationdata: Response text '{response.text}'")
			data = {}
		return data

	stationdata = _read_cached_jsonfile(cache_path + f'{fuel}.json', CACHE_TIME_STATIONS)
	if stationdata == False:
		logger.debug(f"gas_station: Fuel '{fuel}' new request")
		stationdata = _write_allstationdata()
	else:
		logger.debug(f"gas_station: Fuel '{fuel}' from cache")
	return stationdata

def gas_station(station_id, fuel):
	"""
	Get the fuel price of the specified station
	:param station_id: The id of the station to get the fuel price for
	:param fuel: The fuel type to get the gas price for
	"""
	url = f'https://tankservice.app-it-up.com/Tankservice/v1/places/{station_id}.png'
	addon_config = _read_dockerconfig()

	def _search_value(lines, search_value):
		"""
		OCR logic for Euro 95 en Diesel, TODO rewrite logic, dirty as * now... & Split up....
		"""
		return_value = None
		try:
			word_list = None
			for i, line in enumerate(lines):
				for value in search_value:
					if value in line.lower():
						word_list = line.split()
						break
				if word_list:
					break

			if word_list:
				return_value1 = word_list[-1].replace(',', '.')
				#Sometimes digits get interpreted wrong, correct them here
				return_value1 = return_value1.replace('..','.')
				return_value1 = return_value1.replace('°','9')
				return_value1 = return_value1.replace('?','9')
				return_value1 = return_value1.replace('®','9')
				return_value1 = return_value1.replace('%','8')
				#print(return_value1)
				return_value2 = re.sub("[^0-9,.]", "", return_value1)
				return_value = float(return_value2)
		except Exception as exception_info:
			logger.error(f'_search_value failed: {exception_info}')

		return return_value

	def _write_stationdata(station_id):
		"""
		Query the api and cache the results to a json file
		"""
		headers = Headers(headers=True).generate()

		session = requests.Session()
		retry = Retry(connect=3, backoff_factor=0.5)
		adapter = HTTPAdapter(max_retries=retry)
		session.mount('http://', adapter)
		session.mount('https://', adapter)
		response = session.get(url, headers=headers)
		if response.status_code == 200:
			resize_number = 4
			logo_width = 60
			logo_top = 50
			img = Image.open(BytesIO(response.content))
			img.save(f'{cache_path}{station_id}.png')

			#convert the blue to white
			width = img.size[0]
			height = img.size[1]
			for i in range(0,width):# process all pixels
				for j in range(0,height):
					data = img.getpixel((i,j))
					#print(data) #(255, 255, 255)
					if (data[0]==235 and data[1]==245 and data[2]==249):
						img.putpixel((i,j),(255, 255, 255))

			img2 = img.convert('L') #assign other var, convert does not work otherwise

			#Improve the characteristics of the letters
			img2 = img2.filter(ImageFilter.SHARPEN)

			#Resize the image
			width, height = img2.size
			newsize = (width*resize_number, height*resize_number)
			img2 = img2.resize(newsize) #resize for better ocr

			#replace logo, prevent OCR from reading text. The logo is detectable by background color (#TODO)
			draw = ImageDraw.Draw(img2)
			x0 = ((width*resize_number) - (logo_width*resize_number)) #right corner minus logo
			y0 = 0 #top
			x1 = (width*resize_number) #rigth corner
			y1 = (logo_top*resize_number) #logo size
			logger.debug(f"_write_stationdata: draw logo coverup with coordinates x0: '{x0}', y0: '{y0}', x1: '{x1}', '{y1}'")
			draw.rectangle((x0, y0, x1, y1), fill=255)

			#Improve contrast to have more clear lines. Fiddeling means improvement on some digits and worsening on others
			contrast_enhance = 2
			if 'ocr' in addon_config:
				if 'contrast_enhance' in addon_config['ocr']:
					if type(addon_config['ocr']['contrast_enhance']) == int:
						contrast_enhance = addon_config['ocr']['contrast_enhance']
			logger.debug(f"_write_stationdata: Enhancing contrast with '{contrast_enhance}'")

			img2 = ImageEnhance.Contrast(img2).enhance(contrast_enhance)
			img2.save(f'{cache_path}{station_id}_edit.png')

			#do the ocr
			ocr_result = pytesseract.image_to_string(img2, config='--psm 6 --oem 3') #configure tesseract explicit
			ocr_lines = ocr_result.split("\n")
			ocr_lines = list(filter(None, ocr_lines)) #Filter out empty values
			logger.debug(f"_write_stationdata: OCR lines detected '{ocr_lines}'")

			#lowercase definition of fuels to search
			euro95_prijs = _search_value(ocr_lines, ['euro 95','euro95','(e10)'])
			diesel_prijs = _search_value(ocr_lines, ['diesel','(b7)'])
			lpg_prijs = _search_value(ocr_lines, ['lpg','autogas'])
			cng_prijs = _search_value(ocr_lines, ['cng'])
			euro98_prijs = _search_value(ocr_lines, ['euro 98','euro98','e5'])

			if (euro95_prijs is None) or (diesel_prijs is None):
				data = {
					'station_id': station_id,
					'euro95': euro95_prijs,
					'euro98': euro98_prijs,
					'diesel' : diesel_prijs,
					'lpg' : lpg_prijs,
					'cng' : cng_prijs,
					'station_street' : ocr_lines[0],
					'station_address' : ocr_lines[1],
					'timestamp': datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
					'status' : 'Station exists?'
				}
			else:
				data = {
					'station_id': station_id,
					'euro95': euro95_prijs,
					'euro98': euro98_prijs,
					'diesel' : diesel_prijs,
					'lpg' : lpg_prijs,
					'cng' : cng_prijs,
					'station_street' : ocr_lines[0],
					'station_address' : ocr_lines[1],
					'timestamp': datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
					'status' : 'Ok'
				}

			with open(f'{cache_path}{station_id}.json', 'w') as outfile:
				json.dump(data, outfile)
		else:
			logger.error(f"_write_stationdata '{station_id}': statuscode '{response.status_code}'")
			logger.error(f"_write_stationdata '{station_id}': Used header '{headers}'")
			ip_addr = requests.get('https://api.ipify.org').text
			logger.error(f"_write_stationdata '{station_id}': Used IP '{ip_addr}'")
			logger.error(f"_write_stationdata '{station_id}': Response text '{response.text}'")
			data = {
				'station_id': None,
				'euro95': None,
				'euro98': None,
				'diesel' : None,
				'lpg' : None,
				'cng' : None,
				'station_street' : None,
				'station_address' : None,
				'timestamp' : None,
				'status' : f'{response.status_code}'
			}
		return data

	# Main logic
	request_start =  datetime.datetime.utcnow()
	return_value = _read_cached_jsonfile(f'{cache_path}{station_id}.json', CACHE_TIME)
	if return_value == False:
		logger.debug(f"station: Station id '{station_id}' new request")
		return_value = _write_stationdata(station_id)
	else:
		logger.debug(f"station: Station id '{station_id}' from cache")

	stationdata = get_all_stations(fuel)
	stationinfo = None
	for station in stationdata:
		if station['id'] == int(station_id):
			stationinfo = {}
			stationinfo['brand'] = station['brand']
			stationinfo['name'] = station['name']
			station_lat = str(station['lat'])
			stationinfo['latitude'] = float(station_lat[:2] + "." + station_lat[2:])#quick and dirty conversion of lat lon to float, should not be done this way
			station_lon = str(station['lng'])
			stationinfo['longitude'] = float(station_lon[:1] + "." + station_lon[1:])
			stationinfo['fuel'] = fuel
			break

	return_value['processing_start'] = request_start.replace(tzinfo=datetime.timezone.utc).isoformat()
	processing_end = datetime.datetime.utcnow()
	return_value['processing_time'] = round(processing_end.timestamp() - request_start.timestamp(),2)

	if return_value['station_id'] is not None:
		price = return_value[fuel]
		status = return_value['status']
		station_id = return_value['station_id']

		image_path = cache_path + str(return_value['station_id']) + ".png"
		prepped_image_path = cache_path + str(return_value['station_id']) + "_edit.png"
		if not path.exists(image_path):
			image_path = ""
		if not path.exists(prepped_image_path):
			prepped_image_path = ""

		newdata = {
			'station_id': station_id,
			'price': price,
			'fuel_type': fuel,
			'station_street' : return_value['station_street'],
			'station_address' : return_value['station_address'],
			'timestamp' : return_value['timestamp'],
			'status' : status,
			'processing_start': return_value['processing_start'],
			'processing_time': return_value['processing_time'],
			'image': image_path,
			'prepped_image': prepped_image_path
		}
		#merge the station information
		return_value = {**newdata, **stationinfo}

	logger.debug(f"station '{station_id}': return value '{return_value}'")

	return return_value

if __name__ == '__main__':
	#if called upon directly, use gas_station.py [stationid] or gas_station.py [station_id] [fuel_type]
	gas_station(str(sys.argv[1]),str(sys.argv[2])) 
