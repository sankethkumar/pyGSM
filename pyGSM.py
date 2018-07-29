import glob
import serial

class gsm(object):
	def __init__(self):
		ports = glob.glob('/dev/ttyUSB[0-9]*')
		if ports:
			self.usb = serial.Serial(ports[0],timeout=0.1)
		else:
			print 'Device Not Connected'
			raw_input()
			exit()

		self.incoming_call = 0

	def readline(self):
		line = self.usb.readline().replace('\r\n','')	
		if line == 'RING':
			self.incoming_call = 1
		elif line == 'NO CARRIER' and self.incoming_call:
			self.incoming_call = 0
		return line

	def isOK(self):
		while True:
			line = self.readline()		
			if line:
				if 'OK' in line:
					return True
				else:
					return False
			else:
				pass
	
	def echo_off(self): 
		self.usb.write('ATE0')
		while self.usb.read(): pass
		self.usb.write('\n')
		if self.isOK():
			print 'Echo OFF Success'
		else:
			print 'Echo OFF Fail'

	def dtmf_on(self):
		self.usb.write(b'AT+DDET=1\n')
		if self.isOK():
			print 'DTMF Detection Enabled'
		else:
			print 'DTMF Detection Enabling Failed. Check SIM Card'

if __name__ == '__main__':

	mygsm = gsm()
	mygsm.echo_off()
	mygsm.dtmf_on()
	
	
