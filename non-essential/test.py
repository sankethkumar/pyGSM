import os 

os.system("xterm -e 'bash -c \"python /home/sanketh/Documents/janastu/ivr/pyGSM/serial_port.py; bash\" ' &")
raw_input()
os.system("killall xterm")

'''
import serial_port

usb = serial_port.port()

while True:
	line = usb.readline()
	if line: print 'In: ', line

	line = raw_input('To send: ')
	if line: usb.write(line) 
'''
