#!/usr/bin/env make

requirements:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

venv:
	virtualenv -p python3 venv

bluetooth-on:
	echo "power on" | sudo bluetoothctl

bluetooth-off:
	echo "power off" | sudo bluetoothctl

