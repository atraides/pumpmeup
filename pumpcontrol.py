import re
import time

import pmutools
from pmutools import *
from pmu.MQTTClient import MQTTClient
from pmu.pump import PMUPump

from pprint import pprint

def gracefulExit():
    if callable(mqtt_client.shutdown):
        mqtt_client.shutdown()
    sys.exit(0)

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
                    logger.debug(
                        '{measurement} reading received from {location}: {value}'.format(
                            location=location.capitalize(),
                            measurement=measurement.capitalize(),
                            value=float(msg.payload.decode('utf-8'))))

def main():
    global pump_config
    global mqtt_config
    global mqtt_client

    pmutools.gracefulExit = gracefulExit

    if all (key in config for key in ('mqtt','pumps')):
        logger.debug('We have all the necessary keys in the config.')
        pump_config = config.get('pumps')
        mqtt_config = config.get('mqtt')

        for pump in pump_config:
            logger.debug(pump)
            
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

# import board
# import digitalio
# import paho.mqtt.client as mqtt

# MQTT_TOPIC = 'v1/devices/millhouse/+/pumpcontroll/state'
# MQTT_REGEX = 'v1/devices/millhouse/([^/]+)/pumpcontroll/state'

# basement = digitalio.DigitalInOut(board.D23)
# groundfloor = digitalio.DigitalInOut(board.D24)

# def initIO(io):
#     io.direction = digitalio.Direction.OUTPUT
#     io.value = False
#     time.sleep(0.5)
#     io.value = True

# def str2bool(v):
#   return v.lower() in ("yes", "true", "t", "1")

# def main():
#     initIO(basement)
#     initIO(groundfloor)

#     mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
#     #mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
#     mqtt_client.on_connect = on_connect
#     mqtt_client.on_message = on_message

#     mqtt_client.connect(MQTT_ADDRESS, 1883)
#     try:
#         mqtt_client.loop_forever()
#     except KeyboardInterrupt:
#         mqtt_client.loop_stop()
#         mqtt_client.disconnect()

if __name__ == '__main__':
    main()
