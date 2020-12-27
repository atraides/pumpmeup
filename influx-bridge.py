import re
from typing import NamedTuple

import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

PUMP_STATE = False

INFLUXDB_ADDRESS = '10.42.0.195'
INFLUXDB_USER = 'mqtt'
INFLUXDB_PASSWORD = 'mqtt'
INFLUXDB_DATABASE = 'thermo'

MQTT_ADDRESS = '10.42.0.195'
MQTT_USER = 'cdavid'
MQTT_PASSWORD = 'cdavid'
MQTT_TOPIC = [('v1/devices/millhouse/+/temperature',1),('v1/devices/millhouse/+/humidity',1)]
MQTT_REGEX = '^v1/devices/millhouse/([^/]+)/([^/]+)$'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8086, INFLUXDB_USER, INFLUXDB_PASSWORD, None)
mqtt_client = mqtt.Client(MQTT_CLIENT_ID)

class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float

def on_connect(client, userdata, flags, rc):
    """ The callback for when the client receives a CONNACK response from the server."""
    print('Connected with result code ' + str(rc))
    client.subscribe(MQTT_TOPIC)

def _parse_mqtt_message(msg):
    global PUMP_STATE
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    retain = msg.retain
    match = re.match(MQTT_REGEX, topic)
    if match:
        location = match.group(1)
        measurement = match.group(2)
        if measurement in ('status','pumpcontroll'):
            if retain and measurement == 'pumpcontroll':
                PUMP_STATE = payload
            return None
        return SensorData(location, measurement, float(payload))
    else:
        return None

def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data.measurement,
            'tags': {
                'location': sensor_data.location
            },
            'fields': {
                'value': sensor_data.value
            }
        }
    ]
    influxdb_client.write_points(json_body)

def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received from the server."""
    print(msg.topic + ' ' + str(msg.payload))
    sensor_data = _parse_mqtt_message(msg)
    if sensor_data is not None:
        _send_sensor_data_to_influxdb(sensor_data)
        if sensor_data.measurement == 'temperature':
            if sensor_data.value >= 20:
                set_pump(sensor_data.location,False)
            else:
                set_pump(sensor_data.location,True)

def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if len(list(filter(lambda x: x['name'] == INFLUXDB_DATABASE, databases))) == 0:
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)

def set_pump(location,state):
    mqtt_client.publish('v1/devices/millhouse/{}/pumpcontroll/state'.format(location), payload=state, qos=1, retain=True)

def main():
    _init_influxdb_database()

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
    print('MQTT to InfluxDB bridge')
    main()
