import re
import time
import pmutools

from typing import NamedTuple
from influxdb import InfluxDBClient

from pprint import pprint

class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float

class StatusData(NamedTuple):
    location: str
    measurement: str
    value: bool

class PMUBridge:
    '''
    For now we hardcode the influxdb bridge as this is the
    only one currently supported. However, in the future this 
    library should be responsible to determine the correct module
    and execute it
    '''
    def __init__(self,config={}):
        self.config = config
        if 'regex' in self.config:
            self.re_topic = re.compile(self.config.get('regex'))
        self._init_influxdb_database()

    def parse_message(self, client, userdata, msg):
        if hasattr(msg,'topic') and hasattr(msg,'payload'):
            match = self.re_topic.match(msg.topic)
            payload = msg.payload.decode('utf-8')
            if match:
                matched = match.groupdict()
                if all (key in matched for key in ('floor','room','measurement')):
                    if matched.get('room'):
                        location = matched.get('room')
                    else:
                        location = matched.get('floor')
                    measurement = matched.get('measurement')
                    if payload in ('On','Off'):
                        data = StatusData(location,measurement,payload)
                    elif re.match(r'^-?\d+(?:\.\d+)?$', payload):
                        data = SensorData(location,measurement,float(payload))
                    else:
                        data = None
                    self.log.debug(f'{measurement.capitalize()} reading received from {location}: {payload}')
                    self._send_data(data)

    def _init_influxdb_database(self):
        databases = None
        self.log.debug('Initializing the InfluxDB interface.')
        while not databases:
            try:
                databases = self.client.get_list_database()
            except requests.exceptions.ConnectionError as errc:
                self.log.error('Error Connecting: {error}'.format(error=errc))
                self.log.warning('Connection to InfluxDB failed. Reconnect in {retry} seconds.'.format(retry=60))
                time.sleep(60)
        if len(list(filter(lambda x: x['name'] == self.database, databases))) == 0:
            self.client.create_database(self.database)
        self.client.switch_database(self.database)

    def _send_data(self,data):
        '''
        At the moment all data tuple have to have these exact
        keys: measurement, location, value.
        '''
        if hasattr(data,'measurement'):
            json_body = [{
                'measurement': data.measurement,
                'tags': {
                    'location': data.location
                },
                'fields': {
                    'value': data.value
                }
            }]
            self.client.write_points(json_body)

    def run(self,exit):
        if hasattr(self, 'connection') and self.topics:
            self.connection.connect(self.topics)
            if callable(self.parse_message):
                self.connection.on_message(self.parse_message)
            while not exit.is_set():
                exit.wait(self.interval)
            self.stop()

    def stop(self):
        self.log.debug(f'Stopping bridge.')
        if hasattr(self,'connection'):
            self.connection.disconnect()
        self.log.debug(f'Bridge is stopped.')        

    @property
    def client(self):
        if not hasattr(self,'_client'):
            self._client = InfluxDBClient(self.config.get('address'),8086,self.config.get('user'),self.config.get('password'),None)
        return self._client

    @property
    def database(self):
        if 'database' in self.config:
            return self.config.get('database')
        return None

    @property
    def manager(self):
        if 'manager' in self.config:
            manager = self.config.get('manager')
            if isinstance(manager,pmutools.PMUManager):
                return manager
        return None

    @property
    def log(self):
        if hasattr(self.manager,'log'):
            return self.manager.log
        return None            

    @property
    def connection(self):
        if hasattr(self.manager,'connection'):
            return self.manager.connection
        return None            

    @property
    def topics(self):
        if 'topics' in self.config:
            return self.config.get('topics')
        return None

    @property
    def interval(self):
        if 'interval' in self.config:
            return self.config.get('interval')
        return None