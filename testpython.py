
# using queues to interact between two threads
import threading
import time
from packet import packet
from logger import logger


def main():




    word = logger("snd", 0, "ACK", 1, 0, 1)
    word.print_logger()



main()