#!/usr/bin/python3

'''
Get data from airly api, try to display in useful way
'''

from math import radians, sin, cos, sqrt, asin
import configparser
import logging
import requests

logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read('airbot.ini')
NORM_PM25 = config['norms'].getfloat('NORM_PM25')
NORM_PM10 = config['norms'].getfloat('NORM_PM10')
LATITUDE = config['location'].getfloat('LATITUDE')
LONGITUDE = config['location'].getfloat('LONGITUDE')
DISTANCE = config['location'].getfloat('distance')
DISTANCE_DG = config['location'].getfloat('DISTANCE_DG')
LAT_SW = LATITUDE - DISTANCE_DG
LON_SW = LONGITUDE - DISTANCE_DG
LAT_NE = LATITUDE + DISTANCE_DG
LON_NE = LONGITUDE + DISTANCE_DG

# Airly
APIKEY = config['airly']['APIKEY']
API_URL = 'https://airapi.airly.eu'
NEAREST_URL = API_URL + '/v1/nearestSensor/measurements'
SENSOR_URL = API_URL + '/v1/sensor/measurements'
SENSOR_LIST_URL = API_URL + '/v1/sensorsWithWios/current'
LOCATION_URL = API_URL + '/v1/mapPoint/measurements'
HEADERS = {'apikey': APIKEY}


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


def get_sensor_list(lat_sw, lon_sw, lat_ne, lon_ne):
    '''
    Get list of sensors for defined area
    '''
    payload = {'southwestLat': lat_sw, 'southwestLong': lon_sw,
               'northeastLat': lat_ne, 'northeastLong': lon_ne}
    airly = requests.get(SENSOR_LIST_URL, headers=HEADERS, params=payload)
    sensor_list = airly.json()
    return sensor_list


def get_current_readings(sensor_id):
    '''
    Get current reading off of the sensor
    '''
    payload = {'sensorId': sensor_id}
    airly = requests.get(SENSOR_URL, headers=HEADERS, params=payload)
    data = airly.json()
    return data['currentMeasurements']


def get_location_data(lat, lon):
    '''
    Get data for a specific point on map
    '''
    payload = {'latitude': lat, 'longitude': lon}
    airly = requests.get(LOCATION_URL, headers=HEADERS, params=payload)
    data = airly.json()
    return data['currentMeasurements']


def print_reading(data):
    '''
    Pretty print reading data
    '''
    print(" Pollution level: " + str(data['pollutionLevel']) +
          " Temperature: " + str(round(data['temperature'], 1)) +
          " Humidity: " + str(round(data['humidity'])) +
          " Pressure: " + str(round(data['pressure']/100)) +
          " AQI: " + str(round(data['airQualityIndex'])) +
          " PM2.5: " + str(round(data['pm25'], 2)) +
          " PM10: " + str(round(data['pm10'], 2)) +
          "\n")


def sensor_info(instance):
    '''Print information about sensor'''
    print(str(instance['address']['route']) + " (" +
          str(round(instance['distance'], 1)) + " km, id " +
          str(instance['id']) + ")")


logging.debug("Fetching list of sensors")
sensors = get_sensor_list(LAT_SW, LON_SW, LAT_NE, LON_NE)  # noqa: E501 pylint: disable=invalid-name
for sensor in sensors:
    sensor['distance'] = haversine(sensor['location']['latitude'],
                                   sensor['location']['longitude'],
                                   LATITUDE, LONGITUDE)

logging.debug("Fetching data")
for sensor in sorted(sensors, key=lambda sensor: sensor['distance']):
    current_reading = get_current_readings(sensor['id'])
    if current_reading:
        logging.debug(current_reading)
        sensor_info(sensor)
        try:
            print_reading(current_reading)
        except KeyError:
            print("\tCouldn't get data for sensor\n")
        # print(sensor)

logging.debug("Getting location data")
location_data = get_location_data(LATITUDE, LONGITUDE)  # noqa: E501 pylint: disable=invalid-name
logging.debug(location_data)
print("Current extrapolated data for location:")
print("Temperature: " + str(round(location_data['temperature'], 1)) +
      " Humidity: " + str(round(location_data['humidity'])) +
      " Pressure: " + str(round(location_data['pressure']/100)) +
      " PM2.5: " + str(round(location_data['pm25'], 2)) +
      " PM10: " + str(round(location_data['pm10'], 2)))
