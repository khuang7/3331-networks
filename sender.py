# COMP3331
# Sender.py acts as the CLIENT
# python sender.py receiver_host_ip receiver_port file.pdf MWS MSS gamma
# pDrop pDuplicate pCorrupt pOrder maxOrder pDelay maxDelay seed

import socket, sys
from packet import *
import threading



############ INITIALIZATION ############

# Grab and check all arguments (14)
rcv_host_ip = "127.0.0.1"
rcv_port = 5000
hostport = (rcv_host_ip, rcv_port)
timeout = 1000



# Create a UDP socket (indicated via SOCK_DGRAM)
sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def main():
        with open("test0.pdf", "rb") as fi:
            buf = fi.read(150)
            sender_socket.sendto(buf, hostport)
            while (buf):
                print ("sends ", buf)
                sender_socket.sendto(buf, hostport)
                buf = fi.read(150)
        
        # onces it done\
        print ('sends a stop message')
        message = "stop"
        message = message.encode("Latin-1")
        sender_socket.sendto(message, hostport)    


main()


