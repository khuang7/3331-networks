import logging # probably wont be using this


class logger:
    def __init__(self, direction, time, type, seq_num, data_size, ack_num):
        self.direction = direction #snd/rcv
        self.time = time
        self.type = type # S, SA, A, D
        self.seq_num = seq_num
        self.data_size = data_size
        self.ack_num = ack_num

    def print_logger(self):
        print("ADDING TO LOG", vars(self))

    # returns a list of the attribute values
    def list_attr(self):
        dictionary = vars(self)
        return list(dictionary.values())