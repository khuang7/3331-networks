import socket
from packet import *
import pickle
import os  # needed for size of file
import time
import PLD
import threading
import collections


# Initialized Variables
# Hard coded for now, add arguments later
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)
INITIAL_SEQ = 0
INITIAL_ACK = 0
MSS = 150
MWS = 600

# initial timeout attributes
InitialEstimatedRTT = 500
InitialDevRTT = 250
# fake file for now
FAKE_FILE = 2300
CONNECTION_STATE = 0  # connected or not connected to receiver

sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
acks_received = []
window = []
last_byte_sent = 0
last_byte_acked = 0
cumulative_ack = 0  # the sender know the receiver has got all bytes up to this byte stream
packets_to_send = {}
file_not_sent = 1

def main():
    handshake()
    # overall timer start here
    send_file()




# send two packets
# changes satte
def handshake():
    global CONNECTION_STATE
    pkt1 = packet("SYN", 0, 0)
    send_data(pkt1)
    pkt2 = packet("ACK", 1, 1)  # i shoudl put this insdie the same functino.. do later
    send_ack(pkt2)

    # function that checks packets have been received ()
    CONNECTION_STATE = 1


def send_file():
    # opens the file and generates all the packets that need to be sent
    global packets_to_send
    global acks_received
    global last_byte_acked
    global last_byte_sent
    global file_not_sent

    packets_to_send = generate_packets()
    print_dict_packets(packets_to_send)

    # keep sending until the file is fully sent
    while file_not_sent:

        # slowing it down to see what happens
        time.sleep(5)

        # if all the packets are known to be received on the other side
        if (full_window()):
            sleep(1000)

        if len(packets_to_send) == 1:  # TODO: fix the way its count later
            exit(0)

        pkt = choose_packet(packets_to_send)


        thread = threading.Thread(target=send_packet, args=(pkt,))
        thread.start()


# returns the next packet to send
# algorithm determine what the next packet should be sent
def choose_packet(packets_to_send):
    global window
    global acks_received

    list_of_keys = list(packets_to_send.keys())
#    list_of_window = list(window.keys())
#    next_seq_num = list_of_keys[0]


    # empty window
    if (not window):
        # START TIMER
        return return_packet(list_of_keys[0], packets_to_send)
        # send the first packet in the packets to send list
    # this function wont be accessed if the window is full
    else:
        if (not full_window()):
            # return next available packet
            # make a check that the last packet in window is not hte last packet
            return return_packet(list_of_keys[-1] + 150, packets_to_send)


# returns true if the window is full
def full_window():
    global window
    True if (len(window) >= MWS / MSS) else False


# returns the packet based on a key and dictionary
def return_packet(seq_num, packets_to_send):
    return packets_to_send[seq_num]



# sends the actual data packet
def send_packet(packet):
    global last_byte_acked
    global last_byte_sent
    global done
    done = 1
    seq_num = packet.seq_num
    last_byte_sent = packet.seq_num
    window.append(packet.seq_num)
    print("updated window", window)

    packet.simple_print()
    serialize = serialize_packet(packet)
    sender_socket.sendto(serialize, hostport)


    while True:
        try:
            packet, server = sender_socket.recvfrom(4096)
            break
        except:
            # this should only happen if somehow the packet didnt send (NOT TIME)
            # if nothing comes back
            print ("Did not receive an ACK")
            exit(0)  # should never go here hopefully
    process_packet(packet, seq_num)



# looks at the ack number: determines what to do next
# seq_num is what we sent initially (what it received from)
def process_packet(packet, seq_num):
    global acks_received
    global last_byte_acked
    global packets_to_send

    pkt = deserialize_packet(packet)
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()

    if pkt_type == "ACK":
        if (ack_num not in acks_received):
            acks_received.append(ack_num)
            last_byte_acked = ack_num
            packets_to_send.pop(seq_num)
            print ("updated packets to send", packets_to_send)
            window.remove(seq_num)
            print ("updated window", window)



# everytime we receive an ACK we will update the static timeout value
def update_timeout(new_sampleRTT):
    # take RTT from previous
    # EstRTT and DevRtt are 
    alpha = 0.25
    beta = 0.25
    EstRTT = (1 - alpha) * EstRTT + alpha * new_sampleRTT
    DevRTT = (1 - beta) * DevRTT + beta * (new_sampleRTT - EstimatedRTT)
    timeout = EstRTT + 4 * DevRTT


def generate_packets():

    dictionary = {}
    with open("test0.pdf", "rb") as fi:
        buf = fi.read(150)
        counter = 0
        encapsulate_data(buf, dictionary, counter)  # TODO: refactor this

        while (buf):
            counter = counter + 1
            buf = fi.read(150)
            encapsulate_data(buf, dictionary, counter)
    #  try to make it such that the last byte contains a FIN flag
    return collections.OrderedDict(dictionary)


# encapsualtes the data into a packet
# extra function needed due to conversion to bytes and stuff
# sets the sequence number to appropriate value
def encapsulate_data(data, dictionary, count):
    seq_num = count * 150 + 1
    ack_num = 1  # always 1?
    pkt = packet("DATA", seq_num, ack_num)
    pkt.add_payload(data)  # not sure if i should pickle it first?
    dictionary[seq_num] = pkt




# IMPORTANT FUNCTIONS
# send data and waits for a return
def send_data(packet):
    serialize = serialize_packet(packet)
    try:
        sender_socket.sendto(serialize, hostport)
        check = deserialize_packet(serialize)
        print ("sent initially from sender:", check.get_packet_type())
        # waiting for an ack acknowledgement
        # after a certain time period of timeout (no need for handshake)
        while True:
            try:
                packet, server = sender_socket.recvfrom(4096)
                break
            except:
                # if nothing comes back
                print ("Did not receive an ACK")
                exit(0)  # should never go here hopefully
    except:
        exit(0)
        pass


# HANDSHAKE STUFF
# sends an individual ACK without expecting a return (gotta incorporate this inside later)
def send_ack(packet):
    print ("sending:", packet.get_packet_type())
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.settimeout(10)
    sender_socket.sendto(serialize_packet(packet), hostport)

def print_dict_packets(dictionary):
    for key, value in dictionary.items():
        print ("%s --> (SEQ: %d, ACK %d)" % (key, value.seq_num, value.ack_num))

def serialize_packet(packet):
    return pickle.dumps(packet)

def deserialize_packet(packet):
    return pickle.loads(packet)


# start function call
main()
