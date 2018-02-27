#!/usr/bin/python3

'''
Get data from airly api, try to display in useful way
'''

# import json
from math import radians, sin, cos, sqrt, asin
import configparser
import logging
import requests

logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read('airbot.ini')

# Norms, simplified
NORM = {
    'PM2.5': config['norms'].getfloat('PM25_24H'),
    'PM10': config['norms'].getfloat('PM10'),
    'O3': config['norms'].getfloat('O3'),
    'NO2': config['norms'].getfloat('NO2_24H'),
    'CO': config['norms'].getfloat('CO'),
    'C6H6': config['norms'].getfloat('BENZENE'),
    'SO2': config['norms'].getfloat('SO2_24H')
}


LATITUDE = config['location'].getfloat('LATITUDE')
LONGITUDE = config['location'].getfloat('LONGITUDE')
DISTANCE = config['location'].getfloat('distance')

# If we have specific distance, use that, otherwise use global
if config['gios']['DISTANCE_DG']:
    DISTANCE_DG = config['gios'].getfloat('DISTANCE_DG')
else:
    DISTANCE_DG = config['location'].getfloat('DISTANCE_DG')

LAT_SW = LATITUDE - DISTANCE_DG
LON_SW = LONGITUDE - DISTANCE_DG
LAT_NE = LATITUDE + DISTANCE_DG
LON_NE = LONGITUDE + DISTANCE_DG

API_URL = 'https://api.gios.gov.pl/pjp-api/rest'
STATIONS_URL = API_URL + '/station/findAll'
SENSORS_URL = API_URL + '/station/sensors/'
READINGS_URL = API_URL + '/data/getData/'


def haversine(lat1, lon1, lat2, lon2):
    '''
    Calculate distance between two points on sphere
    Taken from https://rosettacode.org/wiki/Haversine_formula#Python
    '''

    R = 6372.8  # Earth radius in kilometers  # pylint: disable=invalid-name

    dLat = radians(lat2 - lat1)  # pylint: disable=invalid-name
    dLon = radians(lon2 - lon1)  # pylint: disable=invalid-name
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2  # noqa: E501 pylint: disable=invalid-name
    c = 2*asin(sqrt(a))  # pylint: disable=invalid-name

    return R * c


def station_within_distance(instance):
    '''Check if station is within set distance from coordinates'''
    if LATITUDE - DISTANCE_DG <= float(instance['gegrLat']) <= LATITUDE + DISTANCE_DG:
        if LONGITUDE - DISTANCE_DG <= float(instance['gegrLon']) <= LONGITUDE + DISTANCE_DG:
            return True
        else:
            return False
    else:
        return False

def get_station_list():
    '''
    Get list of stations
    '''
    gios = requests.get(STATIONS_URL)
    station_list = gios.json()
    nearby_stations = []

    # Get additional info for stations in configured city
    for location in station_list:
        if station_within_distance(location):
            logging.debug("Station within distance: {}".format(location['id']))
            location['distance'] = haversine(float(location['gegrLat']),
                                             float(location['gegrLon']),
                                             LATITUDE, LONGITUDE)
            location['sensors'] = get_sensor_list(str(location['id']))
            nearby_stations.append(location)
        else:
            station_list.remove(location)
    logging.debug(nearby_stations)
    return nearby_stations


def get_sensor_list(instance):
    '''Get list of sensors on a station'''
    gios = requests.get(SENSORS_URL + instance)
    sensor_list = gios.json()
    return sensor_list


def sensors_info(instance):
    '''Print information about sensors on a staton'''
    print("  Sensors:")
    for instance_sensor in instance['sensors']:
        print("\tName: {} Code: {} ID: {}".format(
            instance_sensor['param']['paramName'],
            instance_sensor['param']['paramCode'],
            instance_sensor['id']))


def station_info(instance):
    '''Print information about a station'''
    print("{}: {} ({} km, id {})".format(instance['stationName'],
                                         instance['addressStreet'],
                                         round(instance['distance'], 2),
                                         instance['id']))
    logging.debug(instance['sensors'])
    # sensors_info(instance)


def get_current_readings(sensor_id):
    '''
    Get current reading off of the sensor
    '''
    gios = requests.get(READINGS_URL + sensor_id)
    data = gios.json()
    return data


def sensor_reading_latest(data):
    '''Get latest reading off of a sensor'''
    logging.debug(data['values'])
    for result in data['values']:
        if result['value']:
            logging.debug("Latest valid reading: value %s, date %s" % (result['value'], result['date']))
            logging.debug("Latest sensor value:")
            logging.debug(result)
            message = str(result['value']) + " (measured at " + result['date'] + ")"
            return message


def sensor_reading_24avg(data):
    '''Get 24h average of sensor data'''
    if len(data['values']) < 24:
        print("Not enough data to calculate 24h average!")
        return False
    else:
        datapoints_count = 0
        datapoints_sum = 0.0
        for i in range(0, 24):
            if data['values'][i]['value']:
                datapoints_count += 1
                datapoints_sum += data['values'][i]['value']
        return round(datapoints_sum / datapoints_count, 2)


def get_norm(norm, value):
    '''Get percentage of 24h norm for pillutant'''
    logging.debug("Calculating norm for {} with value {}".format(norm, value))
    return round(value * 100 / NORM[norm], 0)


for station in sorted(get_station_list(),
                      key=lambda station: station['distance']):
    station_info(station)
    for sensor in sorted(station['sensors'],
                         key=lambda sensor: sensor['param']['paramCode']):
        reading = get_current_readings(str(sensor['id']))
        if reading['key'] == sensor['param']['paramCode']:
            print("\t{}: {}, 24h average: {} ({}% norm)".format(
                reading['key'],
                sensor_reading_latest(reading),
                sensor_reading_24avg(reading),
                get_norm(reading['key'], sensor_reading_24avg(reading)))
                 )
        else:
            print("Station code {} NOT EQUAL reading key {}".format(
                sensor['param']['paramCode'], reading['key']))
