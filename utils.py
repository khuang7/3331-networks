
from globals import *
# functions that exist in both sender and receiver


import pickle
from packet import *
import time

# serelize right before sending any packet
def serialize_packet(packet):
    return pickle.dumps(packet)

# desereliaze as soon as we received a packet
def deserialize_packet(packet):
    return pickle.loads(packet)



