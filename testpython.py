
# using queues to interact between two threads
import threading
import time


dict = {
        1 : 150,
        151 : 150,
        301 : 150,
        451 : 150,
        601 : 150,
    }


def main():
    
    expected_num = 151
    list_of_keys = list(dict.keys())

    print(list_of_keys)

    index = list_of_keys.index(expected_num)
    sliced = list_of_keys[index:]

    length = len(sliced)
    counter = 0
    for i in sliced:
        



main()