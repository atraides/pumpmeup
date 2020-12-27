import sys
import time
import logging
import paho.mqtt.client as mqtt

class MQTTClient(mqtt.Client):
   
    def __init__(self,cname,**kwargs):
        super(MQTTClient, self).__init__(cname,**kwargs)
        self.last_pub_time=time.time()
        self.topic_ack=[]
        self.run_flag=True
        self.subscribe_flag=False
        self.bad_connection_flag=False
        self.connected_flag=False
        self.disconnect_flag=False
        self.disconnect_time=0.0
        self.pub_msg_count=0
        self.devices=[]

    def setLogger(self,logger):
        if logger:
            self.logger=logger
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger=getLogger()
            self.logger.setLevel(logging.DEBUG)
            self.logger.addHandler(handler)


    def initialize(self,broker,logger=None):
        self.setLogger(logger)
        self.logger.info('MQTT configuration found. Initializing MQTT connection.')

        self.on_connect=self.connect_check
        self.safe_connect(broker)
        self.loop_start()
        while not self.connected_flag:
            time.sleep(1)

    def connect_check(self,client, userdata, flags, rc):
        if rc==0:
            client.connected_flag=True #set flag
            self.logger.info("MQTT connection succesful.")
        else:
            self.logger.warning("MQTT connection failed with return code=",rc)

    def shutdown(self):
        self.loop_stop
        self.disconnect()

    def safe_connect(self,address,port=1883,keepalive=60,retry=120):
        if address:
            while not self.connected_flag:
                try:
                    self.connect(address,port,keepalive)
                    break
                except OSError as error:
                    if error.errno == 113: # No route to host
                        self.logger.warning('Can\'t connect to the MQTT broker (No route to host), retrying in {retry} seconds.'.format(retry=retry))
                    pass
                self.logger.warning('MQTT connection failed. Retrying in {retry} seconds.'.format(retry=retry))
                time.sleep(retry)
