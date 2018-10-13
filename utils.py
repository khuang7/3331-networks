import packet
import pickle

# a list of utility functions that both sides use basically

# UTILS
def serialize_packet(packet):
    return pickle.dumps(packet)

def deserialize_packet(packet):
    return pickle.loads(packet)