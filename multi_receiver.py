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

receiver_buffer = []
CONNECTION_STATE = "CLOSED"


def main():
    # this part always waits for a connection
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    receiver_socket.bind(hostport)
    # always wait for a connection
    # start a new thread if a connection comes
    while True:
        data, address = receiver_socket.recvfrom(4000)
        deserialize = deserialize_packet(data)
        print ("type of thing being received is now", deserialize.get_packet_type())
        thread = threading.Thread(target=handle_connection, args=(deserialize,address))
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
    if pkt:
        newSocket.sendto(pkt, address)

#    # set a time out wait for a response of an ACK (for SYN ACK)
#    newSocket.settimeout(2)
#
#    try:
#        ack, address = threadSock.recvfrom(1000)
#    except:
#        #dw about this till i implement timeout
#        print ("time out reached, resending")


# returns the packet that needs to be sent back, based on what packet is given
def process_packet(pkt):
    seq_num = pkt.get_seq_num()
    ack_num = pkt.get_ack_num()
    pkt_type = pkt.get_packet_type()
    # initial packet sent
    


    if pkt_type == "SYN":
        # create a SYNACK packet to send back
        new_packet = packet("SYNACK", 0,0)
        print ("send a synack packet")
        return new_packet
    # this packet completes the handshake (return nothing?)
    elif pkt_type == "ACK":
        # complete the handshake
        CONNECTION_STATE = "OPEN"
        return None
    # packet should be a data packet
    else:
        new_packet = "yoy"
        return new_packet



# serelize right before sending any packet
def serialize_packet(packet):
    return pickle.dumps(packet)

# desereliaze as soon as we received a packet
def deserialize_packet(packet):
    return pickle.loads(packet)

def new_ACK(seq_num, ack_num):
    return packet("ACK", seq_num , ack_num)

main()





