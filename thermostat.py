#!/home/dietpi/production/bin/python3

import os
import sys
import time
import json
import board
import signal
import logging
import argparse
import adafruit_dht
import paho.mqtt.client as mqtt

from yaml import safe_load
from logging import config as log_config

def debug_message(message):
    if args.debug:
        root_logger.debug(message)

def signal_catcher(signalNumber, frame):
    if signalNumber == signal.SIGTERM: # SIGTERM
        logger.info('We got a request to terminate! Quitting...')
        gracefull_exit()
    if signalNumber == 1: # SIGHUP
        logger.info('Restart of the thermometer was requested! Restarting...')
    if signalNumber == 2: # SIGINT
        logger.info('We got a request to terminate! Quitting...')
        gracefull_exit()

def gracefull_exit():
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    sys.exit(0)

def main():
    global mqtt_client
    # Initialize the thermostat
    if 'thermostat' in config:
        thermostat = config.get('thermostat')
        thermostat_device = adafruit_dht.DHT22(board.D4)
        measure_interval = thermostat.get('interval')
        next_reading = time.time()

        mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

        try:
            mqtt_client.connect(MQTT_ADDRESS, 1883, 60)
        except OSError as error:
            print(error)

        mqtt_client.loop_start()

        while True:
            try:
                temperature = thermostat_device.temperature
                humidity = thermostat_device.humidity
                debug_message("Temp: {:.1f} °C - Humidity: {}% ".format(temperature, humidity))

                mqtt_client.publish('v1/millhouse/basement/study/temperature', temperature, 1)
                mqtt_client.publish('v1/millhouse/basement/study/humidity', humidity, 1)
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                logger.error('The following DHT error occured: {}'.format(error.args[0]))
                time.sleep(2.0)
                continue
            except Exception as error:
                thermostat_device.exit()
                raise error

            next_reading += measure_interval
            sleep_time = next_reading-time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT22 sensor and publish it to a MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
args = parser.parse_args()

script_path = os.path.dirname(os.path.realpath(__file__))
config = safe_load(open('{}/config.yml'.format(script_path)))

if 'logger' in config:
    log_config.dictConfig(config.get('logger'))
    logger = logging.getLogger('main')

root_logger = logging.getLogger()

signal.signal(signal.SIGTERM, signal_catcher)
signal.signal(signal.SIGHUP, signal_catcher)
signal.signal(signal.SIGINT, signal_catcher)

MQTT_ADDRESS = '10.42.0.195'
MQTT_CLIENT_ID = 'PMUThermostat'

if __name__ == '__main__':
    main()