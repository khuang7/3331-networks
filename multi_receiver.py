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
    
    # CONNECTION TEARDOWN
    elif pkt_type == "FIN":
        CONNECTION_STATE = 0
        # convert receiver buffer to file and output

    # packet should be a data packet
    else:
        if (pkt.seq_num in receiver_buffer.keys()):
            return None  # dont return the packet since we have it already
        else:

            add_to_buffer(pkt)
            # the state of the buffer after every add
            print("added packet, buffer is now", receiver_buffer.keys())

            update_expected_seq_num()
            print ("new expected seq num is", expected_seq_num)
            new_packet = packet("ACK", 1, expected_seq_num)
            new_packet.simple_print()

            return new_packet


# constantly ensures that hte expected seq num is updated
def update_expected_seq_num():
    global receiver_buffer
    global expected_seq_num
    start = 1

    list_of_keys = sorted(receiver_buffer.keys())
    print("determining expected seq num from here", list_of_keys)
    prev = list_of_keys.pop(0)

    # edge case beginning
    if (prev != start):
        expected_seq_num = start

    # after popping the list is empty so it has to be just the next one
    elif (not list_of_keys):
        expected_seq_num = start + 150  # make sure i use payload size here

    # cycle through the whole list till we reach a point
    else:
        for i in list_of_keys:
            curr = i
            if (prev + 150 == curr):
                prev = curr
                continue
            else: 
                expected_seq_num = prev
                return
        # if we get out of this loop
        expected_seq_num = curr + 150


def add_to_buffer(pkt):
    global receiver_buffer

    list_of_keys = receiver_buffer.keys()
    if pkt.seq_num not in list_of_keys:
        print("adding into buffer", pkt.seq_num)
        receiver_buffer[pkt.seq_num] = pkt.payload
        # instead of sorting it here, we sort everytime we check the list

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
