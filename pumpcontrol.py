import re
import time
import board
import digitalio
import paho.mqtt.client as mqtt

MQTT_ADDRESS = '10.42.0.195'
MQTT_USER = 'cdavid'
MQTT_PASSWORD = 'cdavid'
MQTT_TOPIC = 'v1/devices/millhouse/+/pumpcontroll/state'
MQTT_REGEX = 'v1/devices/millhouse/([^/]+)/pumpcontroll/state'
MQTT_CLIENT_ID = 'CirculationPumpControl'

basement = digitalio.DigitalInOut(board.D23)
groundfloor = digitalio.DigitalInOut(board.D24)


def initIO(io):
    io.direction = digitalio.Direction.OUTPUT
    io.value = False
    time.sleep(0.5)
    io.value = True

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEX, topic)
    if match:
        location = match.group(1)
        pump_state = str2bool(payload)
        print('loc: {}, payload: {}'.format(location, pump_state))
        if location in ('bedroom'):
            basement.value = pump_state
        elif location in ('livingroom'):
            groundfloor.value = pump_state
    else:
        return None

def on_message(client, userdata, msg):
    print(msg.topic,' - ',str(msg.payload.decode("utf-8")),' - ',msg.retain)
    _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

def main():
    initIO(basement)
    initIO(groundfloor)

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    #mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_ADDRESS, 1883)
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == '__main__':
    main()
