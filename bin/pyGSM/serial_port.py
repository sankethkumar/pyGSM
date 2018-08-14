import glob			### to detect the USB Serial port
import serial		### the serial port library
import os			### for getting current working directory

''' Location of buffer files '''
projectpath =  os.path.split(os.path.realpath(__file__))[0]	
serial_in = projectpath + '/../../bcp_output/debug/' + 'serial_in_buffer'
serial_out = projectpath + '/../../bcp_output/debug/' + 'serial_out_buffer'

''' The serial port object that has access to buffer files '''
class port(object):
	
	def __init__(self):
		### Open files in non-blocking mode to be accessed by serial port and 
		### other objects
		self.buff_in = open (serial_in,'a+',os.O_NONBLOCK)
		self.buff_out = open(serial_out, 'a+', os.O_NONBLOCK)

		### Ignore the previous contents of buffer file
		self.buff_in.readlines()
		
	### To write to output buffer file
	def write(self,line):
		self.buff_out.write(line)
		self.buff_out.flush()
	
	### To read from input buffer file
	def readline(self):
		return self.buff_in.readline()

	### Close files in destructor
	def __del__(self):
		self.buff_in.close()
		self.buff_in.close()
	
if __name__ == '__main__':

	### Get the USB serial port ID
	ports = glob.glob('/dev/ttyUSB[0-9]*')
	if ports:
		usb = serial.Serial(ports[0],timeout=0.1)
	else:
		print 'Device Not Connected'
		raw_input()
		exit()

	### Open buffer files and be ready
	serial_input = open(serial_in, 'a+', os.O_NONBLOCK)
	serial_output = open(serial_out, 'a+', os.O_NONBLOCK)
	serial_output.readlines()
	
	### In infinite loop, do two tasks
	### 1. Check output buffer file, and send it out through serial port
	### 2. Read data from serial port, if any, and save it in buffer files
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


