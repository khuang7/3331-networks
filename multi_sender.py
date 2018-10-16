import socket
from packet import *
import pickle
import time
import threading
import collections
from random import *
import random



# Initialized Variables
# Hard coded for now, add arguments later
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)
INITIAL_SEQ = 0
INITIAL_ACK = 0
MSS = 150
MWS = 600

timeout = 1.5 # make it initially one
timer_active = None # global variable to check the timer is on or not

# initial timeout attributes
EstRTT = 500
DevRTT = 250
# fake file for now
FAKE_FILE = 2300
CONNECTION_STATE = 0  # connected or not connected to receiver

sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
acks_received = []
window = []
cumulative_ack = 0  # the sender know the receiver has got all bytes up to this byte stream
packets_to_send = {}
file_not_sent = 1


def main():
    handshake()
    send_file()
    teardown_connection()


# send two packets
# changes satte
def handshake():
    global CONNECTION_STATE
    initial_pkt = packet("SYN", 0, 0)
    send_syn(initial_pkt)
    # function that checks packets have been received ()
    CONNECTION_STATE = 1


def send_file():
    # opens the file and generates all the packets that need to be sent
    global packets_to_send
    global acks_received
    global file_not_sent

    packets_to_send = generate_packets()
    print_dict_packets(packets_to_send)

    # thread that constantly receives acks and changes the acks received and window
    receiving_thread = threading.Thread(target=receive_packets)
    receiving_thread.start()

    # keep sending until the file is fully sent
    while file_not_sent:
        # slowing it down to see what happens
        print ("+++++++++++++++++++++++++++++++++++++")

        time.sleep(3)
        # comapres acks_received and window, if any of acks received inside window
        # then remove it
        print ("window before updating", window)
        update_window()
        print("window after checking acks", window)

        # if all the packets are known to be received on the other side
        if len(window) >= (MWS / MSS) :
            print("window is full! WAIT PLS")
            continue

        if len(packets_to_send) == 1:  # TODO: fix the way its count later
            print("we are going to send a fin packet and end it")
            return

        '''
        PLD CODES
        # possible outcomes
        DROP_PACKET = 1
        DUPLICATE = 2
        CORRUPT = 3
        OUT_OF_ORDER = 4
        DELAY = 5
        NOTHING = 6
    
        '''
        # determines what will happen to the packet
        PLD = 6
        pkt = choose_packet(packets_to_send)
        if (random.uniform(0, 1) < 0.3):
            PLD = 2
        elif (random.uniform(0, 1) < 0.5):
            print("going to corrupt packet")
            PLD = 3
        else:
            PLD = 6

        send_packet(pkt, PLD)

# ensures that the window has the right values every time (maybe i should update this more?)
def update_window():
    global acks_received
    global window

    for i in window:
        if i in acks_received:
            window.remove(i)

# this will be called as a thread that will stop when needed
# constantly receives and does something to the packet
def receive_packets():
    while True:
        try:
            packet, server = sender_socket.recvfrom(4096)
            process_packet(packet)
        except:
            pass
# for each ack we receive update:
# window
# acks received
# packets_to_send
def process_packet(packet):
    global acks_received
    global packets_to_send
    global timer_active
    global window

    pkt = deserialize_packet(packet)
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()
    seq_num = ack_num - MSS  # the packet number we are acknowledging
    print ("RECEIVED ACK NUM:", ack_num)
    if pkt_type == "ACK":
        if (ack_num not in acks_received):
            acks_received.append(ack_num)
            packets_to_send.pop(seq_num)
            print ("removed from packets_to_send", seq_num, packets_to_send.keys())
            window.remove(seq_num)
            print ("removed from window ", seq_num, window)

            if (timer_active == seq_num):
                timer_active = None
                # activate timer for next window space if free
                if (window):
                    print("started a timer")
                    timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
                    timer.start()
    else:
        print("another packet received somehow..")




# returns the next packet to send
# algorithm determine what the next packet should be sent




def choose_packet(packets_to_send):
    global window
    global acks_received
    global base # base of the window

    list_of_keys = list(packets_to_send.keys())

    print("checking the window", window)
    # if the window is empty just send first packet
    if (not window):
        print("window is EMPTY")
        index = list_of_keys[0]
        base = index
        print("chooses this packet from an empty window")
        packets_to_send.get(index).simple_print()
        return packets_to_send.get(index)
    # window contains something, so choose the first packet not in the window
    else:
        for s in list_of_keys:
            if s not in window:
                index = s
                break
        print("chooses this packet from a full window")
        packets_to_send.get(index).simple_print()
        return packets_to_send.get(index)


# returns true if the window is full
def full_window():
    global window
    True if (len(window) >= MWS / MSS) else False


# PLD = 1
def drop_packet(packet):
    global window
    global timer_active
    global timeout

    seq_num = packet.seq_num
    print ("DROPPING PACKET seqnum:", seq_num)

    window.append(seq_num)
    print("changing window", window)
    if not timer_active:
        print("changed timer_active to", timer_active)
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()
        return  # exit the function

# sends the actual data packet
def send_packet(packet, PLD):

    if PLD == 2:
        drop_packet(packet)
        return

    if PLD == 3:
        packet.corrupt()

    global window
    global timer_active
    global timeout
    seq_num = packet.get_seq_num()
    payload_size = packet.payload_size()

    print("TImer active before sending packet is", timer_active)

    if (seq_num not in window):
        window.append(seq_num)

    # this will limit what we send (so if we know we already have an ack)
    # we dont have to send it again
    # seq_num is the next packet
    if (seq_num + payload_size in acks_received):
        return

    print("updated window", window)
    print("SENDING THIS PACKET")
    packet.simple_print()
    serialize = serialize_packet(packet)
    sender_socket.sendto(serialize, hostport)

    # if the timer is not active
    print("value of timer after timeout", timer_active)

    if timer_active is None:
        print("activated the timer for seq_num")
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()
    else:
        print("timer already on do nothing")


# runs a timer for timeout
# if the ack for the timer has been received already
# then we do nothing
def single_timer(timeout, seq_num):
    print("timer for seqnum has started:", seq_num)

    time.sleep(timeout)

    global timer_active
    global window
    global acks_received
    global packets_to_send

    print("RESENDING PACKETS!! and TIMER RESET")
    print("comparing timer_active and seq_num", timer_active, seq_num)
    # this ensures that the timer will only resend if the timer_active doesnt change

    if (seq_num == timer_active):
        print("resending this window!", window)
        for i in window:
            if (i in packets_to_send):
                print("resending", i)
                # generate a new PLD again
                send_packet(packets_to_send.get(i), 1)
    
    print("changed timer active to none")
    timer_active = None  # reset timer

# everytime we receive an ACK we will update the static timeout value
def update_timeout(new_sampleRTT):
    # take RTT from previous
    # EstRTT and DevRtt are 
    global timeout
    global EstRTT
    global DevRTT

    alpha = 0.25
    beta = 0.25
    EstRTT = (1 - alpha) * EstRTT + alpha * new_sampleRTT
    DevRTT = (1 - beta) * DevRTT + beta * (new_sampleRTT - EstimatedRTT)
    timeout = (EstRTT + 4 * DevRTT) / 1000 # since we need the timeout to be in seconds




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
def send_syn(packet):
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
                exit(0)  # shoufld never go here hopefully

        if (deserialize_packet(packet).get_packet_type() == "SYNACK"):
            print("received a synack and going to send an ack")            

    except:
        print("cannot establish connection")
        exit(0)
        pass

    send_ack(1,1)


# HANDSHAKE STUFF
# sends an individual ACK without expecting a return
def send_ack(seq_num, ack_num):
    pkt2 = packet("ACK", seq_num, ack_num)
    print ("sending:", pkt2.get_packet_type())
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.settimeout(10)
    sender_socket.sendto(serialize_packet(pkt2), hostport)

def teardown_connection():
    pkt = packet("FIN", 10000, 1)
    sender_socket.sendto(serialize_packet(pkt), hostport)

def print_dict_packets(dictionary):
    for key, value in dictionary.items():
        print ("%s --> (SEQ: %d, ACK %d)" % (key, value.seq_num, value.ack_num))


def serialize_packet(packet):
    return pickle.dumps(packet)


def deserialize_packet(packet):
    return pickle.loads(packet)


# start function call
main()
