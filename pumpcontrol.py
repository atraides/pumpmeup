import re
import argparse

import pmutools
from pmutools import *
from pmu.MQTTClient import MQTTClient
from pmu.pump import PMUPump


def gracefulExit():
    global logger
    if callable(mqtt_client.shutdown):
        mqtt_client.shutdown()

    for pump in pumps:
        pump = pumps.get(pump)
        if callable(pump.turnOff):
            logger.info('Turning off the {pump} pump.'.format(pump=pump.floor))
            pump.turnOff()
    sys.exit(0)

def _parse_mqtt_message(client, userdata, msg):
    if hasattr(msg,'topic') and hasattr(msg,'payload'):
        match = re.match(mqtt_config.get('regex'), msg.topic)
        if match:
            matched = match.groupdict()
            if 'floor' in matched:
                floor = matched.get('floor')
                state = msg.payload.decode('utf-8')
                logger.debug('State change requested to turn {state} the {floor} pump.'.format(floor=floor,state=state))
                if floor in pumps:
                    pump = pumps.get(floor)
                    pump.changeState(state)

def main():
    global pump_config
    global mqtt_config
    global mqtt_client
    global pumps

    pumps = {}

    if all (key in config for key in ('mqtt','pumps')):
        logger.debug('We have all the necessary keys in the config.')
        pumps_config = config.get('pumps')
        mqtt_config = config.get('mqtt')

        for floor in pumps_config:
            pump_config = pumps_config.get(floor)
            pump = PMUPump({**pump_config,'logger':logger,'floor':floor})
            pumps[floor] = pump
            
        if all (key in mqtt_config for key in ('broker','topic','regex')):
            mqtt_client = MQTTClient({**mqtt_config,'logger':logger})
            mqtt_client.safe_connect()
            mqtt_client.on_message = _parse_mqtt_message
            mqtt_client.loop_forever()

parser = argparse.ArgumentParser(description='Watches for changes in the relevant MQTT topics to turn the relevant curcilation pump on or off.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

logger = getLogger(arguments.debug)
config = getConfig('pumpcontrol')

pmutools.gracefulExit = gracefulExit

if __name__ == '__main__':
    main()
