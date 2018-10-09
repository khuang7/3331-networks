

"""
import os

def read():
    with open("test0.pdf", "rb") as fi:


        buf = fi.read(150)
        print ("FIRST 150 BYTES")
        print (buf)
        counter = 1
        while (buf):
            counter = counter + 1
            buf = fi.read(150)
            print("NEXT 150 BYTES")
            print (buf)
    print ("NUMBER OF PACKETS = ", counter)
read()


        print(os.path.getsize("test0.pdf"))
"""

from packet import packet

def main():
    pkt = packet("ACK", 100, 200)
    pkt.print_packet_data()

main()