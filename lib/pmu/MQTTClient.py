import sys
import time
import logging
import paho.mqtt.client as mqtt

from collections import namedtuple

class MQTTClient(mqtt.Client):
    def __init__(self,config={},**kwargs):
        # Get the client name from the provided config, then pass all non-config parameters to the parent
        if (('client_name' in config) and ('client_id' not in kwargs)):
            kwargs = {**kwargs, 'client_id': config.get('client_name')}
        super(MQTTClient, self).__init__(**kwargs)

        self.config = namedtuple('MQTTConfig', config.keys())(**config)
        self.last_pub_time=time.time()
        self.topic_ack=[]
        self.run_flag=True
        self.subscribe_flag=False
        self.bad_connection_flag=False
        self.connected_flag=False
        self.disconnect_flag=False
        self.disconnect_time=0.0
        self.pub_msg_count=0
        self.devices=[]
        if 'logger' in config:
            self.logger=config.get('logger')
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger=logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(handler)

    def on_connect(self, client, userdata, flags, rc):
        while not self.connected_flag:
            if rc==0:
                self.connected_flag=True #set flag
                self.logger.info("MQTT connection succesful.")
                if hasattr(self.config,'topic'):
                    self.logger.info('Subscribing to topic: {topic}'.format(topic=self.config.topic))
                    self.subscribe(self.config.topic)
            else:
                self.logger.warning("MQTT connection failed with return code=",rc)
            time.sleep(1)

    def on_message(self, client, userdata, msg):
        self.logger.info('New message in \'{topic}\' with payload {payload}'.format(topic=msg.topic,payload=str(msg.payload)))

    def shutdown(self):
        self.loop_stop
        self.disconnect()

    def get_connection_options(self):
        options = []
        if hasattr(self.config,'broker'): options.append(self.config.broker)
        if hasattr(self.config,'port'): options.append(self.config.port)
        if hasattr(self.config,'keepalive'): options.append(self.config.keepalive)
        self.logger.info('We have the following connection options: [{}].'.format(', '.join(map(str,options))))
        return options

    def safe_connect(self,retry=60):
        if hasattr(self.config,'broker'):
            while True:
                try:
                    self.logger.info('Connecting to {broker}.'.format(broker=self.config.broker))
                    self.connect(*self.get_connection_options())
                    break
                except OSError as error:
                    if error.errno == 113: # No route to host
                        self.logger.warning('Can\'t connect to the MQTT broker (No route to host).')
                self.logger.warning('MQTT connection failed. Retrying in {retry} seconds.'.format(retry=retry))
                time.sleep(retry)
            