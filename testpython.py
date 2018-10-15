
# using queues to interact between two threads
import threading
import time


list = [1, 2]


def main():
    global list

    thread = threading.Thread(target=func1)
    thread.start()

    while True:
        time.sleep(1)
        print(list)


def func1():

    global list

    i = 2
    while True:
        time.sleep(1)
        list.append(i)
        i = i + 1



main()