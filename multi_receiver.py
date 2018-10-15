# https://realpython.com/python-sockets/
import socket
import threading
from packet import packet
import pickle


########### INITIALIZED VARIBLES ########### 
# Hard coded for now, add arguments later
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)

receiver_buffer = {}
CONNECTION_STATE = "CLOSED"
base = 1  # expects byte stream 1 initially

# the sequence number the receiver should receive next
global expected_seq_num
expected_seq_num = 0
receiver_buffer = {} #contains the seq_num and payload (not packet)

def main():
    # this part always waits for a connection

    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    receiver_socket.bind(hostport)
    # always wait for a connection
    # start a new thread if a connection comes

    while True:
        data, address = receiver_socket.recvfrom(4000)
        deserialize = deserialize_packet(data)
        thread = threading.Thread(target=handle_connection, args=(deserialize, address))
        thread.start()


# this function gets called every time a packet arrives from sender
def handle_connection(deserialize, address):
    # get the data from outside
    newSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # receives a SYN, ACK or DATA
    # returns the appropriate packet to send back
    pkt = process_packet(deserialize)
    # serilalize the new packet to send over the socket
    pkt = serialize_packet(pkt)
    if pkt is not None:
        newSocket.sendto(pkt, address)


# returns the packet that needs to be sent back, based on what packet is given
def process_packet(pkt):
    global expected_seq_num
    global CONNECTION_STATE
    global receiver_buffer

    seq_num = pkt.get_seq_num()
    pkt_type = pkt.get_packet_type()
    # initial packet sent

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

        if (pkt.seq_num in receiver_buffer.keys()):
            return None  # dont return the packet since we have it already
        else:
            add_to_buffer(pkt)
            new_packet = packet("ACK", 1, get_ack_number(pkt))
            new_packet.simple_print()
            return new_packet



# this algorithm keeps all packets received out of order packets
# returns the appropriate ACK number
def get_ack_number(pkt):
    global expected_seq_num
    global receiver_buffer

    list_of_keys = receiver_buffer.keys()
    seq_num = pkt.seq_num

    # nothign in receiver buffer
    if (not receiver_buffer):
        return expected_seq_num
    else:
        # since we still need the element
        if expected_seq_num < list_of_keys[0]:
            return expected_seq_num

        elif expected_seq_num == list_of_keys[0]:
            sliced = list_of_keys[list_of_keys.index(expected_seq_num)]
            for i in sliced:
                if ()






    if (pkt.seq_num > expected_seq_num):
        return expected_seq_num
    elif (pkt.seq_num == expected_seq_num):
        expected_seq_num = pkt.seq_num + pkt.payload_size()
        return expected_seq_num
    else:
        return expected_seq_num


def add_to_buffer(pkt):
    global receiver_buffer
    list_of_keys = receiver_buffer.keys()
    if pkt.seq_num not in list_of_keys:
        print("adding into buffer", pkt.seq_num)
        receiver_buffer[pkt.seq_num] = pkt.payload

    receiver_buffer = sorted(receiver_buffer) 


# serelize right before sending any packet
def serialize_packet(packet):
    return pickle.dumps(packet)


# desereliaze as soon as we received a packet
def deserialize_packet(packet):
    return pickle.loads(packet)


# writes the file from the buffer
def convertBufferToFile():
    return None

main()
