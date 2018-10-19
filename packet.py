#COMP3331
# packet.py acts as the HEADER FILE

class packet:

    # instantiates a new packet, sort of like a constructor in java
    def __init__(self, packet_type, seq_num, ack_num):
        self.packet_type = packet_type
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload = None # initially its nothing
        self.checksum = 0# should be changed to actual checksum value

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

    def get_payload(self):
        return self.payload

    def print_packet_data(self):
        print(vars(self))

    def simple_print(self):
        print("%s (%s %s)" % (self.packet_type, self.seq_num, self.ack_num))

    def payload_size(self):
        return len(self.payload)

    def get_corrupt(self):
        return self.checksum

    def corrupt(self):
        self.checksum = 1 

    def uncorrupt(self):
        self.checksum = 0
