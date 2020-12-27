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
    if thermostat:
        thermostat.exit()
    sys.exit(0)

def main():
    global mqtt_client
    global thermostat
    # Initialize the thermostat
    if 'thermostat' in config:
        next_reading = time.time()
        thermostat_config = config.get('thermostat')
        thermostat = adafruit_dht.DHT22(board.D4)
        if 'interval' in thermostat_config:
            measure_interval = thermostat_config.get('interval')
        else:
            measure_interval = 60

        if 'location' in thermostat_config:
            thermostat_location = thermostat_config.get('location')
        else:
            thermostat_location = { 'floor': 'default', 'room': 'default'}

        mqtt_connected = False
        mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

        while not mqtt_connected:
            try:
                mqtt_client.connect(MQTT_ADDRESS, 1883, 60)
                mqtt_connected = True
            except OSError as error:
                if error.errno == 113: # No route to host
                    logger.error('Can\'t connect to the MQTT broker (No route to host), retrying in 120 seconds.')
                    time.sleep(120)

        mqtt_client.loop_start()

        while True:
            try:
                temperature = thermostat.temperature
                humidity = thermostat.humidity
                debug_message("Temp: {:.1f} °C - Humidity: {}% ".format(temperature, humidity))

                mqtt_client.publish('v1/millhouse/{}/{}/temperature'.format(thermostat_location.get('floor'),thermostat_location.get('room')), temperature, 1)
                mqtt_client.publish('v1/millhouse/{}/{}/humidity'.format(thermostat_location.get('floor'),thermostat_location.get('room')), humidity, 1)
            except RuntimeError as error:
                # Errors happen fairly often, DHT's are hard to read, just keep going
                logger.error('The following DHT error occured: {}'.format(error.args[0]))
                time.sleep(2.0)
                continue
            except Exception as error:
                thermostat.exit()
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