import random

# possible outcomes
DROP_PACKET = 1
DUPLICATE = 2
CORRUPT = 3
OUT_OF_ORDER = 4
DELAY = 5
NOTHING = 6


def PLD(pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, seed):

    if (random(seed) < pDrop):
        return DROP_PACKET
    elif(random(seed) < pDuplicate):
        return DUPLICATE
    elif (random(seed) < pCorrupt):
        return CORRUPT
    elif (random(seed) < pOrder):
        return OUT_OF_ORDER
    elif (random(seed) < pDelay):
        return DELAY  # determine delay value  in main
    else:
        return NOTHING

# returns a random number between 0 and 1
def random(seed):
    random.seed(seed)
    return random.random(0, 1)