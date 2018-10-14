
# using queues to interact between two threads
import threading
import time
from queue import *

def func1(num, q):

    while num < 100000000:
        num = num**2
        time.sleep(1)
        print("putting", num)
        q.put(num)

def func2(num, q):

    while num < 100000000:
        num = q.get()
        print (num)

num = 2
q = Queue()
thread1 = threading.Thread(target=func1,args=(num,q))
thread2 = threading.Thread(target=func2,args=(num,q))
print ("setup")


thread1.start()
thread2.start()


