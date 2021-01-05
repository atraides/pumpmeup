#!/home/dietpi/production/bin/python3

import re
import sys
import time
import requests

from typing import NamedTuple
from influxdb import InfluxDBClient

import pmutools
from pmutools import *
from pmu.MQTTClient import MQTTClient

class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float

def _init_influxdb_database():
    databases = None
    logger.debug('Initialization of the InfluxDB interface.')
    while not databases:
        try:
            databases = influxdb_client.get_list_database()
        except requests.exceptions.ConnectionError as errc:
            logger.error('Error Connecting: {error}'.format(error=errc))
            logger.warning('Connection to InfluxDB failed. Reconnect in {retry} seconds.'.format(retry=60))
            time.sleep(60)
    database = influx_config.get('database')
    if len(list(filter(lambda x: x['name'] == database, databases))) == 0:
        influxdb_client.create_database(database)
    influxdb_client.switch_database(database)

def gracefulExit():
    if callable(mqtt_client.shutdown):
        mqtt_client.shutdown()
    sys.exit(0)

def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data.measurement,
            'tags': {
                'location': sensor_data.location
            },
            'fields': {
                'value': sensor_data.value
            }
        }
    ]
    influxdb_client.write_points(json_body)

def _parse_mqtt_message(client, userdata, msg):
    if hasattr(msg,'topic') and hasattr(msg,'payload'):
        match = re.match(mqtt_config.get('regex'), msg.topic)
        if match:
            matched = match.groupdict()
            if all (key in matched for key in ('floor','room','measurement')):
                location = matched.get('room')
                measurement = matched.get('measurement')
                if measurement in ('status'):
                    return None
                else:
                    _send_sensor_data_to_influxdb(
                        SensorData(
                            location,
                            measurement,
                            float(msg.payload.decode('utf-8'))))
                    logger.debug(
                        '{measurement} reading received from {location}: {value}'.format(
                            location=location.capitalize(),
                            measurement=measurement.capitalize(),
                            value=float(msg.payload.decode('utf-8'))))

def main():
    global influx_config
    global influxdb_client
    global mqtt_config
    global mqtt_client
    pmutools.gracefulExit = gracefulExit
    if all (key in config for key in ('mqtt','influxdb')):
        logger.debug('We have all the necessary keys in the config.')
        influx_config = config.get('influxdb')
        mqtt_config = config.get('mqtt')
        if all (key in influx_config for key in ('address','user','password','database')):
            logger.debug('We have all necessary influxdb config keys.')
            influxdb_client = InfluxDBClient(influx_config.get('address'),8086,influx_config.get('user'),influx_config.get('password'),None)
            _init_influxdb_database()
        else:
            logger.error('Some crucial influxdb configuration is missing. Pleae check the configuration file.')
            gracefulExit()
            
        if all (key in mqtt_config for key in ('broker','topic','regex')):
            mqtt_client = MQTTClient({**mqtt_config,'logger':logger})
            mqtt_client.safe_connect()
            mqtt_client.on_message = _parse_mqtt_message
            mqtt_client.loop_forever()

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

logger = getLogger(arguments.debug)
config = getConfig('influx-bridge')

if __name__ == '__main__':
    main()