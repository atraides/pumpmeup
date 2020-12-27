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

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT22 sensor and publish it to a MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
args = parser.parse_args()

script_path = os.path.dirname(os.path.realpath(__file__))

config = safe_load(open('{}/config.yml'.format(script_path)))
if config.logger:
    log_config.dictConfig(config.logger)
    logger = logging.getLogger('main')

root_logger = logging.getLogger()

def debug_message(message):
    if args.debug:
        root_logger.debug(message)

def signal_catcher(signalNumber, frame):
    if signalNumber == signal.SIGTERM: # SIGTERM
        logger.info('We got a request to terminate! Quitting...')
        sys.exit(0)
    if signalNumber == 1: # SIGHUP
        logger.info('Restart of the thermometer was requested! Restarting...')
    if signalNumber == 2: # SIGINT
        logger.info('We got a request to terminate! Quitting...')
        sys.exit(0)

signal.signal(signal.SIGTERM, signal_catcher)
signal.signal(signal.SIGHUP, signal_catcher)
signal.signal(signal.SIGINT, signal_catcher)


# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(board.D4)
INTERVAL=10
sensor_data = {'temperature': 0, 'humidity': 0}
next_reading = time.time()

# THINGSBOARD_HOST = '10.42.0.195'
# ACCESS_TOKEN = 'DHT22_DEMO_TOKEN'
# client = mqtt.Client()

# Set access token
#client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
# client.connect(THINGSBOARD_HOST, 1883, 60)

# client.loop_start()

while True:
    try:
        # Print the values to the serial port
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        debug_message("Temp: {:.1f} °C - Humidity: {}% ".format(temperature, humidity))
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity

        # client.publish('v1/devices/millhouse/bedroom/temperature', sensor_data['temperature'], 1)
        # client.publish('v1/devices/millhouse/bedroom/humidity', sensor_data['humidity'], 1)
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        logger.error('The following DHT error occured: {}'.format(error.args[0]))
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    next_reading += INTERVAL
    sleep_time = next_reading-time.time()
    if sleep_time > 0:
        time.sleep(sleep_time)

# client.loop_stop()
# client.disconnect()
