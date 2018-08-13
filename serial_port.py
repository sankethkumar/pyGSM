import glob
import serial
import os
#import time

projectpath =  os.path.split(os.path.realpath(__file__))[0]	
serial_in = projectpath + '/bcp_output/debug/' + 'serial_in_buffer'
serial_out = projectpath + '/bcp_output/debug/' + 'serial_out_buffer'

class port(object):
	
	def __init__(self):
		self.buff_in = open (serial_in,'a+',os.O_NONBLOCK)
		self.buff_in.readlines()
		self.buff_out = open(serial_out, 'a+', os.O_NONBLOCK)	
	
	def write(self,line):
		self.buff_out.write(line)
		self.buff_out.flush()
		#time.sleep(0.2)

	def readline(self):
		return self.buff_in.readline()

	def __del__(self):
		self.buff_in.close()
		self.buff_in.close()
	
if __name__ == '__main__':

	ports = glob.glob('/dev/ttyUSB[0-9]*')
	if ports:
		usb = serial.Serial(ports[0],timeout=0.1)
	else:
		print 'Device Not Connected'
		raw_input()
		exit()
	serial_input = open(serial_in, 'a+', os.O_NONBLOCK)
	serial_output = open(serial_out, 'a+', os.O_NONBLOCK)
	serial_output.readlines()
	try: 
		while True:
			line = serial_output.readline()
			if line: usb.write(line)

			line = usb.readline().replace('\r\n','')
			if line:
				print line
				serial_input.write(line)
				serial_input.write('\n')
				serial_input.flush()
	except:
		serial_input.close()
		serial_output.close()


