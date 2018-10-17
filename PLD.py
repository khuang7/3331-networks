import random

# possible outcomes
DROP_PACKET = 1
DUPLICATE = 2
CORRUPT = 3
OUT_OF_ORDER = 4
DELAY = 5
NOTHING = 6


def PLD_gen(list):
    num = float(random.random())
    print ("comparing ", num , list[0])

    if (num < list[0]):
        return DROP_PACKET
    elif(num < list[1]):
        return DUPLICATE
    elif (num < list[2]):
        return CORRUPT
    elif (num < list[3]):
        return OUT_OF_ORDER
    elif (num < list[5]):
        return DELAY  # determine delay value  in main
    else:
        return NOTHING

