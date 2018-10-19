import socket
from packet import *
import pickle
import time
import threading
import collections
from logger import *
import sys
from PLD import *
from utils import serialize_packet, deserialize_packet

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

timestamper = {}
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
    last_seq_num = list(packets_to_send.keys())[-1]
    last_data_byte_stream = last_seq_num + packets_to_send.get(last_seq_num).payload_size()

    receiving_thread = threading.Thread(target=receive_packets, args = (last_data_byte_stream, ))
    receiving_thread.start()
    # keep sending until the file is fully sent
    while file_not_sent:

        print ("EVERY ITERATION")
        print ("chooses a packet to send from this list")
        print_dict_packets(packets_to_send)
        print("also looking at acks_received", acks_received)

        if acks_received:
            highest_ack = sorted(acks_received)[-1]
            update_packetstosend(highest_ack)
        # checker for the global variables

        if not packets_to_send:  # TODO: fix the way its count later
            print("FINISHED SENDING FILE")
            return  # goes to close file

        # my code dies without giving it some time to check between packets
        #time.sleep(0.3)

        if len(window) >= (MWS / MSS):
            continue

        global PLD_list
        PLD = 6  # default just incase
        PLD = PLD_gen(PLD_list)

        if packets_to_send:
            pkt = choose_packet(packets_to_send)
        if pkt is not None:
            send_packet(pkt, PLD)


# ensures that the window has the right values every time (maybe i should update this more?)
def update_window():
    global acks_received
    global window
    # since we are using accumulative acknolwedgement
    if acks_received:
        highest_ack = sorted(acks_received)[-1]
    else:
        highest_ack = 0
    for i in window:
        if i < highest_ack:
            window.remove(i)


# this will be called as a thread that will stop when needed
# constantly receives and does something to the packet
def receive_packets(stopper):
    while True:
        global acks_received
        global packets_to_send
        global timestamper

        if (stopper in acks_received):
            print("RECEIVER_THREAD_STOP")
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
    global timestamper

    duplicates = []

    pkt = deserialize_packet(packet)
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()
    # need to consider edge case (last packet will be a different size)

    if (ack_num == last_data_byte_stream):
        pop_off = list(packets_to_send.keys())[-1] # hardcoded
    elif(ack_num == 1):
        pop_off = 0
    else:
        pop_off = ack_num - MSS  # the packet number we are acknowledging
        update_packetstosend(ack_num)

    if pkt_type == "ACK":
        last_ack_received = ack_num
        
        duplicates.append(ack_num)

        if (ack_num not in acks_received):
            acks_received.append(ack_num)
            window.remove(pop_off)
             # receiver a packet and update the timeout based on the RTT
            if (ack_num in list(timestamper.keys())):
                sampleRTT = time.time() - timestamper.get(ack_num)
                # update_timeout(sampleRTT)

            if (timer_active == seq_num):
                timer_active = None
                # activate timer for next window space if free
                if (window):
                    timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
                    timer.start()

        # duplciates will go in here
        else:
            if ack_num in duplicates:
                duplicates.append(ack_num)
            else:
                del duplicates[:]
            
            if (len(duplicates)):
                # FAST RETRANSMIT
                send_packet(packet, 1)

    else:
        pass


# accumlatively deletes packets to send
def update_packetstosend(ack_num):
    global packets_to_send
    for i in list(packets_to_send.keys()): 
        if (i < ack_num):
            packets_to_send.pop(i)
        if (i > ack_num):
            break

# returns the next packet to send
# algorithm determine what the next packet should be sent
def choose_packet(packets_to_send):

    # just incase the receiving thread somehow doesnt update in time
    if (not packets_to_send):
        return None

    global window
    global acks_received
    global base # base of the window

    list_of_keys = list(packets_to_send.keys())

    # if the window is empty just send first packet
    if (not window):
        index = list_of_keys[0]
        base = index
        print("CHOOSE PACKET chose indexno:", index)
        return packets_to_send.get(index)
    # window contains something, so choose the first packet not in the window
    else:
        print ("window is filled with something, choses the first index which doesnt exist in window")
        for s in list_of_keys:
            if s not in window:
                index = s
                break
        print("CHOOSE PACKET chose indexno:", index)        
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
    # drop packet
    if PLD == 1:
        drop_packet(packet)
        return
    # corrupt packet
    if PLD == 3:
        packet.corrupt()
    if PLD != 3:
        packet.uncorrupt()  # refactor this later

    if PLD == 5:
        # delay by waiting a certain time between 0 and max delay
        time.sleep(random.random(0, maxDelay))

    global window
    global timer_active
    global timeout
    global timestamper
    global log

    seq_num = packet.get_seq_num()
    payload_size = packet.payload_size()

    if (seq_num not in window):
        window.append(seq_num)

    if (seq_num + payload_size in acks_received):
        return

    serialize = serialize_packet(packet)
    sender_socket.sendto(serialize, hostport)
    timestamper[packet.get_seq_num() + packet.payload_size()] = time.time()
    add_to_log(serialize, "snd")
    if timer_active is None:
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()

# my code creates a new thread for every new timer made
def single_timer(timeout, seq_num):
    print ("MAKING A NEW TIMER FOR", seq_num)
    time.sleep(timeout)

    # acquire these variables AFTER the timer runs out
    global timer_active
    global window
    global acks_received
    global packets_to_send

    if (seq_num == timer_active):
        print ("RESENDING WINDOW!!")
        for i in window:
            if (i in packets_to_send):
                send_packet(packets_to_send.get(i), 6)
    timer_active = None  # reset timer


# everytime we receive an ACK we will update the static timeout value
# could not implement
def update_timeout(new_sampleRTT):
    global timeout
    global EstRTT
    global DevRTT
    global gamma

    alpha = 0.25
    beta = 0.25
    EstRTT = (1 - alpha) * EstRTT + alpha * new_sampleRTT
    DevRTT = (1 - beta) * DevRTT + beta * (new_sampleRTT - EstRTT)
    timeout = (EstRTT + gamma * DevRTT) / 1000 # since we need the timeout to be in seconds


def generate_packets():
    global filename
    global MSS

    dictionary = {}
    with open(filename, "rb") as fi:
        buf = fi.read(MSS)
        counter = 0
        encapsulate_data(buf, dictionary, counter)  # TODO: refactor this

        while (buf):
            counter = counter + 1
            buf = fi.read(MSS)
            if (len(buf) != 0):
                encapsulate_data(buf, dictionary, counter)
    return collections.OrderedDict(dictionary)


# encapsualtes the data into a packet
# extra function needed due to conversion to bytes and stuff
# sets the sequence number to appropriate value
def encapsulate_data(data, dictionary, count):
    seq_num = count * MSS + 1
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
        add_to_log(serialize, "snd")
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
    add_to_log(serialize, "snd")


def teardown_connection():
    global last_ack_received
    global CONNECTION_STATE
    global log

    pkt = packet("FIN", last_ack_received, 1)
    serialize = serialize_packet(pkt)
    sender_socket.sendto(serialize, hostport)
    add_to_log(serialize, "snd")
    print("sending a FIN")
    CONNECTION_STATE = "FIN_WAIT_1"


    while True:
        try:
            received, server = sender_socket.recvfrom(4096)
            add_to_log(received, "rcv")
        except:
            print("teardown failed")

        if received:
            rcv = deserialize_packet(received)
            if rcv.get_packet_type() == "FIN":
                send_ack(rcv.get_ack_num(), 2)
                print ('FINISHED')
                create_log()
                exit(0)
                break


def print_dict_packets(dictionary):
    new = dictionary.copy()
    for key, value in new.items():
        print ("%s --> (SEQ: %d, ACK %d)" % (key, value.seq_num, value.ack_num))


# always give thsi function a SERIALIZED PACKET
def add_to_log(packet, direction):
    global overall_timer
    global log
    global timestamp

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

    with open('sender_log.txt', 'w') as f:
        for logs in log:
            f.write("%s\n" % logs.list_attr())

main()
