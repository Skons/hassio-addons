"""
Dutch Gas stations API Module
"""
import sys
import json
import time
from io import BytesIO
import re
from PIL import Image
import requests
import pytesseract
from fake_headers import Headers
from geopy import distance
from gas_prices import gas_prices
from dgp_common import _read_cached_jsonfile

# Settings
# Something like lru_cache would be nice but has no time expiring support, so custom json storage
CACHE_TIME_STATIONS = 86400 #24h, could be longer, stations don't come and go very often

def gas_stations(fuel,longitude,latitude,radius):
    """
    Main Dutch Gas stations API Function
    """

    url = f'https://tankservice.app-it-up.com/Tankservice/v1/places?fmt=web&fuel={fuel}'

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

    def _write_stationdata():
        """
        Query the api and cache the results to a json file
        """
        headers = Headers(headers=True).generate()

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()

            with open('cache/' + f'{fuel}.json', 'w') as outfile:
                    json.dump(data, outfile)
        else:
            print(f'Error: statuscode: {response.status_code}')
            print(f'Error: Used header: {headers}')
            ip_addr = requests.get('https://api.ipify.org').text
            print(f'Error: Used IP: {ip_addr}')
            print(f'Error: Response text: {response.text}')
            data = {}
        return data

    # Main logic
    stationdata = _read_cached_jsonfile('cache/' + f'{fuel}.json', CACHE_TIME_STATIONS)
    if stationdata == False:
        print(f'Fuel {fuel} new request')
        stationdata = _write_stationdata()

    stations = []
    for station in stationdata:
        """
        Loop through all stations and find if they are within radius
        """
        newstation = {}
        newstation['brand'] = station['brand']
        newstation['name'] = station['name']
        station_lat = str(station['lat'])
        newstation['latitude'] = float(station_lat[:2] + "." + station_lat[2:])#quick and dirty conversion of lat lon to float, should not be done this way
        station_lon = str(station['lng'])
        newstation['longitude'] = float(station_lon[:1] + "." + station_lon[1:])
        newstation['fuel'] = fuel
        return_value = is_location_in_radius(latitude, longitude, newstation['latitude'] , newstation['longitude'], radius)
        if return_value == True:
            gasprices = gas_prices(station['id'], fuel) #get the corresponding gas station and its prices
            if 'prijs' in gasprices:
                newstation = {**newstation, **gasprices}
                stations.append(newstation)

    return_value = {}
    return_value['gas_stations'] = sorted(stations, key=lambda x: x['prijs'], reverse=False) #sort on prijs, cheapest first
    print(return_value)
    return return_value

if __name__ == '__main__':
    gas_stations(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]), str(sys.argv[4])) #if called upon directly, use gas_stations.py [fueltype] [longitude] [latitude] [radius]
