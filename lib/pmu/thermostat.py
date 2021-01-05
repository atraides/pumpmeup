import time
import board
import logging
import adafruit_dht

class PMUThermostat:
    def __init__(self,config):
        if 'model' in config:
            model = config.get('model')
            if model in dir(adafruit_dht):
                self._dht_device = getattr(adafruit_dht,model)
        if 'interval' in config:
            self.interval = config.get('interval')
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
            self.logger=logging.getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(handler)

    def getTemperature(self):
        return self.__getReading('temperature')
    
    def getHumidity(self):
        return self.__getReading('humidity')

    def getFloor(self):
        return self.__getLocation('floor')
    
    def getRoom(self):
        return self.__getLocation('room')

    def getPlace(self):
        return self.__getLocation('place')

    def waitForNextRead(self):
        if 'interval' in dir(self):
            if self.interval > 0:
                time.sleep(self.interval)
                return self
        time.sleep(10)
        return self
    
    def __getLocation(self,type):
        if 'location' in dir(self):
            if type in self.location:
                return self.location.get(type)
        return 'default'

    def __getReading(self,type):
        reading = None
        if type in ('humidity','temperature') and 'thermostat' in dir(self):
            while not reading:
                try:                    
                    reading = getattr(self.thermostat,type)
                except RuntimeError as error:
                    # Errors happen fairly often, DHT's are hard to read, just keep going
                    self.logger.warning('An error occured reading the DHT sensor: {}'.format(error.args[0]))
                    time.sleep(2)
                except Exception as error:
                    self.thermostat.exit()
                    raise error
            return reading
        return None