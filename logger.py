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
        return list(dictionary.values())[:6]


class overall_sender_logger:

    def __init__(self):
            self.dict = {
                "size_of_file": 0,
                "segments_transmitted": 0,
                "segments_PLD": 0,
                "segments_dropped": 0,
                "segments_corrupted": 0,
                "segments_reordered": 0,
                "segments_duplicated": 0,
                "segments_delayed": 0,
                "number_retransmissions": 0,
                "fast_retransmissions": 0,
                "dup_acks": 0
            }

    def update_field(self, dictionary_key, num):
        self.dict[dictionary_key] = num

    def increment_field(self, dictionary_key):
        self.dict[dictionary_key] += 1

    def get_dict(self):
        return self.dict


class overall_receiver_logger:
    def __init__(self):
            self.dict = {
                "size_of_file": 0,
                "total_segments": 0,
                "data_segments": 0,
                "bit_errors": 0,
                "duplicates": 0,
                "duplicate_acks_sent": 0
            }

    def update_field(self, dictionary_key, num):
        self.dict[dictionary_key] = num

    def increment_field(self, dictionary_key):
        self.dict[dictionary_key] += 1

    def get_dict(self):
        return self.dict
