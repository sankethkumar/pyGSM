import glob
import serial
import os

def incoming_call_list(number):
	f = open ('call_list_queue','a+')
	if (number+'\n') not in f.readlines():
		f.write(number+'\n')
	f.flush()
	f.close()

def get_number():
	f = open ('call_list_queue','r')
	number = f.readline().replace('\n','')
	f.close()
	return number

def update_call_list(number):
	f = open ('call_list_queue','r+w')
	call_list = f.readlines()
	#print call_list
	call_list.remove(number+'\n')
	print 'Call list now: ', call_list
	f.truncate(0)
	f.write(''.join(call_list))
	f.flush()
	f.close()

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
		f = open ('call_list_queue','r')
		numbers = f.readlines()
		f.close()		
		self.call_log = len(numbers)

	def __del__(self):
		self.usb.write('ATH\n')

	def readusb(self):
		return self.usb.readline().replace('\r\n','')

	def readline(self):
		line = self.readusb()
		if line: print line
		if line == 'RING' and not self.incoming_call:
			self.incoming_call = 1
			line = self.readusb()
			line = self.readusb()
			if 'CLIP' in line: 
				incoming_call_list(line.split(',')[0].split('"')[1])
				line = self.readusb()
		if self.incoming_call:
			if line == 'NO CARRIER':
				self.incoming_call = 0
				self.call_log += 1
			return ''
		elif line == 'NO CARRIER':
			self.on_hook = 0
			raise Exception("Call Terminated")
		elif line == '+CFUN: 1': raise Exception("Call Terminated")
		return line

	def isOK(self):
		while True:
			line = self.readusb()		
			if line:
				if 'OK' in line: return True
				else: return False

	#def isRinging(self):
	#	try:		
	#		line = self.readline()
	#	except Exception as error:
	#		print error
	#		if error == 'Ringing': return True
	#	return False


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
			#return 'DTMF Detection Enabled'
			self.dtmf_status = 1
			return 1
		else:
			#return 'DTMF Detection Enabling Failed. Check SIM Card'
			return 0

	def dtmf_off(self):
		self.usb.write('AT+DDET=0\n')
		if self.isOK():
			return 1
			self.dtmf_status = 0
		else:
			return 0
	
	def clip_on(self):
		self.usb.write('AT+CLIP=1\n')
		if self.isOK():
			return 'CLIP Enabled'
		else:
			return 'CLIP Enabling Failed'
	
	def end_call(self):
		self.usb.write('ATH\n')
		self.on_hook = 0
		if self.isOK():
			self.on_hook = 0
			return 'Call Terminated'			
		else:
			return 'Something wrong with call termination '

	def outgoing_call_status_on(self):
		self.usb.write('AT+MORING=1\n')
		if self.isOK():
			return 'Outgoing Call Status Identification Enabled'
		else:
			return 'Outgoing Call Status Identification Failed'

	#def readcallerID(self):
	#	line = self.readline()		
	#	if self.incoming_call and not self.on_hook:		
	#		while 'CLIP' not in line:
	#			line = self.readline()
	#		return line.split(',')[0].split('"')[1]
	#	return 'No Incoming Call'

	def clearDTMF(self):
		i = 0
		while i<5:
			x=self.readline()
			print 'Things to Clear', x
			if not x: i += 1
			else: i = 0


	def readDTMF(self):
		#self.dtmf_on()
		line = self.readline()
		if 'DTMF' in line:
			self.clearDTMF()		#to ignore multiple key press
			#self.dtmf_off()
			return line.split(':')[1].replace(' ','')
		return ''

	def callnumber(self,number):
		if self.on_hook:
			return 'Call in progress'
		elif self.incoming_call: 
			return 'Incoming call...'
		else:
			self.usb.write('ATD'+number+';\n')
			if self.isOK():
				try: 
					line = self.readline()
					while not line == 'MO CONNECTED': 
						line = self.readline()
					self.on_hook = 1
					return 'Call Established'
				except Exception: return 'Call Not Answered'
			return 'Calling Failed!'
	
	#def outgoing_call_status(self):
	#	line = self.readline()
	#	if self.outgoing_call:
	#		if line == 'MO RING':
	#			return 'Ringing...'
	#		elif line == 'MO CONNECTED':
	#			self.on_hook = 1
	#			return 'Hello!'
	#		elif line == 'NO CARRIER'and not self.incoming_call:
	#			self.on_hook = 0
	#			self.outgoing_call = 0
	#			return 'Call Terminated'
	#		else:
	#			return ''
	#	return 'Call Not Initiated'

	#def get_DTMF(self):
	#	if self.on_hook:
	#		line = self.readline()
	#		self.usb.reset_input_buffer()
	#		if not line: return line
	#		else:
	#			if 'DTMF' in line: return line.split(':')[1]
	#			elif 'NO CARRIER' in line: 
	#				self.on_hook = 0
	#				self.outgoing_call = 0
	#				return 'STOP'
	#	return ''
		

if __name__ == '__main__':

	mygsm = gsm()
	print mygsm.echo_off()
	print mygsm.dtmf_on()
	print mygsm.outgoing_call_status_on()
	while True:
		line = mygsm.readusb()
		if line == 'RING': 
			print line
			mygsm.usb.write('ATA\n')
			while True:
				try:
					os.system("aplay ./audios/new_user.wav")
					dtmf = ''
					while not dtmf: dtmf = mygsm.readDTMF()
					print 'DTMF is', dtmf
				except Exception as error: 
					print 'Exception', error					
					break
		
