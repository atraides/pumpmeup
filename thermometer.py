import os
import sys
import time
import json
import board
import signal
import logging
import adafruit_dht
import paho.mqtt.client as mqtt

from yaml import safe_load
from logging import config

def signal_terminate(sig, frame):
    global logger
    logger.info('We got a request to terminate! Quitting...')
    sys.exit(0)

def signal_restart(sig, frame):
    global logger
    logger.info('Restart of the thermometer was requested! Restarting...')
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_terminate)
signal.signal(signal.SIGHUP, signal_restart)

log_config = safe_load(open('config.yml'))
config.dictConfig(log_config)

# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(board.D4)

# THINGSBOARD_HOST = '10.42.0.195'
# ACCESS_TOKEN = 'DHT22_DEMO_TOKEN'

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL=10

sensor_data = {'temperature': 0, 'humidity': 0}

next_reading = time.time()

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
        logger.debug("Temp: {:.1f} °C - Humidity: {}% ".format(temperature, humidity))
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity

        # client.publish('v1/devices/millhouse/bedroom/temperature', sensor_data['temperature'], 1)
        # client.publish('v1/devices/millhouse/bedroom/humidity', sensor_data['humidity'], 1)
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        logger.error(error.args[0])
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