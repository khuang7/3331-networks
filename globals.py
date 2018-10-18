# list of globals to be used in both files

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