'''Talk with purifier'''

# import logging
import configparser
import miio

config = configparser.ConfigParser()
config.read('purifier.ini')

TOKEN = config['purifier']['TOKEN']
IP = config['purifier']['IP']

try:
    air_purifier = miio.AirPurifier(ip=IP, token=TOKEN)

except DeviceException:
    print("Device not ready")

state = air_purifier.status()

print("Temp: {} C, Humidity: {}, AQI: {}, Average AQI: {}, RPM: {}".format(
    state.temperature, state.humidity, state.aqi, state.average_aqi,
    state.motor_speed))
if state.mode == miio.airpurifier.OperationMode.Favorite:
    print("Mode: Favorite, Level: {}".format(state.favorite_level))
else:
    print("Mode: {}".format(state.mode))
