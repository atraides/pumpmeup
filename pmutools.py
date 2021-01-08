import os
import sys
import signal
import logging.config

from yaml import safe_load
from pathlib import Path

def __configExists(name):
    config_file = Path('{config}/{name}.yml'.format(config=config_dir,name=name))
    if config_file.exists():
        return config_file
    return None

def getConfig(name):
    if __configExists(name):
        return safe_load(__configExists(name).open())        
    return None

def isConfigured(device):
    if __configExists(device):
        return True
    return False

def getLogger(debug):
    global logger
    if isConfigured('logging'):
        logging.config.dictConfig(getConfig('logging'))
        if debug and 'debug' in logging.root.manager.loggerDict:
            logger = logging.getLogger('debug')
        elif 'main' in logging.root.manager.loggerDict:
            logger = logging.getLogger('main')
        else:
            logger = logging.getLogger()
        return logger
    else:
        return None

def signal_catcher(signalNumber, frame):
    if signalNumber == signal.SIGTERM: # SIGTERM
        logger.info('SIGTERM received! Quitting.')
        gracefulExit()
    if signalNumber == 1: # SIGHUP
        logger.info('SIGHUP received. Restarting.')
    if signalNumber == 2: # SIGINT
        logger.info('SIGINT received. Quitting.')
        gracefulExit()

def gracefulExit():
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_catcher)
signal.signal(signal.SIGHUP, signal_catcher)
signal.signal(signal.SIGINT, signal_catcher)

script_dir = Path(os.path.dirname(os.path.realpath(__file__)))
base_dir = script_dir
config_dir = '{basedir}/config'.format(basedir=base_dir)
lib_dir = '{basedir}/lib'.format(basedir=base_dir)

if os.path.exists(lib_dir):
    sys.path.append(lib_dir)