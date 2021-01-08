import os
import sys
import signal
import threading
import logging.config

from pathlib import Path
from yaml import safe_load
from typing import NamedTuple

from pprint import pprint

from lib.pmu.PMUSensor import PMUSensor
from lib.pmu.PMUConnection import PMUConnection

class PMUManager():
    def __init__(self,arguments={}):
        for key in vars(arguments):
            self.set_arguments(name=key,arguments=arguments)

        self.base_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.load_config()

        signal.signal(signal.SIGTERM, self.signal_catcher)
        signal.signal(signal.SIGHUP, self.signal_catcher)
        signal.signal(signal.SIGINT, self.signal_catcher)

    def set_arguments(self,name=None,arguments=None):
        if hasattr(arguments,name):
            setattr(self, name ,getattr(arguments,name))

    def load_config(self):
        if not hasattr(self,'config_file'):
            self.config_file = Path(f'{self.base_dir}/config.yml')
            if self.config_file.exists():
                self.config = safe_load(self.config_file.open())
        return self

    def init_log(self):
        if 'logger' in self.config:
            logger = None
            logging.config.dictConfig(self.config.get('logger'))
            if self.debug and 'debug' in logging.root.manager.loggerDict:
                logger = 'debug'
            elif 'main' in logging.root.manager.loggerDict:
                logger = 'main'
            self._log = logging.getLogger(logger)
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._log=logging.getLogger()
            self._log.setLevel(logging.DEBUG)
            self._log.addHandler(handler)

    def load_sensors(self):
        ''' Add a bit more validation to the function '''
        self._sensors=[]
        for capability in self.config:
            capability_data = self.config.get(capability)
            if 'sensors' in capability_data:
                for sensor in capability_data.get('sensors'):
                    sensor = PMUSensor({
                        **sensor,
                        **{
                            'log':self.log,
                            'location': self.location,
                            'connection': self.connection,
                            'capability': capability
                        }
                    })
                    self._sensors.append(sensor)

    def start_sensors(self):
        self.threads = []
        self.exit_thread = threading.Event()
        for sensor in self.sensors:
            self.stop_threads = False
            thread = threading.Thread(target=sensor.start_sensor, args=(self.exit_thread,))
            thread.name = f'PMUSensor-{sensor.room}'
            thread.start()
            self.threads.append(thread)

    def stop_sensors(self):
        self.log.debug(f'Stopping all sensors.')
        for thread in self.threads:
            self.exit_thread.set()
            thread.join()
        self.log.debug(f'All sensors stopped.')

    def load_connection(self):
        if 'connection' in self.config:
            self._connection = PMUConnection({
                **self.config.get('connection'),
                'log': self.log
            })
        return None

    def signal_catcher(self, signalNumber, frame):
        if signalNumber == signal.SIGTERM: # SIGTERM
            self.log.info('SIGTERM received! Quitting.')
            self.graceful_exit()
        if signalNumber == 1: # SIGHUP
            self.log.info('SIGHUP received. Restarting.')
        if signalNumber == 2: # SIGINT
            self.log.info('SIGINT received. Quitting.')
            self.graceful_exit()

    def graceful_exit(self):
        self.stop_sensors()

    @property
    def sensors(self):
        if not hasattr(self,'_sensors'):
            self.load_sensors()
        return self._sensors
   
    @property
    def connection(self):
        if not hasattr(self,'_connection'):
            self.load_connection()
        return self._connection
    
    @property
    def location(self):
        if 'location' in self.config:
            return self.config.get('location')
        return 'default'

    @property
    def log(self):
        if not hasattr(self,'_log'):
            self.init_log()
        return self._log
