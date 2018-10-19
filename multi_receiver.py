import socket
import threading
from packet import packet
import sys
import time
from utils import serialize_packet, deserialize_packet
from logger import *

# argument check
if len(sys.argv) != 3:
    print("Usage Python receiver.py, receiver_port, file_r.pdf")
    sys.exit(1)

# initialize variables
rcv_host_ip = "127.0.0.1"
rcv_port = int(sys.argv[1])
hostport = (rcv_host_ip, rcv_port)
filename = sys.argv[2]

# GLOBAL VARIABLES
receiver_buffer = {}
CONNECTION_STATE = "CLOSED"
expected_seq_num = 0
receiver_buffer = {}
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_socket.bind(hostport)

# Logger
log = []
overall_logger = overall_receiver_logger()
overall_timer = None


def main():
    global overall_timer 
    global overall_logger
    overall_timer = time.time()
    
    while True:
        data, address = receiver_socket.recvfrom(4000)
        add_to_log(data, "rcv")
        overall_logger.increment_field("total_segments")
        deserialize = deserialize_packet(data)

        if deserialize.get_packet_type() != "FIN":
            thread = threading.Thread(target=handle_connection, args=(deserialize, address))
            thread.start()
        else:  # FIN has been received
            # maybe i should thread this as well
            finish_connection(deserialize, address)
            break


# this function gets called every time a packet arrives from sender
def handle_connection(deserialize, address):
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pkt = process_packet(deserialize)
    if pkt is not None:
        pkt = serialize_packet(pkt)
        newSocket.sendto(pkt, address)
        add_to_log(pkt, "snd")


# we have to send two packets in a row
# packet given here is already deserialized
# sort of hard coded
def finish_connection(deserialize, address):
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq_num = deserialize.get_seq_num()

    ACK = packet("ACK", 1, seq_num + 1)
    FIN = packet("FIN", 1, seq_num + 1)

    serialize_ack = serialize_packet(ACK)
    newSocket.sendto(serialize_ack, address)
    add_to_log(serialize_ack, "snd")
    time.sleep(2)

    serialize_fin = serialize_packet(FIN)
    newSocket.sendto(serialize_fin, address)
    add_to_log(serialize_fin, "snd")

    while True:
        data, address = receiver_socket.recvfrom(4000)
        add_to_log(data, "rcv")
        deserialize = deserialize_packet(data)
        convert_buffer_to_file()
        break

    create_log()
    print("FINISHED")
    sys.exit(0)


# creates a packet 
def process_packet(pkt):
    global expected_seq_num
    global CONNECTION_STATE
    global receiver_buffer

    seq_num = pkt.get_seq_num()
    pkt_type = pkt.get_packet_type()
    # initial packet sent

    print("RECEIVED THIS PACKET")
    pkt.simple_print()

    # HANDSHAKE
    if pkt_type == "SYN":
        # create a SYNACK packet to send back
        new_packet = packet("SYNACK", 0, seq_num + 1)
        return new_packet
    # this packet completes the handshake (return nothing?)
    elif pkt_type == "ACK":
        # complete the handshake
        CONNECTION_STATE = "OPEN"
        expected_seq_num = 1
        return None
    # packet should be a data packet
    else:
        if (pkt.get_corrupt() == 1):
            overall_logger.increment_field("bit_errors")
            print("corrupt packet send nothing back")
            return None
        elif (pkt.seq_num in receiver_buffer.keys()):
            return None  # dont return the packet since we have it already
        else:

            add_to_buffer(pkt)
            # the state of the buffer after every add
            print("added packet, buffer is now", receiver_buffer.keys())

            update_expected_seq_num(pkt)
            print ("new expected seq num is", expected_seq_num)
            new_packet = packet("ACK", 1, expected_seq_num)
            new_packet.simple_print()

            return new_packet



# globally updates the ack num (what it expects next in the sequence)
# Accumulative Acknowledgement
def update_expected_seq_num(pkt):
    global receiver_buffer
    global expected_seq_num

    list_of_keys = sorted(receiver_buffer.keys())
    print("determining expected seq num from here", list_of_keys)
    prev = list_of_keys.pop(0)

    start = 1
    # edge case beginning
    if (prev != 1):
        expected_seq_num = start

    # after popping the list is empty so it has to be just the next one
    elif (not list_of_keys):
        expected_seq_num = start + packet_length(start)  # make sure i use payload size here

    # cycle through the whole list till we reach a point
    else:
        for i in list_of_keys:
            curr = i
            if (prev + packet_length(prev) == curr):
                prev = curr
                continue
            else: 
                expected_seq_num = prev + packet_length(curr)
                return
        # if we get out of this loop
        expected_seq_num = curr + packet_length(curr)


# helper for finding expected seq num
def packet_length(seq_num):
    global receiver_buffer
    return len(receiver_buffer.get(seq_num))


def add_to_buffer(pkt):
    global receiver_buffer
    list_of_keys = receiver_buffer.keys()
    if pkt.seq_num not in list_of_keys:
        print("adding into buffer", pkt.seq_num)
        receiver_buffer[pkt.seq_num] = pkt.payload
        # instead of sorting it here, we sort everytime we check the list

# writes the file from the buffer
def convert_buffer_to_file():
    global filename
    global receiver_buffer

    list_of_keys = list(receiver_buffer.keys())
    sort_list = sorted(list_of_keys)

    f = open(filename, "wb")

    for i in sort_list:
        f.write(receiver_buffer.get(i))

# always give thsi function a SERIALIZED PACKET
def add_to_log(packet, direction):
    global overall_timer
    global log

    pkt = deserialize_packet(packet)
    pkt_type = pkt.get_packet_type()
    seq_num = pkt.get_seq_num()
    ack_num = pkt.get_ack_num()

    # time calculation
    if not overall_timer:
        total_time = 0
    else:

        timestamp = time.time()
        total_time = timestamp - overall_timer

    if pkt.get_payload() is None:
        data_size = 0
    else:
        data_size = pkt.payload_size()
    new = logger(direction, total_time, pkt_type, seq_num, data_size, ack_num)
    log.append(new)


def create_log():
    global log
    global receiver_buffer
    global overall_logger

    overall_logger.update_field("size_of_file", calculate_size())
    overall_logger.update_field("data_segments", len(receiver_buffer.keys()))

    overall_logger_dict = overall_logger.get_dict()
    with open('receiver_log.txt', 'w') as f:
        for logs in log:
            f.write(' '.join(str(i) for i in logs.list_attr()))
            f.write("\n")
            #f.write("%s\n" % logs.list_attr())

        f.write("\n\n============SUMMARY============\n")
        for itr in overall_logger_dict.keys():
            f.write("%s: %d\n" % (itr, overall_logger_dict[itr]))
        f.write("\n===========================================")
    # final updates before adding


def calculate_size():
    global receiver_buffer
    i = 0
    for keys in list(receiver_buffer.keys()):
        i = i + len(receiver_buffer.get(keys))
    return i

main()
