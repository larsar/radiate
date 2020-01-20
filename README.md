# radiate
The goal is to use a Raspberry Pi Zero with WiFi and Bluetooth to forward readings
from Airthings Wave to Home Assistant via MQTT. None of the other projects I found
worked with my device. This work is heavily inspired by
[radonwave](https://github.com/marcelm/radonwave) and [wave-reader](https://github.com/Airthings/wave-reader).

## Install
```
sudo apt-get install virtualenv
make venv
source venv/bin/activate
make requirements
```

## Find device id
One way to find the device id is to place the Raspberry Pi next to the Airthings
device and then run a bluetooth scan. Look for the device with the highest signal
strength. (RSSI: -40 to -50 indicates great signal strength)
```
$ sudo bluetoothctl
Agent registered
[bluetooth]# scan on
Discovery started
[CHG] Controller B8:27:EB:0C:B7:2B Discovering: yes
[CHG] Device DC:56:E7:42:E8:F8 RSSI: -96
[CHG] Device DC:56:E7:42:E8:F8 TxPower: 12
[NEW] Device 5E:99:A3:1B:AA:5C 5E-99-A3-1B-AA-5C
[CHG] Device DC:56:E7:42:6A:70 RSSI: -92
[CHG] Device DC:56:E7:42:6A:70 TxPower: 12
[NEW] Device 61:06:DC:F2:9B:30 61-06-DC-F2-9B-30
[CHG] Device E0:7D:EA:08:22:66 RSSI: -43
[CHG] Device 61:80:10:78:42:3C RSSI: -87
[CHG] Device 61:80:10:78:42:3C TxPower: 24
[CHG] Device 50:83:16:5E:A3:EC RSSI: -96
...
```
In my case, the device id is ```E0:7D:EA:08:22:66```.

## Run
Without MQTT configuration, the script will only print the data to stdout. The data
can be forwarded to a MQTT server. MQTT authentication is optional. Username is
specified as parameter, but the password must be set as an environment variable (MQTT_PASSWORD).

The short term radon measurement is an average over the last 24 hours thus there is no point in
reading the sensor data very frequently. The default is every 20 minutes.

Airthings Wave can only communicate with a single device at a time. The script will connect to 
the device, read the sensor data and then close the connection. Between readings other clients, 
like mobile apps, can communicate with the device.   

```
# Reads the sensor every 5 seconds and prints the sensor data
$ python radiate.py --wait 5 e0:7d:ea:08:22:66
{'sensor_version': 1, 'humidity': 53.0, 'radon_short_term_avg': 132, 'radon_long_term_avg': 84, 'temperature': 12.74, 'timestamp': '2020-01-15T20:06:34.568825', 'id': 'fff9469f-0d17-4040-853d-c0ceea1107ad'}
```

```
export MQTT_PASSWORD=secret
python radiate.py --mqtt 192.168.76.100 --topic airthings --username my_username e0:7d:ea:08:22:66
```

