import os
import sys
import time
import json
import board
import logging
import adafruit_dht
import paho.mqtt.client as mqtt

from yaml import safe_load

log_config = safe_load(open('config.yml'))
logging.config.dictConfig(log_config)

logger = logging.getLogger("main")

logger.debug("Debug")
logger.info("Info")
logger.warn("Warn")
logger.error("Error")
logger.critical("Critical")

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

try:
    while True:
        try:
            # Print the values to the serial port
            temperature_c = dhtDevice.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = dhtDevice.humidity
            print(
                "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                    temperature_f, temperature_c, humidity
                )
            )
            sensor_data['temperature'] = temperature_c
            sensor_data['humidity'] = humidity

            # client.publish('v1/devices/millhouse/bedroom/temperature', sensor_data['temperature'], 1)
            # client.publish('v1/devices/millhouse/bedroom/humidity', sensor_data['humidity'], 1)
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error

        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
except KeyboardInterrupt:
    pass

# client.loop_stop()
# client.disconnect()