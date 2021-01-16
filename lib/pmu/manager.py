import sys
import signal
import threading
import logging.config

from pathlib import Path
from yaml import safe_load

from pmu.sensor import PMUSensor
from pmu.controller import PMUController
from pmu.connection import PMUConnection
from pmu.bridge import PMUBridge

class PMUManager():
    def __init__(self,arguments=None):
        if arguments:
            for key in vars(arguments):
                self.set_arguments(name=key,arguments=arguments)

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
        if hasattr(self,'threads'):
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

    def load_controllers(self):
        ''' Add more validation to the load sequence. '''
        self._controllers=[]
        for capability in self.config:
            capability_data = self.config.get(capability)
            if 'controllers' in capability_data:
                for controller in capability_data.get('controllers'):
                    controller = PMUController({
                        **controller,
                        'log':self.log,
                        'location': self.location,
                        'connection': self.connection,
                        'capability': capability
                    })
                    self._controllers.append(controller)

    def start_controllers(self):
        self._controller_threads = []
        self._controller_exit = threading.Event()
        for controller in self.controllers:
            thread = threading.Thread(target=controller.start_controller, args=(self._controller_exit,))
            thread.name = f'PMUController-{controller.floor}'
            thread.start()
            self._controller_threads.append(thread)

    def stop_controllers(self):
        self.log.debug(f'Stopping all controllers.')
        if hasattr(self,'_controller_threads'):
            for thread in self._controller_threads:
                self._controller_exit.set()
                thread.join()
        self.log.debug(f'All controllers stopped.')

    def load_bridges(self):
        ''' Add more validation to the load sequence. '''
        self._bridges=[]
        if 'bridges' in self.config:
            for bridge in self.config.get('bridges'):
                _bridge_config = self.config.get('bridges').get(bridge) # This is ugly af and need to be fixed.
                self.log.info(f"Initialzing bridge '{bridge}.")
                _bridge = PMUBridge({**_bridge_config,'manager':self})
                self._bridges.append(_bridge)

    def start_bridges(self):
        self._bridge_threads = []
        self._bridge_exit = threading.Event()
        for bridge in self.bridges:
            thread = threading.Thread(target=bridge.run, args=(self._bridge_exit,))
            thread.name = f'PMUBridge-influxdb'
            thread.start()
            self._bridge_threads.append(thread)

    def stop_bridges(self):
        self.log.debug(f'Stopping all bridges.')
        if hasattr(self,'_bridge_threads'):
            for thread in self._bridge_threads:
                self._bridge_exit.set()
                thread.join()
        self.log.debug(f'All controllers stopped.')

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
        self.stop_controllers()
        self.stop_bridges()

    @property
    def sensors(self):
        if not hasattr(self,'_sensors'):
            self.load_sensors()
        return self._sensors

    @property
    def controllers(self):
        if not hasattr(self,'_controllers'):
            self.load_controllers()
        return self._controllers

    @property
    def bridges(self):
        if not hasattr(self,'_bridges'):
            self.load_bridges()
        return self._bridges

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
