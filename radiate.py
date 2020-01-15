#!/usr/bin/env python3
import json
import os
import signal
import sys
import time
from argparse import ArgumentParser
from datetime import datetime
from struct import unpack
from uuid import uuid4

from bluepy import btle


class Radiate:
    debug = False
    wave_device = None
    mqtt_client = None

    def conv2radon(radon_raw):
        radon = "N/A"  # Either invalid measurement, or not available
        if 0 <= radon_raw <= 16383:
            radon = radon_raw
        return radon

    def connect_and_read(self):
        if self.debug:
            print('Services')
            for service in self.wave_device.services:
                print(service)

            print('Characteristics')
            for ch in self.wave_device.getCharacteristics():
                print(ch.getHandle(), ch.uuid, ch.propertiesToString())

        service = self.wave_device.getServiceByUUID(btle.UUID('b42e4a8e-ade7-11e4-89d3-123b93f75cba'))

        measurement = {}
        for ch in service.getCharacteristics():
            name = ch.uuid.getCommonName()
            if name == 'b42e4dcc-ade7-11e4-89d3-123b93f75cba':
                raw = ch.read()
                data = unpack('BBBBHHHHHHHH', raw)
                measurement['sensor_version'] = data[0]
                measurement['humidity'] = data[1] / 2.0
                measurement['radon_short_term_avg'] = Radiate.conv2radon(data[4])
                measurement['radon_long_term_avg'] = Radiate.conv2radon(data[5])
                measurement['temperature'] = data[6] / 100.0
                measurement['timestamp'] = datetime.now().isoformat()
                measurement['id'] = str(uuid4())

        self.wave_device.disconnect()
        return measurement

    def on_connect(self, client, userdata, flags, rc):
        desc = {}
        desc[1] = 'incorrect protocol version'
        desc[2] = 'invalid client identifier'
        desc[3] = 'server unavailable'
        desc[4] = 'bad username or password'
        desc[5] = 'not authorised'

        if rc == 0:
            client.connected_flag = True  # set flag
            print("connected OK Returned code=0")
        else:
            print("Bad connection Returned code={} details={}".format(rc, desc[rc]))

    def main(self):

        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        parser = ArgumentParser()
        parser.add_argument('--wait', default=1200, type=int,
                            help='Seconds to wait between queries. Do not choose this too low as the '
                                 'radon levels are only updated once every 60 minutes. Set to 0 to query '
                                 'only once. Default: 1200 '
                                 '(20 minutes)')
        parser.add_argument('--mqtt', help='MQTT server')
        parser.add_argument('--topic', help='MQTT topic')
        parser.add_argument('--username',
                            help='MQTT username (if the user has a password, set it in the MQTT_PASSWORD environment variable')
        parser.add_argument('--debug', help='Debug output', action='store_true')
        parser.add_argument('device_address', metavar='BLUETOOTH-DEVICE-ADDRESS')
        args = parser.parse_args()
        device_address = args.device_address

        if args.mqtt and not args.topic:
            parser.error('Provide also a --topic when you use --mqtt')
        if args.mqtt:
            try:
                import paho.mqtt.client as mqtt
                self.mqtt_client = mqtt.Client("radiate")
                self.mqtt_client.connected_flag = False
                if args.username:
                    password = os.environ.get('MQTT_PASSWORD', None)
                    self.mqtt_client.username_pw_set(args.username, password=password)
                self.mqtt_client.loop_start()
                self.mqtt_client.on_connect = self.on_connect
                self.mqtt_client.connect(args.mqtt)
                while not self.mqtt_client.connected_flag:  # wait in loop
                    print("Waiting for MQTT connection...")
                    time.sleep(1)
            except Exception as e:  # unsure which exceptions connect can cause, so need to catch everything
                print('Could not connect to MQTT broker: {}'.format(e))
                client = None
        else:
            client = None
        while True:
            try:
                self.wave_device = btle.Peripheral(device_address)
                measurement = self.connect_and_read()
                if self.mqtt_client:
                    self.mqtt_client.publish(args.topic, json.dumps(measurement))
                else:
                    print(measurement)
                    sys.stdout.flush()
            except btle.BTLEException as e:
                print('Bluetooth error: {}'.format(e))
                sys.stdout.flush()
            finally:
                if self.wave_device:
                    self.wave_device.disconnect()
                    self.wave_device = None
            if args.wait == 0:
                break
            time.sleep(args.wait)

    def shutdown(self, signum, frame):
        print("Shutting down...")
        if self.wave_device:
            print("Disconnecting from Bluetooth device...")
            self.wave_device.disconnect()
        if self.mqtt_client:
            print("Closing MQTT connection...")
            self.mqtt_client.disconnect()
        sys.stdout.flush()
        exit(0)


if __name__ == '__main__':
    r = Radiate()
    r.main()
