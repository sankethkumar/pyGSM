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
		self.outgoing_call = 0
		self.dtmf_status = 0
		self.dtmf_value = 0
		self.on_hook = 0
		self.incoming_call_alert = 0

	def readline(self):
		line = self.usb.readline().replace('\r\n','')	
		if line == 'RING' and not self.incoming_call:
			self.incoming_call = 1
			raise Exception("Ringing")
		elif line == 'NO CARRIER':
			if self.incoming_call: 
				self.incoming_call = 0
			elif self.on_hook: 
				self.on_hook = 0
				raise Exception("Outgoing Call Terminated")
		return line

	def isOK(self):
		while True:
			line = self.readline()		
			if line:
				if 'OK' in line: return True
				else: return False

	def isRinging(self):
		try:		
			line = self.readline()
		except Exception as error:
			print error
			if error == 'Ringing': return True
		return False


	def echo_off(self): 
		self.usb.write('ATE0')
		while self.usb.read():	pass
		self.usb.write('\n')
		if self.isOK():
			return 'Echo OFF Success'
		else:
			return 'Echo OFF Fail'

	def dtmf_on(self):
		self.usb.write('AT+DDET=1\n')
		if self.isOK():
			return 'DTMF Detection Enabled'
			self.dtmf_status = 1
		else:
			return 'DTMF Detection Enabling Failed. Check SIM Card'

	def outgoing_call_status_on(self):
		self.usb.write('AT+MORING=1\n')
		if self.isOK():
			return 'Outgoing Call Status Identification Enabled'
		else:
			return 'Outgoing Call Status Identification Failed'

	def readcallerID(self):
		line = self.readline()		
		if self.incoming_call and not self.on_hook:		
			while 'CLIP' not in line:
				line = self.readline()
			return line.split(',')[0].split('"')[1]
		return 'No Incoming Call'

	def readDTMF(self):
		line = self.readline()
		if self.on_hook:
			while 'DTMF' not in line:
				line = self.readline()
			return line.split(':')[1]
		return 'No Call'

	def callnumber(self,number):
		if self.on_hook:
			return 'Call in progress'
		elif self.incoming_call: 
			return 'Incoming call...'
		else:
			self.usb.write('ATD'+number+';\n')
			if self.isOK():
				self.outgoing_call = 1				
				return 'Calling ' + number + '...'
			return 'Calling Failed!'
	
	def outgoing_call_status(self):
		line = self.readline()
		if self.outgoing_call:
			if line == 'MO RING':
				return 'Ringing...'
			elif line == 'MO CONNECTED':
				self.on_hook = 1
				return 'Hello!'
			elif line == 'NO CARRIER'and not self.incoming_call:
				self.on_hook = 0
				self.outgoing_call = 0
				return 'Call Terminated'
			else:
				return ''
		return 'Call Not Initiated'

	def get_DTMF(self):
		if self.on_hook:
			line = self.readline()
			self.usb.reset_input_buffer()
			if not line: return line
			else:
				if 'DTMF' in line: return line.split(':')[1]
				elif 'NO CARRIER' in line: 
					self.on_hook = 0
					self.outgoing_call = 0
					return 'STOP'
		return ''
		

if __name__ == '__main__':

	mygsm = gsm()
	print mygsm.echo_off()
	print mygsm.dtmf_on()
	print mygsm.outgoing_call_status_on()
	while True:
		if mygsm.isRinging():
			print 'Call from ' + mygsm.readcallerID()
