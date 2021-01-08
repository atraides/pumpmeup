import sys
import time
import threading
import argparse

from pmutools import PMUManager
from pprint import pprint

def main():
    manager = PMUManager(arguments)
    manager.start_sensors()
    manager.start_controllers()
            
parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()

if __name__ == '__main__':
    main()