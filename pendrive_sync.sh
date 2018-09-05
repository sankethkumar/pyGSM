#!/bin/bash

### Command to get directory of this script
dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )

### Command to get the USB Storage mount point
x=$(lsblk | grep media | awk '{print $7}')

### Forever be looking for conection of USB Storage
###  When connected, sync 'bcp_output' folder
while :
do
	### Wait for connection of USB Storage
	while [ -z ${x} ] 
	do 
		sleep 1
		x=$(lsblk | grep media | awk '{print $7}')
	done
	
	y=$(date +%d%b%Y,%X:)
	echo $y 'USB Storage Connected'

	### Sync the desired folder
	sleep 5
	rsync -r $dir/bcp_output/ $x/bcp_output
	
	y=$(date +%d%b%Y,%X:)
	echo $y 'Sync Completed'

	### Wait for disconnection of USB Storage
	while [ ! -z ${x} ] 
	do 
		sleep 1
		x=$(lsblk | grep media | awk '{print $7}')
	done

	y=$(date +%d%b%Y,%X:)
	echo $y 'USB Storage Removed'	
done
