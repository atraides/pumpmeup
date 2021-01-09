import os
import sys
import argparse
from pathlib import Path

base_dir = Path(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,f'{base_dir}/lib')

from pmu.manager import PMUManager

parser = argparse.ArgumentParser(description='Gets the reading from the connected DHT11/22 sensor and publish it to an MQTT topic.')
parser.add_argument('--debug',action='store_true',help='print debug messages to stderr')
arguments = parser.parse_args()
arguments.base_dir = base_dir

def main():
    manager = PMUManager(arguments)
    manager.start_sensors()
    manager.start_controllers()
    manager.start_bridges()

if __name__ == '__main__':
    main()
    