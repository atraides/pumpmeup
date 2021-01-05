# pumpmeup
Pump management for houses

## Additional steps on Raspberry Pi ( dietpi )
```
sudo apt update && sudo apt upgrade -y
```
### Install python3 with git and make it the default python interpreter
```
sudo apt install -y python3 git python3-pip python3-venv
sudo update-alternatives --install /usr/bin/python python $(which python2) 1
sudo update-alternatives --install /usr/bin/python python $(which python3) 2
sudo update-alternatives --config python
```

### Enable I2C and SPI
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c
https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-spi
```
reboot
ls -ltra /dev/i2c* /dev/spi*
```

### Create and activate a virtual environment
```
python -m venv production
source production/bin/activate
```

### Install the python libraries from adafruit
```
pip3 install RPI.GPIO
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-dht
```

### Install the libgpiod2
```
sudo apt install -y libgpiod2
```

### Install the paho-mqtt library and pyyaml
```pip3 install paho-mqtt
pip3 install pyyaml
```

### Create the logfile and give it to our user
```
sudo touch /var/log/pumpmeup.log
sudo chown dietpi.gpio /var/log/pumpmeup.log 
sudo chmod 664 /var/log/pumpmeup.log
```

### Add user to the gpio group
```
adduser dietpi gpio
```
