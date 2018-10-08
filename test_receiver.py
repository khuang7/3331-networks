# COMP3331
# Receiver.py acts as the SERVER
# python receiver.py receiver_port file_r.pdf

import socket, sys, pickle
from packet import *

# variable inputs
IP_ADDRESS = "127.0.0.1"
rcv_port = 5000

TCP_STATE = CLOSED

def main():

    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    receiver_socket.bind((IP_ADDRESS, rcv_port))

    print ("Server is ready to receive")


    f = open("out.pdf", "w")
    f.write("test")

    while True:
        # everytime we reach a message
        message, clientAddress = receiver_socket.recvfrom(2048)
        print("type is", type(message))
        print (message.decode('latin-1').encode("utf-8").decode("utf-8"))




        
main()


