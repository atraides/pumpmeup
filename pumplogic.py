#!/home/dietpi/production/bin/python3

import os
import re
import sys
import time

import pmutools
from pmutools import *
from pmu.MQTTClient import MQTTClient

def gracefulExit():
    if callable(mqtt_client.shutdown):
        mqtt_client.shutdown()
    sys.exit(0)

def _parse_mqtt_message(client, userdata, msg):
    if hasattr(msg,'topic') and hasattr(msg,'payload'):
        match = re.match(mqtt_config.get('regex'), msg.topic)
        if match:
            matched = match.groupdict()
            if all (key in matched for key in ('place','floor','room','measurement')):
                location = matched.get('room')
                measurement = matched.get('measurement')
                if measurement in ('status'):
                    return None
                else:
                    payload = float(msg.payload.decode('utf-8'))
                    logger.debug(
                        '{measurement} reading received from {location}: {value}'.format(
                            location=location.capitalize(),
                            measurement=measurement.capitalize(),
                            value=payload))
                    topic_prefix = 'v1/{}/{}'.format(matched.get('place'),matched.get('floor'))
                    if payload >= 22:
                        mqtt_client.publish('{prefix}/pumpcontrol/state'.format(prefix=topic_prefix), payload='off', qos=1, retain=True)
                        logger.debug('Publishing to {topic} with payload {payload}'.format(topic='{prefix}/pumpcontrol/state'.format(prefix=topic_prefix),payload='off'))
                    elif payload <= 20:
                        mqtt_client.publish('{prefix}/pumpcontrol/state'.format(prefix=topic_prefix), payload='on', qos=1, retain=True)
                        logger.debug('Publishing to {topic} with payload {payload}'.format(topic='{prefix}/pumpcontrol/state'.format(prefix=topic_prefix),payload='off'))

def main():
    global mqtt_config
    global mqtt_client
    pmutools.gracefulExit = gracefulExit
    if 'mqtt' in config:
        logger.debug('We have all the necessary keys in the config.')
        mqtt_config = config.get('mqtt')

        if all (key in mqtt_config for key in ('broker','topic','regex')):
            mqtt_client = MQTTClient({**mqtt_config,'logger':logger})
            mqtt_client.safe_connect()
            mqtt_client.on_message = _parse_mqtt_message
            mqtt_client.loop_forever()

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

logger = getLogger(arguments.debug)
config = getConfig('pumplogic')

if __name__ == '__main__':
    main()