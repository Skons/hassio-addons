"""
Dutch Gas prices API Module
"""
import sys
import json
import time, datetime
from io import BytesIO
import re
from PIL import Image, ImageEnhance, ImageDraw
import requests
import math
import pytesseract
from fake_headers import Headers
from dgp_common import _read_cached_jsonfile
from dgp_common import get_logger

# Settings
# Something like lru_cache would be nice but has no time expiring support, so custom json storage
CACHE_TIME = 3600

logger = get_logger(__name__)

def gas_station(station_id, fuel = None):
	"""
	Main Dutch Gas prices API Function
	"""
	url = f'https://tankservice.app-it-up.com/Tankservice/v1/places/{station_id}.png'

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

		response = requests.get(url, headers=headers)
		if response.status_code == 200:
			img = Image.open(BytesIO(response.content))
			img2 = img.convert('L') #assign other var, convert does not work otherwise
			width, height = img2.size
			newsize = (width*2, height*2)
			img2 = img2.resize(newsize) #resize for better ocr
			draw = ImageDraw.Draw(img2)
			draw.rectangle((((width*2) - 160), 100, (width*2), 0), fill=240) #replace logo, prevent OCR from reading text. The logo is detectable by background color (#TODO)
			img2.save(f'cache/{station_id}.png')

			ocr_result = pytesseract.image_to_string(img2, config='--psm 6 --oem 3') #configure tesseract explicit
			ocr_lines = ocr_result.split("\n")
			ocr_lines = list(filter(None, ocr_lines)) #Filter out empty values

			#lowercase definition of fuels to search
			euro95_prijs = _search_value(ocr_lines, ['euro 95','euro95','(e10)'])
			diesel_prijs = _search_value(ocr_lines, ['diesel','(b7)'])
			lpg_prijs = _search_value(ocr_lines, ['lpg'])
			euro98_prijs = _search_value(ocr_lines, ['euro 98','euro98','e5'])

			if (euro95_prijs is None) or (diesel_prijs is None):
				data = {
					'station_id': station_id,
					'euro95': euro95_prijs,
					'euro98': euro98_prijs,
					'diesel' : diesel_prijs,
					'lpg' : lpg_prijs,
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
					'station_street' : ocr_lines[0],
					'station_address' : ocr_lines[1],
					'timestamp': datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
					'status' : 'Ok'
				}

			with open('cache/' + f'{station_id}.json', 'w') as outfile:
				json.dump(data, outfile)
		else:
			logger.error(f"_write_stationdata: statuscode '{response.status_code}'")
			logger.error(f"_write_stationdata: Used header '{headers}'")
			ip_addr = requests.get('https://api.ipify.org').text
			logger.error(f"_write_stationdata: Used IP '{ip_addr}'")
			logger.error(f"_write_stationdata: Response text '{response.text}'")
			data = {
				'station_id': None,
				'euro95': None,
				'euro98': None,
				'diesel' : None,
				'lpg' : None,
				'station_street' : None,
				'station_address' : None,
				'timestamp' : None,
				'status' : f'{response.status_code}'
			}
		return data

	# Main logic
	request_start =  datetime.datetime.utcnow()
	return_value = _read_cached_jsonfile('cache/' + f'{station_id}.json', CACHE_TIME)
	if return_value == False:
		logger.debug(f"Station id '{station_id}' new request")
		return_value = _write_stationdata(station_id)

	return_value['processing_start'] = request_start.replace(tzinfo=datetime.timezone.utc).isoformat()
	processing_end = datetime.datetime.utcnow()
	return_value['processing_time'] = round(processing_end.timestamp() - request_start.timestamp(),2)
	#Only return the fuel that was requested
	if fuel:
		newdata = {
			'station_id': return_value['station_id'],
			'price': return_value[fuel],
			'fuel_type': fuel,
			'station_street' : return_value['station_street'],
			'station_address' : return_value['station_address'],
			'timestamp' : return_value['timestamp'],
			'status' : return_value['status'],
			'processing_start': return_value['processing_start'],
			'processing_time': return_value['processing_time']
		}
		return_value = newdata
	logger.debug(f"station: return value '{return_value}'")
	return return_value

if __name__ == '__main__':
	#if called upon directly, use gas_station.py [stationid] or gas_station.py [station_id] [fuel_type]
	if len(sys.argv) > 2:
		gas_station(str(sys.argv[1]),str(sys.argv[2])) 
	else:
		gas_station(str(sys.argv[1]))