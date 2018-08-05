import pyGSM
import os
import signal
import commands

audio_file = []
level = []
valid_input = []
action = []
timeout = []	
repeat = []
timeout_action = []

call_log = 0

mygsm = pyGSM.gsm()

projectpath =  os.path.split(os.path.realpath(__file__))[0]
audiopath = projectpath + "/audios/"


def timeout_handler(signum, frame):
	raise Exception('Timeout')
	
def prepare_ivr_flow():

	global audio_file
	global level
	global valid_input
	global action
	global timeout
	global timeout_action
	global expiry_action
	global calllog_seek
	
	f = open('wodaabe_bcp_skeleton.csv','r')
	flow = f.readlines()
	f.close()

	flow = flow[:-1]
	flow = [w.replace('\n', '').replace('"','').replace('\r','') for w in flow]

	level = flow[0].split(',')[1:]
	#level = [int(i) if i else 0 for i in level]
	#print level	

	audio_file = flow[1].split(',')[1:]
	#print audio_file

	valid_input = flow[2].split(',')[1:]
	#print valid_input

	action = flow[3].split(',')[1:]
	#print action

	timeout = flow[4].split(',')[1:]
	timeout = [int(i) if i else 0 for i in timeout]
	#print timeout

	timeout_action = flow[5].split(',')[1:]
	timeout_action = [int(i) if i else '' for i in timeout_action]
	#print timeout_action

	#expiry_action = flow[6].split(',')[1:]
	#expiry_action = [int(i) if i else 0 for i in expiry_action]
	#print expiry_action

def fetch_record(number):

	with open('call_log.csv','r') as f:
		log = f.readlines()
	
	for line in log[2:]:
		record = line.split(',')

		if number == record[0]:
			log.remove(line)
			log.append(line)
			log = ''.join(log)
			with open('call_log.csv','w') as f:
				f.truncate(0)
				f.write(log)
				f.flush()
			record = [w.replace('\n', '') for w in record]
			return record
	return ['']*(len(level)+1)

def fetch_valid_input(levl):
	if len(valid_input[levl]) > 1:
		return valid_input[levl].split(';')
	else:
		return valid_input[levl]

def fetch_action(levl):
	if len(action[levl]) > 1:
		return action[levl].split(';')
	else:
		return action[levl]

def create_record(record):
	line = ','.join(record) + '\n'
	with open('call_log.csv','r') as f:
		log = f.readlines()
		log.append(line)
		log = ''.join(log)
	with open('call_log.csv','w') as f:
		f.truncate(0)
		f.write(log)
		f.flush()
		#print log

def update_record(record):
	line = ','.join(record) + '\n'
	with open('call_log.csv','r') as f:
		log = f.readlines()
		log[-1] = line
		log = ''.join(log)
	with open('call_log.csv','w') as f:
		f.truncate(0)
		f.write(log)
		f.flush()

def fetch_dtmf(levl):
	
	if not valid_input[levl]:
		return '-'			
	try:
		dtmf = ''			
		signal.alarm(timeout[levl])				
		while not dtmf: dtmf = mygsm.readDTMF()#raw_input('Enter choice: ')
	except Exception as error:
		print 'Error is ', error
		if 'Timeout' in error:	dtmf = 't' 
		else: dtmf = 'exit'
		signal.alarm(0)
		return dtmf
	signal.alarm(0)
	print 'dtmf @ fetch is', dtmf
	try:
		print 'Level is ', levl
		print 'Valid inputrs are: ', fetch_valid_input(levl)
		fetch_valid_input(levl).index(dtmf)
	except: dtmf = 'invalid'
	return dtmf


def execute_ivr(record, from_level):
	timeout_cnt = 0
	invalid_cnt = 0
	zero_cnt = 0
	now_level = 0
	
	while True:
		if now_level == 40: 
			print mygsm.end_call()
			return
		'''
		try:
			mygsm.clearDTMF()
		except:
			print "Call Terminated"
			break
		'''

		os.system("aplay "+audiopath+audio_file[now_level]+".wav ")		
		dtmf = fetch_dtmf(now_level)
		print 'DTMF is ', dtmf
		if dtmf == 'exit': break
		elif dtmf == 't': 
			if not timeout_action[now_level] == now_level: 
				next_level = timeout_action[now_level]
				print 'Nexxt: ', next_level
				print 'Now: ', now_level
				now_level = next_level
				continue
			else:
				if timeout_cnt < 1:
					os.system("aplay "+audiopath+"provideinput.wav")
					timeout_cnt += 1
					continue
				else:
					now_level = 6
					continue
		elif dtmf == 'invalid':
			if invalid_cnt < 1: 
				os.system("aplay "+audiopath+"invalidinput.wav")
				invalid_cnt += 1
				continue
			else: 
				now_level = 6
				continue
		else:
			timeout_cnt = 0
			invalid_cnt = 0
			if dtmf == '-': i = 0
			else: i = fetch_valid_input(now_level).index(dtmf)
			print 'i is ', i
			print action[now_level]
			next_level = fetch_action(now_level)[i]
			print 'Next level is ', next_level
			try: next_level = int(next_level)
			except: 
				if next_level == 'A':
					if not from_level: next_level = 2
					else: next_level = 1
				elif next_level == 'B':
					next_level = from_level
				elif next_level == 'C':
					if record[14] == '1': next_level = 15
					else: next_level = 21 
				elif next_level == 'D':
					if from_level: next_level = from_level
					else: next_level = 7
			
		if not dtmf == '-' and not (dtmf == '0' and now_level >= 7):
			record[now_level+1] = dtmf
			update_record(record)	
			if now_level == 26 and dtmf == '3':
				with open('Caller Clan Not Listed.txt','a+') as f:
					f.write(phone_number)
		
		if next_level < now_level: zero_cnt += 1		
		else: zero_cnt = 0
		if zero_cnt > 1: now_level = 6
		else: now_level = next_level


def get_number():
	f = open ('call_list_queue','r')
	number = f.readline().replace('\n','')
	f.close()
	return number

def update_call_list(number):
	f = open ('call_list_queue','r+w')
	call_list = f.readlines()
	print call_list
	call_list.remove(number+'\n')
	print call_list
	f.truncate(0)
	f.write(''.join(call_list))
	f.close()


if __name__ == '__main__':

	print mygsm.echo_off()
	print mygsm.dtmf_on()
	print mygsm.outgoing_call_status_on()

	prepare_ivr_flow()
	signal.signal(signal.SIGALRM, timeout_handler)

	while True:
		try:
			mygsm.readline()
		except: pass
	
		phone_number = get_number()
		if phone_number and not (mygsm.on_hook or mygsm.incoming_call): 		
			record = fetch_record(phone_number)
			if record[0]:
				from_level = len(record) - 1
				while not record[from_level]: from_level -= 1
				print 'From level', from_level
				if from_level < 7:	from_level = 0
				elif from_level == 34: from_level -= 1
				elif from_level == 39: 
					update_call_list(phone_number)
					continue
			else:
				from_level = 0
				record[0] = phone_number
				create_record(record)
		
			status = mygsm.callnumber(phone_number)
			if 'Established' in status:
				print status
				update_call_list(phone_number)
				execute_ivr(record,from_level)

			elif 'Not Answered' in status:
				print status
				update_call_list(phone_number)
				

	#while True:
	#	phone_number = raw_input('Enter number: ')
	#	execute_ivr(phone_number)

#def zero_back(zero_count):
#	pid = commands.getoutput('ps -a | grep aplay')
#	while pid:
#		if zero_count < 1:
#			dtmf = raw_input()
#			if dtmf == '0':
#				os.system("killall aplay")					
#				return True			
#		pid = commands.getoutput('ps -a | grep aplay')	
#	return False
	
