import serial_port
import os
import signal
import time
import commands

projectpath =  os.path.split(os.path.realpath(__file__))[0]
incoming_call_log = projectpath + '/bcp_output/debug/' + 'call_list_queue'

terminal_soft = commands.getoutput('echo $TERM')

def incoming_call_list(number):
	f = open (incoming_call_log,'a+')
	if (number+'\n') not in f.readlines():
		f.write(number+'\n')
	f.flush()
	f.close()

def get_number():
	f = open (incoming_call_log,'r')
	number = f.readline().replace('\n','')
	f.close()
	return number

def update_call_list(number):
	f = open (incoming_call_log,'r+w')
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
		os.system(terminal_soft + " -e 'bash -c \"python /home/sanketh/Documents/janastu/ivr/pyGSM/serial_port.py; bash\" ' &")
		time.sleep(1)
		self.usb = serial_port.port()

		self.call_state = '6' # Call Disconnect State
		

	def __del__(self):
		self.disconnect_call()
		os.system("killall xterm")

	def readusb(self):
		return self.usb.readline().replace('\n','').replace('\r','')

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

	def command_echo(self, state): 
		if state == 'OFF':
			self.usb.write('ATE0\n')
		elif state == 'ON':
			self.usb.write('ATE1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	def phone_functionality(self, state):
		if state == 'OFF': self.usb.write('AT+CFUN=0\n')
		elif state == 'ON': self.usb.write('AT+CFUN=1\n')
		elif state == 'RESTART': 
			self.usb.write('AT+CFUN=1,1\n')
			while not 'Call Ready' in self.readline(): pass
			self.command_echo('OFF')
			return True
		else: raise ValueError

		if self.isOK():	return True
		else: return False
	
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
				
	def current_calls_report(self, state):
		if state == 'OFF':
			self.usb.write('AT+CLCC=0\n')
		elif state == 'ON':
			self.usb.write('AT+CLCC=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	def check_current_calls(self):
		temp = False		
		self.usb.write('AT+CLCC\n')
		line = self.readline()
		while not (('OK' in line) or ('ERROR' in line)):
			if '+CLCC:' in line: temp = True
			line = self.readline()
		return temp
		
	def parse_current_calls(self, line):
		line = line.split(':')[1]
		line = line.split(',')
		#self.call_id = line[0]
		self.call_direction = line[1]
		self.call_state = line[2]
		self.call_number = line[5].replace('"','')		

					
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
			#elif '+CFUN: 1' in line: 
			#	raise Exception("Call Terminated, modem restarted")
			#print line
			return line	
		return ''

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

	def dtmf_detection(self, state, interval = '1000'):
		if state == 'OFF':
			self.usb.write('AT+DDET=0\n')
		elif state == 'ON':
			self.usb.write('AT+DDET=1,'+interval+'\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	def clip(self, state):
		if state == 'OFF':
			self.usb.write('AT+CLIP=0\n')
		elif state == 'ON':
			self.usb.write('AT+CLIP=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False

	def call_wait_control(self, state, report='0'):
		if state == 'OFF':
			self.usb.write('AT+CCWA='+report+',0\n')
		elif state == 'ON':
			self.usb.write('AT+CCWA='+report+',1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False
	
	def disconnect_call(self):
		self.usb.write('ATH\n')
		if self.isOK(): return True				
		else: return False

	def outgoing_call_status(self, state):
		if state == 'OFF':
			self.usb.write('AT+MORING=0\n')
		elif state == 'ON':
			self.usb.write('AT+MORING=1\n')
		else: raise ValueError

		if self.isOK(): return True				
		else: return False


	def clear_dtmf(self):
		i = 0
		while i<5:
			x=self.readline()
			print 'Things to Clear', x
			if not x: i += 1
			else: i = 0


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
	
	
'''
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
'''		
