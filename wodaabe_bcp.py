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
expiry_action = []

call_log = 0

mygsm = pyGSM.gsm()

projectpath =  os.path.split(os.path.realpath(__file__))[0]
audiopath = projectpath + "/audios/"


def timeout_handler(signum, frame):
	raise Exception
	
def prepare_ivr_flow():

	global audio_file
	global level
	global valid_input
	global action
	global timeout
	global repeat
	global expiry_action
	global calllog_seek
	
	f = open('wodaabe_bcp_skeleton.csv','r')
	flow = f.readlines()
	f.close()

	flow = flow[:-1]
	flow = [w.replace('\n', '').replace('"','').replace('\r','') for w in flow]

	level = flow[0].split(',')[1:]
	level = [int(i) if i else 0 for i in level]
	#print level	

	audio_file = flow[1].split(',')[1:]
	#print audio_file

	valid_input = flow[2].split(',')[1:]
	print valid_input

	action = flow[3].split(',')[1:]
	print action

	timeout = flow[4].split(',')[1:]
	timeout = [int(i) if i else 0 for i in timeout]
	#print timeout

	repeat = flow[5].split(',')[1:]
	repeat = [int(i) if i else 0 for i in repeat]
	#print repeat

	expiry_action = flow[6].split(',')[1:]
	expiry_action = [int(i) if i else 0 for i in expiry_action]
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
	return []

def fetch_valid_input(levl):
	if len(valid_input[levl]) > 1:
		return valid_input[levl].split(';')
	else:
		return valid_input[levl]

def create_record(record):
	line = ','.join(record) + '\n'
	with open('call_log.csv','r') as f:
		log = f.readlines()
		print log
		log.append(line)
		print log
		log = ''.join(log)
	with open('call_log.csv','w') as f:
		f.truncate(0)
		f.write(log)
		f.flush()
		print log

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

def zero_back(zero_count):
	pid = commands.getoutput('ps -a | grep aplay')
	while pid:
		if zero_count < 1:
			dtmf = raw_input()
			if dtmf == '0':
				os.system("killall aplay")					
				return True			
		pid = commands.getoutput('ps -a | grep aplay')	
	return False
		
def execute_ivr(record,levl):
	ivr_stop = 0	
	repeat_cnt = 0
	zero_flag = False
	zero_count = 0
	
	dtmf = mygsm.get_DTMF()

	os.system("aplay "+audiopath+audio_file[levl]+".wav ")
	if valid_input[levl]:
			try:
				dtmf = ''				
				signal.alarm(timeout[levl])				
				while not dtmf: dtmf = mygsm.get_DTMF()
			except Exception:
				os.system("aplay "+audiopath+"provideinput.wav")
				dtmf = 't'
			signal.alarm(0)
			print 'DTMF is: ', dtmf
			if dtmf and 't' not in dtmf:
				levl += 1
			'''try:
				act = fetch_valid_input(levl).index(dtmf)
				record.append(dtmf)
				update_record(record)	
				levl = action[levl]
				actions = action[levl].split(';')
				if dtmf == '1':
					inputs = valid_input[levl].split(';')
			except:
				if dtmf:
					os.system("aplay "+audiopath+"invalidinput.wav")
				repeat_cnt += 1			
				if repeat_cnt > 2:
					print "Maximum number of failed attempts reached"
					ivr_stop = 1
					try:
						levl = action[int(dtmf)]
					except: pass
				else:
					levl = int(action[levl])
			'''
	else:
			record.append('-')
			update_record(record)
			levl += 1
			ivr_stop = 1
			
def addto_call_list(number):
	f = open ('call_list_queue','a+')
	if (number+'\n') not in f.readlines():
		f.write(number+'\n')
	f.close()

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
		if mygsm.isRinging():
			call_log += 1			
			phone_number = mygsm.readcallerID()			
			print 'Call from ', phone_number 
			addto_call_list(phone_number)
			while mygsm.isRinging(): pass
		if call_log:
			phone_number = get_number()
			if phone_number:
				status = mygsm.callnumber(phone_number)
				print status
				if not 'Failed' in status:
					status = mygsm.outgoing_call_status()
					if 'Terminated' not in status:
						if not status:
							pass
						elif 'Ringing' in status: print status
						elif status == 'Hello!':
							print status
							update_call_list(phone_number)
							call_log -= 1

							os.system("aplay "+audiopath+audio_file[0]+".wav")
							levl = 1

							record = fetch_record(phone_number)

							if record:
								print 'User is in Level: ', len(record) - 1
		
							else:
								print 'Creating new record'
								record.insert(0,phone_number)
								record.append('-')
								create_record(record)
								levl += 1

							execute_ivr(record,levl)
