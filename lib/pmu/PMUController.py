import time
import board
import adafruit_dht

from pprint import pprint

class PMUController:
    def __init__(self,config={}):
        for key in config:
            self.set_arguments(name=key,config=config)

        self.topic = [self.location,self.capability,self.floor]

        if hasattr(self, 'consume'):
            ''' We have an network resource we need to listen on '''
            self.topics = []
            if isinstance(self.consume,list):
                for resource in self.consume:
                    self.topics.append(['/'.join([*self.topic,resource]),1])
                    self.log.debug(f"Controller is set to consume {'/'.join([*self.topic,resource])}")

        if hasattr(self, 'connection'):
            self.connection.connect(self.topics)
            self.connection.on_message(self._parse_mqtt_message)

    def set_arguments(self,name=None,config=None):
        if name in config:
            setattr(self, name ,config.get(name))

    def _parse_mqtt_message(self, client, userdata, msg):
        if hasattr(msg,'topic') and hasattr(msg,'payload'):
            state = msg.payload.decode('utf-8')
            logger.debug(f'State change requested to turn {state} the {floor} pump.')
                
    def start_controller(self,exit):
        while not exit.is_set():
            exit.wait(self.interval)
        self.stop_controller()

    def stop_controller(self):
        controller = '/'.join([self.location,self.capability,self.floor])
        self.log.debug(f'Stopping {controller}.')
        if hasattr(self,'connection'):
            self.connection.disconnect()
        self.log.debug(f'Controller {controller} is stopped.')