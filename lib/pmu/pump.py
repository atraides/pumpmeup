import re
import time
import board
import digitalio
import pmu.controller

class PMUPump:
    def __init__(self,controller):
        if isinstance(controller,pmu.controller.PMUController):
            self.controller = controller
            if hasattr(self.controller,'provide'):
                self._provider_topic = f'{self.location}/{self.capability}/controllers/{self.floor}/status'
            self.re_topic = re.compile(r'^(?P<location>[^/]+)/(?P<capability>[^/]+)/controllers/(?P<floor>[^/]+)/manage$')
            if self.floor and self.pin:
                self.log.debug(f"Initialize pump for '{self.floor}' on pin '{self.pin}'")
                self.io = digitalio.DigitalInOut(self.pin)
                self.io.direction = digitalio.Direction.OUTPUT
                self.turn_on()
                self.turn_off()

    def turn_on(self):
        self.io.value = False
        self.io_state = False
        time.sleep(0.5)
        return self

    def turn_off(self):
        self.io.value = True
        self.io_state = True
        time.sleep(0.5)
        return self

    def change_state(self,new_state):
        if new_state != self.io.value:
            self.io.value = new_state
            self.log.debug(f'State changed to {self.state}')
            if hasattr(self,'_provider_topic'):
                self.log.debug(f"Publishing state change to '{self._provider_topic}': {self.state}")
                self.controller.connection.publish(self._provider_topic,payload=self.state,retain=True)

    def str2state(self,string):
        return string.lower() not in ('yes', 'true', 't', '1', 'on')

    def process_message(self, client, userdata, msg):
        if hasattr(msg,'topic') and hasattr(msg,'payload'):
            self.log.debug(f'We got a message in topic {msg.topic}')
            if self.re_topic.match(msg.topic):
                state = self.str2state(msg.payload.decode('utf-8'))
                self.log.debug(f'''We got a request to change our state to '{msg.payload.decode('utf-8')}'.''')
                self.log.debug(f'''Our current state is '{self.state}'.''')
                self.change_state(state)

    @property
    def state(self):
        if hasattr(self,'io'):
            if hasattr(self.io,'value'):
                if self.io.value:
                    return 'Off'
                return 'On'
        return None

    @property
    def log(self):
        if hasattr(self.controller,'log'):
            return self.controller.log
        return None

    @property
    def location(self):
        if hasattr(self.controller,'location'):
            return self.controller.location
        return None
    
    @property
    def capability(self):
        if hasattr(self.controller,'capability'):
            return self.controller.capability
        return None

    @property
    def provide(self):
        if hasattr(self.controller,'provide'):
            return self.controller.provide
        return None

    @property
    def floor(self):
        if hasattr(self.controller,'floor'):
            return self.controller.floor
        return 'default'

    @property
    def pin(self):
        if hasattr(self.controller,'pin'):
            if hasattr(board,self.controller.pin):
                return getattr(board,self.controller.pin)
        return None