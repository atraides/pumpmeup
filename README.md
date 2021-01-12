[![Codacy Badge](https://api.codacy.com/project/badge/Grade/5b4c73892a27441dadad671c418a4413)](https://app.codacy.com/gh/atraides/pumpmeup?utm_source=github.com&utm_medium=referral&utm_content=atraides/pumpmeup&utm_campaign=Badge_Grade)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/atraides/pumpmeup.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/atraides/pumpmeup/alerts/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/atraides/pumpmeup.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/atraides/pumpmeup/context:python)
# pumpmeup
Pump management for houses

## Additional steps on Raspberry Pi ( dietpi )
```
sudo apt update && sudo apt upgrade -y
```
### Install python3 with git and make it the default python interpreter
```
sudo apt install -y python3 git python3-pip python3-venv libgpiod2
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
pip3 install -r requirements.txt
```
