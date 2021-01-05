import sys
import time
import board
import logging
import digitalio

from logging import getLogger

from pprint import pprint

class PMUPump:
    def __init__(self,config):
        if 'floor' in config:
            self.floor = config.get('floor')
        if 'pin' in config:
            pin = config.get('pin')
            if pin in dir(board):
                 self.pin = getattr(board,pin)
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

        self.initIO()

    def initIO(self):
        if self.floor and self.pin:
            self.logger.debug(
                'Initialize pump for {floor} on pin {pin}'.format(
                    floor=self.floor,
                    pin=self.pin))
            self.io = digitalio.DigitalInOut(self.pin)
            self.io.direction = digitalio.Direction.OUTPUT
            self.turnOn()
            self.turnOff()

    def turnOn(self):
        self.io.value = False
        self.io_state = False
        time.sleep(0.5)
        return self

    def turnOff(self):
        self.io.value = True
        self.io_state = True
        time.sleep(0.5)
        return self

    def getState(self):
        if self.io.value:
            return 'Off'
        return 'On'

    def changeState(self,new_state):
        self.logger.debug('We got a requst to turn the pump {} which is currently {}.'.format(new_state,self.getState()))
        if isinstance(new_state, str) :
            new_state = self.str2state(new_state)
        if new_state != self.io.value:
            self.logger.debug('State changed to {}'.format(new_state))
            self.io.value = new_state

    def str2state(self,string):
        return string.lower() not in ('yes', 'true', 't', '1', 'on')