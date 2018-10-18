
# using queues to interact between two threads
import sys
import random
import time

start_time = None


def func1():
	global start_time
	print (start_time)
	timestamp = time.time()

	print (start_time-timestamp)



def main():
	global start_time
	start_time = time.time()
	i = 0
	while i < 1000:
		i = i + 1

	func1()
main()


'''
The arguments on the sample log file
MSS=150 bytes, MWS=600, gamma=4, pDrop=0.1 and seed=100.


python sender.py receiver_host_ip receiver_port file.pdf MWS MSS gamma
pDrop pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed

python3 multi_sender.py 127.0.0.1 5000 test0.pdf 600 150 4 0.1 0 0 0 0 0 0 100

 try out updatewindow() inside the resent packets thign


'''
