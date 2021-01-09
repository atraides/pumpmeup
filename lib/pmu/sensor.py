import time
import board
import adafruit_dht

class PMUSensor:
    def __init__(self,config={}):
        for key in config:
            self.set_arguments(name=key,config=config)

        if hasattr(self, '_dht_device') and hasattr(self, 'pin'):
            self._device = self._dht_device(self.pin)

        if hasattr(self, 'connection'):
            self.connection.connect()

    def set_arguments(self,name=None,config=None):
        if name in config:
            setattr(self, name ,config.get(name))

    def read_sensor(self):
        if hasattr(self,'_device'):
            for measurement in self.provide:
                sensor = '/'.join([self.location,self.capability,'sensors',self.floor,self.room,measurement])
                self.log.debug(f"Attempting to read sensor {sensor}.")
                reading = None
                while not reading:
                    try:                    
                        reading = getattr(self._device,measurement)
                        self.log.debug(f"Successful read of sensor {sensor}: {reading}")
                        if hasattr(self,'connection'):
                            self.connection.publish(sensor,reading)
                    except RuntimeError as error:
                        # Errors happen fairly often, DHT's are hard to read, just keep going
                        self.log.warning(f'An error occured reading the DHT sensor: {error.args[0]}')
                        time.sleep(2)
                    except Exception as error:
                        self._device.exit()
                        raise error

    def start_sensor(self,exit):
        while not exit.is_set():
            self.read_sensor()
            exit.wait(self.interval)
        self.stop_sensor()

    def stop_sensor(self):
        sensor = '/'.join([self.location,self.capability,self.floor,self.room])
        self.log.debug(f'Stopping {sensor}.')
        if hasattr(self,'connection'):
            self.connection.disconnect()
        self.log.debug(f'Sensor {sensor} is stopped.')

    @property
    def interval(self):
        if hasattr(self,'_interval'):
            return self._interval
        return 60
        
    @property
    def model(self):
        return self._model
    
    @model.setter
    def model(self,model):
        if model in dir(adafruit_dht):
            self._model = model
            self._dht_device = getattr(adafruit_dht,model)
        else:
            self._model = None

    @property
    def pin(self):
        return self._pin
    
    @pin.setter
    def pin(self,pin):
        if pin in dir(board):
            self._pin = getattr(board,pin)
        else:
            self._pin = None
