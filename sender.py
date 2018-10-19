"""Sender.py on Python3.6.3.

Kevin Huang (z3461590) 3331_ass1

Takes in a file, splits it into packets and sends these packets over to
receiver.py over a UDP connection

"""
import socket
from packet import packet
import time
import threading
import collections
from logger import logger, overall_sender_logger
import sys
from PLD import PLD_gen
import os
import pickle
import random

""" Argument Checker"""
if len(sys.argv) != 15:
    print("Usage Python sender.py receiver_host_ip \
           receiver_port file.pdf MWS MSS gamma pDrop \
           pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed")
    sys.exit(1)

"""Initialize Variables"""
rcv_host_ip = sys.argv[1]
rcv_port = int(sys.argv[2])
hostport = (rcv_host_ip, rcv_port)
filename = sys.argv[3]
MWS = int(sys.argv[4])
MSS = int(sys.argv[5])
gamma = int(sys.argv[6])
EstRTT = 500
DevRTT = 250
timeout = (500 + gamma * DevRTT) / 1000

"""PLD Variables"""
PLD_list = []
for i in range(7, 15):
    PLD_list.append(float(sys.argv[i]))

random.seed(int(PLD_list[7]))

"""Global Variables"""
timer_active = None
CONNECTION_STATE = "CLOSED"
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

"""Logger Variables"""
log = []
overall_timer = None
overall_logger = overall_sender_logger()


def main():
    """Entry point into sender function.

    Sequentially calls the three processes required for what TCP does
    Handshake to initiate connection
    Send file to send the data over the socket
    Teardown to finish the connection
    """
    handshake()
    send_file()
    teardown_connection()


"""=============HANDSHAKE FUNCTIONS============="""


def handshake():
    """Handshake Function.

    Creates an initial SYN packet and sends it
    Establishes connection when complete
    """
    global CONNECTION_STATE
    initial_pkt = packet("SYN", 0, 0)
    send_syn(initial_pkt)
    CONNECTION_STATE = "ESTABLISHED"
    print("HANDSHAKE COMPLETE")


def send_syn(packet):
    """Send a Syn Packet."""
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
                print ("Could not establish conection")
                exit(0)
        if (deserialize_packet(packet).get_packet_type() == "SYNACK"):
            send_ack(1, 1)
    except:
        print("Could not establish conection")
        exit(0)
        pass


def send_ack(seq_num, ack_num):
    """Send an ACK packet."""
    pkt = packet("ACK", seq_num, ack_num)
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serialize = serialize_packet(pkt)
    sender_socket.sendto(serialize, hostport)
    add_to_log(serialize, "snd")


"""=============SEND FILE ============="""


def send_file():
    """Open the file and generates all the packets that need to be sent."""
    global packets_to_send
    global acks_received
    global file_not_sent
    global last_data_byte_stream
    global overall_timer
    overall_timer = time.time()
    packets_to_send = generate_packets()
    last_seq_num = list(packets_to_send.keys())[-1]
    last_data_byte_stream = last_seq_num + packets_to_send.get(last_seq_num).payload_size()

    receiving_thread = threading.Thread(target=receive_packets, args = (last_data_byte_stream, ))
    receiving_thread.start()
    while file_not_sent:
        if acks_received:
            highest_ack = sorted(acks_received)[-1]
            update_packetstosend(highest_ack)
        if not packets_to_send:
            print("FINISHED SENDING FILE")
            return  # goes to close file
        time.sleep(0.3)

        if len(window) >= (MWS / MSS):
            continue
        global PLD_list
        pld = 6  # default code to normally send packet
        pld = PLD_gen(PLD_list)

        if packets_to_send:
            pkt = choose_packet(packets_to_send)
        if pkt is not None:
            send_packet(pkt, pld)


"""Generates Packets """


def generate_packets():
    """Return a dictionary that contains all the packets.

    Splits the packets in segments of MSS and puts it inside a packet
    Key --> Value == sequence number --> packet class (and payload)
    """
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


def encapsulate_data(data, dictionary, count):
    """Create a packet and put payload in then add packet to dictionary."""
    seq_num = count * MSS + 1
    ack_num = 1  # always 1?
    pkt = packet("DATA", seq_num, ack_num)
    pkt.add_payload(data)
    dictionary[seq_num] = pkt


""" RECEIVING THREAD FUNCTIONS """


def receive_packets(stopper):
    """Keep a while loop on that receives packets.

    This code is intended to run whilst the sender is sending packets
    Constantly updates variables based on what is given
    Stopper arg indicates when to stop the thread (stopper = ack of last packet)
    """
    while True:
        global acks_received
        global packets_to_send
        global timestamper

        if (stopper in acks_received):
            return

        if packets_to_send is None:
            return
        try:
            packet, server = sender_socket.recvfrom(4096)
            add_to_log(packet, "rcv")
            process_packet(packet)
        except:
            pass


def process_packet(packet):
    """Determine what to do with the packet that has arrived.

    Updates necessary global variables depending on what we have already
    """
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

    if (ack_num == last_data_byte_stream):
        pop_off = list(packets_to_send.keys())[-1]
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
            if (ack_num in list(timestamper.keys())):
                sampleRTT = time.time() - timestamper.get(ack_num)
                # update_timeout(sampleRTT)
            if (timer_active == seq_num):
                timer_active = None
                # activate timer for next window space if free
                if (window):
                    timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
                    timer.start()
        else:
            if ack_num in duplicates:
                duplicates.append(ack_num)
            else:
                del duplicates[:]

            if (len(duplicates) == 2):
                overall_logger.increment_field("fast_retransmissions")
                overall_logger.increment_field("dup_acks")
                overall_logger.increment_field("dup_acks")
                overall_logger.increment_field("dup_acks")
                send_packet(packet, 1)
                del duplicates[:]
    else:
        pass


""" FUNCTIONS involving sending the packet """


def choose_packet(packets_to_send):
    """Return the next packet to be sent.

    This function determiens the next packet to send by the overall
    packets_to_send list and also the window to see if its already in flight
    """
    if (not packets_to_send):
        return None

    global window
    global acks_received
    global base

    list_of_keys = list(packets_to_send.keys())
    if not list_of_keys:
        return None
    index = 0
    if (not window):
        index = list_of_keys[0]
        base = index
        return packets_to_send.get(index)
    else:
        for s in list_of_keys:
            if s not in window:
                index = s
                break
        return packets_to_send.get(index)


def send_packet(packet, pld):
    """Send the packet.

    PLD determines what happens to the packet (refer to PLD.py)
    """
    if pld == 1:
        drop_packet(packet)
        return
    if pld == 3:
        packet.corrupt()
        overall_logger.increment_field("segments_corrupted")
    if pld != 3:
        packet.uncorrupt()
    if pld == 5:
        overall_logger.increment_field("segments_delayed")
        time.sleep(random.random(0, maxDelay))
    if pld != 6:
        overall_logger.increment_field("segments_PLD")

    global window
    global timer_active
    global timeout
    global timestamper
    global log

    overall_logger.increment_field("segments_transmitted")
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


def single_timer(timeout, seq_num):
    """Initiate a new timer for a new seq_num that we send.

    The window won't resend unless the timer_active is the same value as the
    seq_num. This is used to ensure that if there is a new timer being activated
    for another packet then this thread won't resend the window
    """
    time.sleep(timeout)

    # acquire these variables AFTER the timer runs out
    global timer_active
    global window
    global acks_received
    global packets_to_send

    if (seq_num == timer_active):
        update_window()
        for i in window:
            overall_logger.increment_field("number_retransmissions")
            if (i in packets_to_send):
                send_packet(packets_to_send.get(i), 6)
    timer_active = None


def drop_packet(packet):
    """Drop the packet.

    Function gets called when PLD == 1
    Adds to the window but does not actually send
    """
    global window
    global timer_active
    global timeout
    global log

    seq_num = packet.seq_num
    window.append(seq_num)
    serialize = serialize_packet(packet)
    add_to_log(serialize, "drop")
    overall_logger.increment_field("segments_dropped")

    if not timer_active:
        timer_active = seq_num
        timer = threading.Thread(target=single_timer, args=(timeout, seq_num))
        timer.start()
        return


"""=============TEARDOWN CONNECTION ============="""


def teardown_connection():
    """Initiate the closing of the connection."""
    global last_ack_received
    global CONNECTION_STATE
    global log

    pkt = packet("FIN", last_ack_received, 1)
    serialize = serialize_packet(pkt)
    sender_socket.sendto(serialize, hostport)
    add_to_log(serialize, "snd")

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
                print ('TEARDOWN COMPLETE')
                create_log()
                exit(0)
                break


"""===========GLOBAL VARIABLE UPDATES and UTILITY FUNCTIONS==========="""


def update_window():
    """Change window based on acks_received."""
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


def update_packetstosend(ack_num):
    """Change packets_to_send dictionary based on ack_num given."""
    global packets_to_send
    for i in list(packets_to_send.keys()): 
        if (i < ack_num):
            packets_to_send.pop(i)
        if (i > ack_num):
            break


def full_window():
    """Determine if window is full or not."""
    global window
    True if (len(window) >= MWS / MSS) else False


def print_dict_packets(dictionary):
    """Print packet to send in nice format."""
    if not dictionary:
        print ("EMPTY")
    else:
        new = dictionary.copy()
        for key, value in new.items():
            print ("%s --> (SEQ: %d, ACK %d)" % (key, value.seq_num, value.ack_num))


def update_timeout(new_samplertt):
    """Update the timeout based on RTT given."""
    global timeout
    global EstRTT
    global DevRTT
    global gamma

    new_samplertt = new_sampleRTT * 1000 # convert to milliseconds
    alpha = 0.25
    beta = 0.25
    EstRTT = (1 - alpha) * EstRTT + alpha * new_sampleRTT
    DevRTT = (1 - beta) * DevRTT + beta * (new_sampleRTT - EstRTT)
    timeout = (EstRTT + gamma * DevRTT)  # since we need the timeout to be in seconds


def serialize_packet(packet):
    """Serialize packet."""
    return pickle.dumps(packet)


def deserialize_packet(packet):
    """Deserialize packet."""
    return pickle.loads(packet)


def add_to_log(packet, direction):
    """Add packet flow info to log."""
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
        total_time = str(round(total_time, 2))

    if pkt.get_payload() is None:
        data_size = 0
    else:
        data_size = pkt.payload_size()
    new = logger(direction, total_time, pkt_type, seq_num, data_size, ack_num)
    print (new.list_attr())
    log.append(new)


def create_log():
    """Create log txt file."""
    global log
    global overall_logger
    global filename

    overall_logger.update_field("size_of_file", os.path.getsize(filename))

    overall_logger_dict = overall_logger.get_dict()
    with open('sender_log.txt', 'w') as f:
        for logs in log:
            f.write('\t'.join(str(i) for i in logs.list_attr()))
            f.write("\n")

        f.write("\n\n============SUMMARY============\n")
        for itr in overall_logger_dict.keys():
            f.write("%s: %d\n" % (itr, overall_logger_dict[itr]))
        f.write("\n===========================================")
main()
