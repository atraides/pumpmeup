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
    if callable(mqtt_client.shutdown):
        mqtt_client.shutdown()
    sys.exit(0)

def main():
    global mqtt_client
    global thermostat

    logger = getLogger(arguments.debug)
    pmutools.gracefulExit = gracefulExit
    
    if isConfigured('thermostat'):
        logger.info('Thermostat configuration found. Intializing thermostat.')    
        thermostat_config = getConfig('thermostat')
        thermostat = PMUThermostat({**thermostat_config,'logger':logger})
        if 'mqtt' in thermostat_config:
            mqtt_config = thermostat_config.get('mqtt')
            if all (key in mqtt_config for key in ('broker','client_prefix')):
                client_name = '{prefix}-{floor}-{room}'.format(
                    prefix=mqtt_config.get('client_prefix'),
                    floor=thermostat.getFloor(),
                    room=thermostat.getRoom())
                mqtt_config = {
                    **mqtt_config,
                    'logger':logger,
                    'client_name': client_name}

                mqtt_client = MQTTClient(mqtt_config)
                mqtt_client.safe_connect()
                mqtt_client.loop_start()
                while True:
                    temperature = thermostat.getTemperature()
                    humidity = thermostat.getHumidity()
                    topic_prefix = 'v1/{}/{}/{}'.format(
                        thermostat.getPlace(),
                        thermostat.getFloor(),
                        thermostat.getRoom())
                    if temperature and humidity:
                        mqtt_client.publish('{prefix}/temperature'.format(prefix=topic_prefix), temperature, 1)
                        mqtt_client.publish('{prefix}/humidity'.format(prefix=topic_prefix), humidity, 1)
                    thermostat.waitForNextRead()
                gracefulExit()
    else:
        logger.critical('Thermostat is not configured. Exiting.')
        sys.exit(0)

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

if __name__ == '__main__':
    main()