#!/home/dietpi/production/bin/python3

import os
import sys
import time
import signal
import argparse
import pmutools

from pmutools import *
from pmu.thermostat import PMUThermostat
from pmu.MQTTClient import MQTTClient

def gracefulExit():
    mqtt_client.shutdown()
    sys.exit(0)

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

logger = getLogger(arguments.debug)

if thermostatConfigured:
    logger.info('Thermostat configuration found. Intializing thermostat.')
    thermostat = PMUThermostat({**getConfig('thermostat'),**{'logger':logger}})
else:
    logger.critical('Thermostat is not configured. Exiting.')
    sys.exit(0)

if mqttConfigured:
    mqtt_client_name = mqttClientName(getConfig('mqtt'),thermostat)
    mqtt_client = MQTTClient(mqtt_client_name)
    mqtt_client.initialize(getConfig('mqtt').get('broker'),logger)
    pmutools.gracefulExit = gracefulExit
    while True:
        temperature = thermostat.getTemperature()
        humidity = thermostat.getHumidity()
        topic_prefix = 'v1/{}/{}/{}'.format(thermostat.getPlace(),thermostat.getFloor(),thermostat.getRoom())
        if temperature and humidity:
            mqtt_client.publish('{prefix}/temperature'.format(prefix=topic_prefix), temperature, 1)
            mqtt_client.publish('{prefix}/humidity'.format(prefix=topic_prefix), humidity, 1)
        thermostat.waitForNextRead()
    gracefulExit()