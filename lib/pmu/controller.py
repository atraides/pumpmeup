from pmu.pump import PMUPump

class PMUController:
    def __init__(self,config={}):
        for key in config:
            self.set_arguments(name=key,config=config)

        self.topic = [self.location,self.capability,'controllers',self.floor]

        if hasattr(self, 'consume'):
            ''' We have an network resource we need to listen on '''
            self.topics = []
            if isinstance(self.consume,list):
                for resource in self.consume:
                    self.topics.append(['/'.join([*self.topic,resource]),1])
                    self.log.debug(f"Controller is set to consume {'/'.join([*self.topic,resource])}")

        ''' For now let's hardcode a relay pump control '''
        if hasattr(self,'type'):
            if self.type == 'pump':
                self._device = PMUPump(self)

        if hasattr(self, 'connection'):
            self.connection.connect(self.topics)
            if hasattr(self,'_device'):
                if callable(self._device.process_message):
                    self.connection.on_message(self._device.process_message)

    def set_arguments(self,name=None,config=None):
        if name in config:
            setattr(self, name ,config.get(name))

    def start_controller(self,exit):
        while not exit.is_set():
            exit.wait(self.interval)
        self.stop_controller()

    def stop_controller(self):
        controller = '/'.join([self.location,self.capability,self.floor])
        self.log.debug(f'Stopping {controller}.')
        self._device.turn_off()
        if hasattr(self,'connection'):
            self.connection.disconnect()
        self.log.debug(f'Controller {controller} is stopped.')
