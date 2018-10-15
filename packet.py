#COMP3331
# packet.py acts as the HEADER FILE
import pickle

# consider using flags for this?
SYN = 0b0001
ACK = 0b0010
SYNACK = 0b0011
FIN = 0b0100
DATA = 0b1000


class packet:

    # instantiates a new packet, sort of like a constructor in java
    def __init__(self, packet_type, seq_num, ack_num):
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload = None # initially its nothing

    # getters and setters
    def set_seq_num(self, num):
        self.seq_num = num

    def set_ack_num(self, num):
        self.ack_num = num 

    def get_seq_num(self):
        return self.seq_num

    def get_ack_num(self):
        return self.ack_num

    def get_packet_type(self):
        return self.packet_type

    def add_payload(self, data):
        self.payload = data

    def print_packet_data(self):
        print(vars(self))
        #https://stackoverflow.com/questions/5969806/print-all-properties-of-a-python-class

    def simple_print(self):
        print("%s (%s %s)" % (self.packet_type, self.seq_num, self.ack_num))

    def payload_size(self):
        return len(self.payload)


    