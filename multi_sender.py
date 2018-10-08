import socket
from packet import *
import pickle
import os # needed for size of file


# Initialized Variables
# Hard coded for now, add arguments later
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)
INITIAL_SEQ = 0
INITIAL_ACK = 0
MSS = 150
MWS = 600
sender_buffer = []
SEND_BASE = 0
y = 0

# initial timeout attributes
InitialEstimatedRTT = 500
InitialDevRTT = 250
# fake file for now
FAKE_FILE = 2300


def main():

    handshake()
    send_file()
# send two packets
# changes satte
def handshake():
    pkt1 = packet("SYN", 0, 0)
    send_data(pkt1)
    pkt2 = packet("ACK", 0, 1)
    send_ack(pkt2)

    # function that checks packets have been received ()
    CONNECTION_STATE = "CONNECTED"

def send_file():
    print("Beginning file sending procedure procedure")

    packets_to_send = generate_packets[]
    


# array of all the packets that have to be sent to the receiver side
def generate_packets():

    array = []  # list 

    with open("test0.pdf", "rb") as fi:
        buf = fi.read(150)
        counter = 0
        encapsulate_data(buf, array, counter)  # TODO: refactor this

        while (buf):
            counter = counter + 1
            buf = fi.read(150)
            encapsulate_data(buf, array, counter)

# encapsualtes the data into a packet
# extra function needed due to conversion to bytes and stuff
# sets the sequence number to appropriate value
def encapsulate_data(data, array, count):
    SEQ_NUM = count * 150 + 1
    ACK_NUM = 1  # always 1?
    pkt = packet("DATA", SEQ_NUM, ACK_NUM)
    pkt.add_payload(data)  # not sure if i should pickle it first?
    array.append(pkt)

# IMPORTANT FUNCTIONS
def send_data(packet):
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.settimeout(10)
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
                check = deserialize_packet(packet)
                print ("received at sender", check.get_packet_type())
                break
            except:
                # if nothing comes back
                print ("Did not receive an ACK")
                exit(0)
        # if we received an ACK
        process_packet(packet)
        sender_socket.close()
    except:
        exit(0)
        pass

# gets the return ACK Packet determines what to do next
def process_packet(packet):
    pkt = deserialize_packet(packet)
    seq_num = pkt.get_seq_num()
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()

    if pkt_type == "ACK":
        print ("received an ACK")
    elif pkt_type == "SYNACK":
        print("received a SYNACK")
    else:
        print("recieved another packet")



# HANDSHAKE STUFF
# sends an individual ACK without expecting a return (gotta incorporate this inside later)
def send_ack(packet):
    print ("sending:", packet.get_packet_type())
    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender_socket.settimeout(10)
    sender_socket.sendto(serialize_packet(packet), hostport)



# UTILS
def serialize_packet(packet):
    return pickle.dumps(packet)

def deserialize_packet(packet):
    return pickle.loads(packet)






# start function call
main()
