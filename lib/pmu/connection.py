import sys
import time

from .MQTTClient import MQTTClient

class PMUConnection():
    def __init__(self,config={}):
        for key in config:
            self.set_arguments(name=key,config=config)

    def set_arguments(self,name=None,config=None):
        if name in config:
            setattr(self, name ,config.get(name))

    def connect(self,topic=None):
        '''
        For now we hardcode the MQTT connection, later down the line
        this module should be responsible to load the appropriate connection
        library before initiating the connection. 
        '''
        if hasattr(self,'mqtt'):
            if 'broker' in self.mqtt:
                mqtt_config = {
                    **self.mqtt,
                    'logger':self.log
                }
                if topic:
                    mqtt_config = {**mqtt_config,'topic': topic}
                self._client = MQTTClient(mqtt_config)
                self._client.safe_connect()
                self._client.loop_start()
    
    def publish(self,topic=None,payload=None,qos=1,retain=False):
        if topic and payload:
            self.log.debug(f"Publishing {payload} to {topic}.")
            self._client.publish(topic, payload=payload, qos=qos, retain=retain)

    def on_message(self,callback):
        if callable(callback):
            self._client.on_message = callback

    def disconnect(self):
        self._client.shutdown()
