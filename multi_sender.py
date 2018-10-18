import socket
from packet import *
import pickle
import time
import threading
import collections
from logger import *
import sys
from PLD import *


print(len(sys.argv))

if len(sys.argv) != 15:
    print("Usage Python sender.py receiver_host_ip \
           receiver_port file.pdf MWS MSS gamma pDrop \
           pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed")
    sys.exit(1)

# initialize all variables
rcv_host_ip = sys.argv[1]
rcv_port = int(sys.argv[2])
hostport = (rcv_host_ip, rcv_port)
filename = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
gamma = int(sys.argv[6])
EstRTT = 500
DevRTT = 250
timeout = (500 + gamma * DevRTT ) / 1000 # intially tis around a second

# Initialize PLD elements
PLD_list = []
for i in range(7, 15):
    PLD_list.append(float(sys.argv[i]))

random.seed(int(PLD_list[7]))

# GLOBAL VARIABLES + Initialization
timer_active = None # global variable to check the timer is on or not
CONNECTION_STATE = "CLOSED"  # connected or not connected to receiver
INITIAL_SEQ = 0
INITIAL_ACK = 0
acks_received = []
window = []
packets_to_send = {}
file_not_sent = 1
last_ack_received = 0
last_data_byte_stream = 9999 # dummy number
sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Logger
log = []
overall_timer = None


def main():
    global overall_timer
    # the main three processes of sender
    handshake()
    overall_timer = time.time()
    send_file()
    teardown_connection()

def handshake():
    global CONNECTION_STATE
    initial_pkt = packet("SYN", 0, 0)
    send_syn(initial_pkt)
    # function that checks packets have been received ()
    CONNECTION_STATE = "ESTABLISHED"


def send_file():
    # opens the file and generates all the packets that need to be sent
    global packets_to_send
    global acks_received
    global file_not_sent
    global last_data_byte_stream

    packets_to_send = generate_packets()
    number_of_pkts = len(packets_to_send.keys())
    last_seq_num = list(packets_to_send.keys())[-1]
    last_data_byte_stream = last_seq_num + packets_to_send.get(last_seq_num).payload_size()

    receiving_thread = threading.Thread(target=receive_packets, args = (last_data_byte_stream, ))
    receiving_thread.start()


    # keep sending until the file is fully sent
    while file_not_sent:
        print ("Beginning loop with")
        print_dict_packets(packets_to_send)

        if not packets_to_send:  # TODO: fix the way its count later
            print("FINISHED")
            return # goes to close file
        time.sleep(2) # not sure if i can remove this :(
        update_window()

        if len(window) >= (MWS / MSS):
            print("Full window")
            continue

        global PLD_list
        PLD = 6  # default just incase
        PLD = PLD_gen(PLD_list)
        pkt = choose_packet(packets_to_send)
        if pkt is not None:
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
def receive_packets(stopper):


    while True:
        print ("stops when acks received contains this", stopper)
        global acks_received
        global packets_to_send
        print ("inside thread, acks received is", acks_received)

        if (stopper in acks_received):
            print("the thread should have stopped now")
            return  # stop the thread

        if packets_to_send is None:
            return
        try:
            packet, server = sender_socket.recvfrom(4096)
            add_to_log(packet, "rcv")
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
    global last_ack_received
    global last_data_byte_stream

    pkt = deserialize_packet(packet)
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()
    # need to consider edge case (last packet will be a different size)
    if (ack_num == last_data_byte_stream):
        pop_off = list(packets_to_send.keys())[-1] # hardcoded
    else:
        pop_off = ack_num - MSS  # the packet number we are acknowledging
    print("within received thread i get this")
    pkt.simple_print()

    if pkt_type == "ACK":
        last_ack_received = ack_num
        if (ack_num not in acks_received):
            print("popping of seq_num", pop_off)
            print("acks received", ack_num)
            acks_received.append(ack_num)
            packets_to_send.pop(pop_off) # remove packetsto_send once we know we have the ack
            window.remove(pop_off)

            if (timer_active == seq_num):
                timer_active = None
                # activate timer for next window space if free
                if (window):
                    timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
                    timer.start()
    else:
        pass

# returns the next packet to send
# algorithm determine what the next packet should be sent


def choose_packet(packets_to_send):

    print ("chooses a packet to send")
    if (not packets_to_send):
        print("the list is empty")
        return None

    global window
    global acks_received
    global base # base of the window

    list_of_keys = list(packets_to_send.keys())

    # if the window is empty just send first packet
    if (not window):
        print ("window is empty so chooses the first thing in packets to send")
        index = list_of_keys[0]
        print ("chooses packet at index", index)
        base = index
        return packets_to_send.get(index)
    # window contains something, so choose the first packet not in the window
    else:
        print ("window is full, choses the first index which doesnt exist in window")
        for s in list_of_keys:
            if s not in window:
                index = s
                break
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
    global log

    print ("Drop a packet")

    seq_num = packet.seq_num
    window.append(seq_num)

    serialize = serialize_packet(packet)
    add_to_log(serialize, "drop")

    if not timer_active:
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()
        return  # exit the function


# sends the actual data packet
# also passes in the PLD to determine what happens to the packet
def send_packet(packet, PLD):

    if PLD == 1:
        drop_packet(packet)
        return
    if PLD == 3:
        packet.corrupt()

    if PLD != 3:
        packet.uncorrupt()  # refactor this later

    global window
    global timer_active
    global timeout
    seq_num = packet.get_seq_num()
    payload_size = packet.payload_size()

    if (seq_num not in window):
        window.append(seq_num)

    # this will limit what we send (so if we know we already have an ack)
    # we dont have to send it again
    # seq_num is the next packet
    if (seq_num + payload_size in acks_received):
        return

    print ("going to send packet:") 
    packet.simple_print()

    serialize = serialize_packet(packet)
    sender_socket.sendto(serialize, hostport)
    add_to_log(serialize, "snd")

    if timer_active is None:
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()

# my code creates a new thread for every new timer made
def single_timer(timeout, seq_num):

    time.sleep(timeout)

    # acquire these variables AFTER the timer runs out
    global timer_active
    global window
    global acks_received
    global packets_to_send

    if (seq_num == timer_active):
        for i in window:
            if (i in packets_to_send):
                # generate a new PLD again
                send_packet(packets_to_send.get(i), 6)
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
            # len returns 150, sizeof returns 183... so sed
            if (len(buf) != 0):
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
    pkt.add_payload(data)
    dictionary[seq_num] = pkt


# IMPORTANT FUNCTIONS
# send data and waits for a return
def send_syn(packet):
    global CONNECTION_STATE
    serialize = serialize_packet(packet)
    try:
        sender_socket.sendto(serialize, hostport)
        check = deserialize_packet(serialize)
        add_to_log(serialize, "snd")
        CONNECTION_STATE = "SYN_SENT"
        # waiting for an ack acknowledgement
        # after a certain time period of timeout (no need for handshake)
        while True:
            try:
                packet, server = sender_socket.recvfrom(4096)
                add_to_log(packet, "rcv")

                break
            except:
                # if nothing comes back
                print ("Did not receive an ACK")
                exit(0)  # shoufld never go here hopefully

        if (deserialize_packet(packet).get_packet_type() == "SYNACK"):
            send_ack(1,1) # check this later
    except:
        print("cannot establish connection")
        exit(0)
        pass


# HANDSHAKE STUFF
# sends an individual ACK without expecting a return
def send_ack(seq_num, ack_num):
    pkt = packet("ACK", seq_num, ack_num)
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.settimeout(10)
    serialize = serialize_packet(pkt)
    sender_socket.sendto(serialize, hostport)
    add_to_log(serialize, "send")





# TODO FIX THIS:

def teardown_connection():
    global last_ack_received
    global CONNECTION_STATE

    pkt = packet("FIN", last_ack_received, 1)
    serialize = serialize_packet(pkt)
    sender_socket.sendto(serialize, hostport)
    print("sending a FIN")
    CONNECTION_STATE = "FIN_WAIT_1"


    while True:
        try:
            received, server = sender_socket.recvfrom(4096)
            # log here
        except:
            print("teardown failed")

        if received:
            add_to_log(received, "rcv")
            rcv = deserialize_packet(received)

            if rcv.get_packet_type() == "FIN":
                send_ack(1 , 1)
                print ('FINISHED')
                create_log()
                exit(0)
                break




def print_dict_packets(dictionary):
    for key, value in dictionary.items():
        print ("%s --> (SEQ: %d, ACK %d)" % (key, value.seq_num, value.ack_num))


def serialize_packet(packet):
    return pickle.dumps(packet)


def deserialize_packet(packet):
    return pickle.loads(packet)


# always give thsi function a SERIALIZED PACKET
def add_to_log(packet, direction):
    global overall_timer
    global log
    global timestamp


    pkt = deserialize_packet(packet)
    #def __init__(self, direction, time, type, seq_num, data_size, ack_num):
    pkt_type = pkt.get_packet_type()
    seq_num = pkt.get_seq_num()


    # don't include handshake in the time
    if not overall_timer:
        total_time = 0
    else: 

        timestamp = time.time()
        total_time = timestamp - overall_timer

    if pkt.get_payload() is None:
        data_size = 0
    else:
        data_size = pkt.payload_size()
    ack_num = pkt.get_ack_num()
    new = logger(direction, total_time, pkt_type, seq_num, data_size, ack_num)
#    new.print_logger()
    log.append(new)


def create_log():
    global log

    with open('sender_log.txt', 'w') as f:
        for logs in log:
            f.write("%s\n" % logs)

# start function call
main()
