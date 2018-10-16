
# using queues to interact between two threads
import threading
import time


dict = {
        1 : 150,
        151 : 150,
        451 : 150
    }


def main():
    
    expected_num = 151
    list_of_keys = list(dict.keys())

    index = list_of_keys.index(expected_num)
    sliced = list_of_keys[index:]

    length = len(sliced)
    counter = 0
    prev = sliced.pop(0)
    curr = prev

    # it was already the last thing in the list
    if (not sliced):
        print (prev + 150)
        exit(0)

    for i in sliced:
        counter = counter + 1
        # if its the last element
        curr = i

        print("compares", prev, curr)
        if (curr == prev + 150):
            prev = curr
            continue
        else: 
            print(curr + 150)
            exit(0)

        if (counter == length - 1 ):
            print(curr + 150)
            exit(0)

main()