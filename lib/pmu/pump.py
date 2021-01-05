import time
import board
import logging
import digitalio

from pprint import pprint

class PMUPump:
    def __init__(self,config):

        if 'location' in config:
            self.location = config.get('location')
        if 'pin' in config:
            pin = config.get('pin')
            if pin in dir(board):
                 self.pin = getattr(board,pin)
        if all (k in dir(self) for k in ('pin', '_dht_device')):
            self.thermostat = self._dht_device(self.pin)
        if 'logger' in config:
            self.logger=config.get('logger')
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger=getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(handler)
