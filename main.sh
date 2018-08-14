#!/bin/bash

### Command to get the USB Serial port
x=$(ls /dev/ | grep ttyUSB*)

### Forever be looking for conection of USB Serial
###  When connected, execute the main script
###  When USB disconnected, kill the main script
while :
do
	### Wait for connection of USB Serial Port	
	while [ -z ${x} ] 
	do 
		sleep 1
		x=$(ls /dev/ | grep ttyUSB*)
	done

	### Execute the relavent script
	sleep 5
	python /home/sanketh/Documents/janastu/ivr/pyGSM/bin/wodaabe_bcp.py &
	#sleep 5
	#/usr/bin/python /home/sanketh/Documents/janastu/ivr/pyGSM/serial_port.py

	### Wait for disconnection of USB Serial Port	 
	while [ ! -z ${x} ] 
	do 
		sleep 1
		x=$(ls /dev/ | grep ttyUSB*)
	done

	### Killing the script upon disconnection
	kill -9 $(ps aux | grep '[w]odaabe'| awk '{print $2}')
done
