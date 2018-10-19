"""Receiver.py on Python3.6.3.

Kevin Huang (z3461590) 3331_ass1

Takes in packets from a receiver UDP socket and outputs a log and the pdf file
sent from sender.py

"""
import socket
import threading
from packet import packet
import sys
import time
from logger import logger, overall_receiver_logger
import pickle

""" Argument Checker"""
if len(sys.argv) != 3:
    print("Usage Python receiver.py, receiver_port, file_r.pdf")
    sys.exit(1)

"""Initialize Variables"""
rcv_host_ip = "127.0.0.1"
rcv_port = int(sys.argv[1])
hostport = (rcv_host_ip, rcv_port)
filename = sys.argv[2]

"""Global Variables"""
receiver_buffer = {}
CONNECTION_STATE = "CLOSED"
expected_seq_num = 0
receiver_buffer = {}
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_socket.bind(hostport)

"""Logger Variables"""
log = []
overall_logger = overall_receiver_logger()
overall_timer = None


def main():
    """Entry point into receiver thread.

    Continuially runs a while loops that takes in packets
    Once received a new thread to handle_connection() occurs
    """
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
        else:
            print("FILE FULLY SENT")
            finish_connection(deserialize, address)
            break


def handle_connection(deserialize, address):
    """Send a packet in response to a packet that has been given.

    The process of choosing a packet is dealt with via process_packet()
    """
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pkt = process_packet(deserialize)
    if pkt is not None:
        pkt = serialize_packet(pkt)
        new_socket.sendto(pkt, address)
        add_to_log(pkt, "snd")


def finish_connection(deserialize, address):
    """Finish the connection, this function is called when a FIN arrives.

    Sends a ACK and FIN packet and expects an ACK later on
    Once the ACK has arrived we create log and exit
    """
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    seq_num = deserialize.get_seq_num()

    ack = packet("ACK", 1, seq_num + 1)
    fin = packet("FIN", 1, seq_num + 1)

    serialize_ack = serialize_packet(ack)
    new_socket.sendto(serialize_ack, address)

    add_to_log(serialize_ack, "snd")
    time.sleep(2)

    serialize_fin = serialize_packet(fin)
    new_socket.sendto(serialize_fin, address)
    add_to_log(serialize_fin, "snd")

    while True:
        data, address = receiver_socket.recvfrom(4000)
        add_to_log(data, "rcv")
        deserialize = deserialize_packet(data)
        convert_buffer_to_file()
        break

    create_log()
    print("FINISHED TEARDOWN")
    sys.exit(0)


def process_packet(pkt):
    """Return the response packet based on sender packet (pkt).

    Return nothing if packet is corrupt or if already in buffer
    Otherwise we find the appropriate ack num and return a packet
    """
    global expected_seq_num
    global CONNECTION_STATE
    global receiver_buffer

    seq_num = pkt.get_seq_num()
    pkt_type = pkt.get_packet_type()
    if pkt_type == "SYN":
        new_packet = packet("SYNACK", 0, seq_num + 1)
        return new_packet
    elif pkt_type == "ACK":
        print("HANDSHAKE COMPLETE")
        CONNECTION_STATE = "OPEN"
        expected_seq_num = 1
        return None

    # all DATA packets go here
    else:
        if (pkt.get_corrupt() == 1):
            overall_logger.increment_field("bit_errors")
            return None
        elif (pkt.seq_num in receiver_buffer.keys()):
            return None
        else:
            add_to_buffer(pkt)
            # print("ADDED TO BUFFER", receiver_buffer.keys())
            update_expected_seq_num(pkt)
            # print ("CUMULATIIVE ACK =", expected_seq_num)
            new_packet = packet("ACK", 1, expected_seq_num)
            return new_packet


def update_expected_seq_num(pkt):
    """Return the ack_num via the logic of cumulative acknowledgement."""
    global receiver_buffer
    global expected_seq_num

    list_of_keys = sorted(receiver_buffer.keys())
    prev = list_of_keys.pop(0)
    start = 1

    if (prev != 1):
        expected_seq_num = start
    elif (not list_of_keys):
        expected_seq_num = start + packet_length(start)
    else:
        for i in list_of_keys:
            curr = i
            if (prev + packet_length(prev) == curr):
                prev = curr
                continue
            else:
                expected_seq_num = prev + packet_length(curr)
                return
        expected_seq_num = curr + packet_length(curr)


def packet_length(seq_num):
    """Return payload length of specific packet of seq_num."""
    global receiver_buffer
    return len(receiver_buffer.get(seq_num))


def add_to_buffer(pkt):
    """Add packet to global receiver buffer."""
    global receiver_buffer
    list_of_keys = receiver_buffer.keys()
    if pkt.seq_num not in list_of_keys:
        #print("ADDING INTO RECEIVER BUFFER", pkt.seq_num)
        receiver_buffer[pkt.seq_num] = pkt.payload


def serialize_packet(packet):
    """Serialize packet."""
    return pickle.dumps(packet)


def deserialize_packet(packet):
    """Deserialize packet."""
    return pickle.loads(packet)


def convert_buffer_to_file():
    """Write receiver buffer to output file."""
    global filename
    global receiver_buffer

    list_of_keys = list(receiver_buffer.keys())
    sort_list = sorted(list_of_keys)
    f = open(filename, "wb")
    for i in sort_list:
        f.write(receiver_buffer.get(i))


def add_to_log(packet, direction):
    """Append packet information to log[]."""
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
        total_time = str(round(total_time, 2))
    if pkt.get_payload() is None:
        data_size = 0
    else:
        data_size = pkt.payload_size()
    new = logger(direction, total_time, pkt_type, seq_num, data_size, ack_num)
    print(new.list_attr())
    log.append(new)


def create_log():
    """Write to log file."""
    global log
    global receiver_buffer
    global overall_logger

    overall_logger.update_field("size_of_file", calculate_size())
    overall_logger.update_field("data_segments", len(receiver_buffer.keys()))

    overall_logger_dict = overall_logger.get_dict()
    with open('receiver_log.txt', 'w') as f:
        for logs in log:
            f.write('\t'.join(str(i) for i in logs.list_attr()))
            f.write("\n")

        f.write("\n\n============SUMMARY============\n")
        for itr in overall_logger_dict.keys():
            f.write("%s: %d\n" % (itr, overall_logger_dict[itr]))
        f.write("\n===========================================")


def calculate_size():
    """Return size of file based on receiver buffer."""
    global receiver_buffer
    i = 0
    for keys in list(receiver_buffer.keys()):
        i = i + len(receiver_buffer.get(keys))
    return i

main()
