''' The PyGSM Library '''
import serial_port		### serial port sniffer with class
import os
import signal
import time
import commands			### to get output of a bash command
import subprocess		### to open serial port

### Get location of call list queue file 
projectpath =  os.path.split(os.path.realpath(__file__))[0]
incoming_call_log = projectpath + '/../../bcp_output/debug/' + 'call_list_queue'

### Get terminal software in system
terminal_soft = commands.getoutput('echo $TERM')

''' -------------------- Global Functions -------------------------- '''
### Adding phone number to incoming call list
def incoming_call_list(number):
	f = open (incoming_call_log,'a+')
	if (number+'\n') not in f.readlines():
		f.write(number+'\n')
	f.flush()
	f.close()

### Getting the first phone number from the incoming call list queue
def get_number():
	f = open (incoming_call_log,'r')
	number = f.readline().replace('\n','')
	f.close()
	return number

### Removing the phone number from call list queue
def update_call_list(number):
	f = open (incoming_call_log,'r+w')
	call_list = f.readlines()
	#print call_list
	call_list.remove(number+'\n')
	f.truncate(0)
	f.write(''.join(call_list))
	f.flush()
	f.close()


''' -------------------- The GSM class --------------------------- '''
class gsm(object):
	def __init__(self,args=''):

		### if debug mode, open terminal and display commands sent
		if args == 'debug':
			self.serpid = subprocess.Popen([terminal_soft, '-e', 'python', projectpath+'/serial_port.py'])
		else:
			self.serpid = subprocess.Popen(['python', projectpath+'/serial_port.py'])
		
		time.sleep(1)
		
		### Create a serial port object to access buffer files
		self.usb = serial_port.port()

		### Initialize state to "Call Disconnect State"
		self.call_state = '6' 
		

	def __del__(self):

		### While object being deleted, disconnect call and kill serial port
		###  sniffer process
		self.disconnect_call()
		self.serpid.kill()

	''' Read from input buffer and remove newline and carriage returns '''
	def readusb(self):
		return self.usb.readline().replace('\n','').replace('\r','')

	''' Check for OK/ERROR from GSM modem '''
	def isOK(self):
		while True:
			try:
				line = self.readline()		
				if line:
					if 'OK' in line: return True
					elif 'ERROR' in line: return False
			except Exception as error:
				print 'Runtime error is: ', error
				return False

	''' ATE Set Command Echo Mode '''
	def command_echo(self, state): 
		if state == 'OFF':
			self.usb.write('ATE0\n')
		elif state == 'ON':
			self.usb.write('ATE1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	''' AT+CFUN Set Phone Functionality '''
	def phone_functionality(self, state):
		if state == 'OFF': self.usb.write('at+cfun=0\n')
		elif state == 'ON': self.usb.write('at+cfun=1\n')
		elif state == 'RESTART': 
			self.usb.write('at+cfun=1,1\n')
			
			### On restart, wait for call ready
			while not 'Call Ready' in self.readline(): pass

			### Disable command echo
			self.command_echo('OFF')

			return True
		else: raise ValueError

		if self.isOK():	return True
		else: return False
	
	''' AT+CCALR Call Ready Query '''
	def call_ready(self):
		temp = False
		self.usb.write('at+ccalr?\n')
		line = self.readline()
		while not 'OK' in line:
			if '+CCALR:' in line:
				temp = bool(int(line.split(':')[1].replace(' ','')))
			line = self.readline()
		#print 'Call Ready: ', temp
		return temp
				
	''' 
		AT+CLCC List Current Calls of GSM modem - Autoreport on change in call
		status 
	'''
	def current_calls_report(self, state):
		if state == 'OFF':
			self.usb.write('AT+CLCC=0\n')
		elif state == 'ON':
			self.usb.write('AT+CLCC=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	''' AT+CLCC List Current Calls of GSM modem - To check for active calls '''
	def check_current_calls(self):
		temp = False		
		self.usb.write('AT+CLCC\n')
		line = self.readline()
		while not (('OK' in line) or ('ERROR' in line)):
			if '+CLCC:' in line: temp = True
			line = self.readline()
		return temp
		
	''' 
		Parse the auto report from AT+CLCC when call state changes 
		+CLCC: <id>,<dir>,<stat>,<mode>,<mpty>,"<number>",<type>,"<alphaID>"
		0. <id>			- call ID number
		1. <dir>		- 0 Mobile originated (MO) call
						  1 Mobile terminated (MT) call
		2. <stat>		- State of the call:
						  0 Active
						  1 Held
						  2 Dialing (MO call)
						  3 Alerting (MO call)
						  4 Incoming (MT call)
						  5 Waiting (MT call)
						  6 Disconnect
		3. <mode>		- Bearer/tele service:
						  0 Voice
						  1 Data
						  2 Fax
		4. <mpty>		- 0 Call is not one of multiparty (conference) call
						  1 Call is one of multiparty (conference) call 
		5. "<number>"	- Phone number in string type 
						  (should be included in quotation marks)
		6. <type>		- Type of address
		7. "<alphaID>"	- Name associated to phone number, in the phonebook
	'''
	def parse_current_calls(self, line):
		line = line.split(':')[1]
		line = line.split(',')
		#self.call_id = line[0]
		self.call_direction = line[1]
		self.call_state = line[2]
		self.call_number = line[5].replace('"','')		

	'''
		Send command AT to GSM modem and wait 3s for reply
	'''	
	def modem_connect(self):
		def gsm_connect_wait(signum, frame):
			raise Exception	

		signal.signal(signal.SIGALRM, gsm_connect_wait)

		signal.alarm(3)
		try:
			temp = ''
			self.usb.write('at\n')
			temp = self.readusb()
			while not temp: temp = self.readusb()
		except: 
			print 'Please connect GSM modem'
			return False
		signal.alarm(0)
		return True

	''' 
		Method to read the input buffer file
		While reading the buffer file it checks for
		01. Any calls and their status
		02. +CPIN: NOT READY - This usually indicates bad network
			Restart phone functionality when encountered. 
		03. +CFUN: 1 - indicates modem  restarted. Disable command echo
	'''
	def readline(self):
		line = self.readusb()
		if line: 
			if '+CLCC:' in line: 
				self.parse_current_calls(line)
				if self.call_direction == '1':
					if not self.call_state == '6':
						incoming_call_list(self.call_number)	
				if self.call_direction == '0':
					if self.call_state == '6': raise Exception ("Call Terminated")
			elif '+CPIN: NOT READY' in line: 
				print 'Modem restart: ', self.phone_functionality('RESTART')
				raise Exception("SIM Card Not Inserted Properly")
			elif '+CFUN: 1' in line: 
				self.command_echo('OFF')
				#raise Exception("Call Terminated, modem restarted")
			return line	
		return ''

	'''
		ATD Mobile Originated Call to Dial A Number
		Also monitor status of the dialed call
	'''
	def dial_number(self,number):
		if self.check_current_calls(): return 'Busy'
		else:
			self.usb.write('ATD'+number+';\n')
			if self.isOK():
				try: 
					line = self.readline()
					while not (self.call_direction == '0' and self.call_state == '0'): 
						line = self.readline()
					return 'Call Established'
				except Exception as error: 
					print 'Error: ', error
					return 'Call Not Answered'
			return 'Dialing Failed'

	''' 
		AT+DDET DTMF Detection Control 
		with default 1000ms interval for two same keypress 
	'''
	def dtmf_detection(self, state, interval = '1000'):
		if state == 'OFF':
			self.usb.write('AT+DDET=0\n')
		elif state == 'ON':
			self.usb.write('AT+DDET=1,'+interval+'\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	''' AT+CLIP Calling Line Identification Presentation '''
	def clip(self, state):
		if state == 'OFF':
			self.usb.write('AT+CLIP=0\n')
		elif state == 'ON':
			self.usb.write('AT+CLIP=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	''' 
		AT+CCWA Call Waiting Control
		<n>		- 0 Disable alert on incoming call wait
				  1 Enable alert on incoming call wait
		<mode> 	- 0 Disable
				- 1 Enable
	'''
	def call_wait_control(self, state, report='0'):
		if state == 'OFF':
			self.usb.write('AT+CCWA='+report+',0\n')
		elif state == 'ON':
			self.usb.write('AT+CCWA='+report+',1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False
	
	''' ATH Disconnect Existing Connection '''
	def disconnect_call(self):
		self.usb.write('ATH\n')
		if self.isOK(): return True				
		else: return False

	''' AT+MORING Show State of Mobile Originated Call '''
	def outgoing_call_status(self, state):
		if state == 'OFF':
			self.usb.write('AT+MORING=0\n')
		elif state == 'ON':
			self.usb.write('AT+MORING=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	''' To clear stray DTMF presses '''
	def clear_dtmf(self):
		i = 0
		while i<5:
			x=self.readline()
			print 'Things to Clear', x
			if not x: i += 1
			else: i = 0

	''' Parse response from modem and obtain the DTMF value '''
	def read_dtmf(self):
		line = self.readline()
		if '+DTMF:' in line:
			self.clear_dtmf()		#to ignore multiple key press
			return line.split(':')[1].replace(' ','')
		return ''

	

if __name__ == '__main__':

	mygsm = gsm()
	while not mygsm.modem_connect(): time.sleep(3)
	#if not mygsm.call_ready(): mygsm.phone_functionality('RESTART')
	print 'Echo OFF: ', mygsm.command_echo('OFF')
	#print 'Phone ON: ', mygsm.phone_functionality('ON')

	print 'Alert on change in call status: ', mygsm.current_calls_report('ON')
	raw_input()
	
