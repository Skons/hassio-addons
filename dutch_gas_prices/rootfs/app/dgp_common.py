"""
Dutch Gas prices Common Functions
"""
import os
import time
import json

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
