import serial
import os

def read (usb):
	return usb.readline().replace('\r\n','')

no_carrier_status = 0

f = open ('call_list_queue','r')
call_log = len(f.readline())
f.close()

usb = serial.Serial('/dev/ttyUSB0',timeout=0.1)

usb.write(b'ATE0\n')
read(usb)
print 'Echo OFF: ' + read(usb)
usb.write(b'AT+DDET=1\n')
print 'DTMF Activation Status: ' + read(usb)
usb.write(b'AT+MORING=1\n')
print 'Outgoing Call Pickup Identification Status: ' + read(usb)

while True:

	line = read(usb)
	if line:
		if ('RING' in line) and no_carrier_status==0:
			print line
			while 'CLIP' not in line:
				line = read(usb)
			number = line.split(',')[0].split('"')[1]
			print 'Caller id is: ' + number
 			f = open ('call_list_queue','a+')
			if (number+'\n') not in f.readlines():
				f.write(number+'\n')
			f.close()	
			no_carrier_status = 1
			call_log += 1
		elif ('NO CARRIER' in line):
			print line
			no_carrier_status = 0
	
	if call_log and not no_carrier_status:	
		f = open ('call_list_queue','r')
		numbers = f.readlines()
		f.close()
		for n in numbers:
			print 'Calling: '+n
			usb.write('ATD'+(n.replace('\n',';\n')))
			line = read(usb)
			print line
			while ('NO CARRIER' not in line) and not no_carrier_status:
				if not line:
					pass
				elif 'MO RING' in line:
					print 'Ringing...'
				elif 'MO CONNECTED' in line:
					print 'Answered'
					numbers.remove(n)
					f = open ('call_list_queue','w')
					f.write(''.join(numbers))
					f.close()
					os.system("aplay level3.wav &")
				elif 'DTMF' in line:
					dtmf = line.split(':')[1]
					print 'Number Entered is: ' + dtmf
				elif 'CLIP' in line:
					number = line.split(',')[0].split('"')[1]
					print 'Caller Waiting: ' + number
 					f = open ('call_list_queue','a+')
					if (number+'\n') not in f.readlines():
						f.write(number+'\n')
					f.close()	
					no_carrier_status = 1
				elif ('NO CARRIER' in line) and no_carrier_status:
					print 'Wait call ended'					
					no_carrier_status = 0
				line = read(usb)
			print line
			
		call_log = 0
		
		

		
	
