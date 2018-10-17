
# using queues to interact between two threads
import sys
import random
import time


def test_rand():

    rand_gen = random.random()  
    return rand_gen


def main():
    random.seed(3)
    while True:
        time.sleep(0.5)
        print(test_rand())
main()





'''
The arguments on the sample log file
MSS=150 bytes, MWS=600, gamma=4, pDrop=0.1 and seed=100.


python sender.py receiver_host_ip receiver_port file.pdf MWS MSS gamma
pDrop pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed

python3 multi_sender.py 127.0.0.1 5000 test0.pdf 600 150 4 0.1 0 0 0 0 0 0 100

 try out updatewindow() inside the resent packets thign


'''
