# COMP3331
# Sender.py acts as the CLIENT
# python sender.py receiver_host_ip receiver_port file.pdf MWS MSS gamma
# pDrop pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed

import socket, sys
from packet import *

############ INITIALIZATION ############

# Grab and check all arguments (14)
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)

# Create a UDP socket (indicated via SOCK_DGRAM)
sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def main():
        with open("test0.pdf", "rb") as fi:
            buf = fi.read(150)
            while (buf):
               sender_socket.sendto(buf, hostport)
               buf = fi.read(150)
main()


