import sys
import time
import os
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from network_layer.peer import Peer
from client_ui import ClientUi

class Client:
    def __init__(self, client_network_port, client_addr, server_addr, server_port):
        self.peer_port = client_network_port
        self.peer_addr = client_addr
        self.server_addr = server_addr
        self.server_port = server_port

        self.peer = Peer(tracker_addr=server_addr, tracker_port=self.server_port, local_addr=client_addr, local_port=self.peer_port, client_instance=self)
        self.ballot_options = None

        self.ui = ClientUi()
    
    def update_ballot(self, ballot_options):
        self.ballot_options = ballot_options
        
if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python client.py <client_network_port> <client_addr> <server_port> <server_addr>")
        sys.exit(1)

    client_network_port = int(sys.argv[1])
    client_addr = sys.argv[2]
    server_port = int(sys.argv[3])
    server_addr = sys.argv[4]
    
    if 'client' not in st.session_state: # Provide Streamlit UI with a single instance of client
        client = Client(client_network_port, client_addr, server_addr, server_port)
        st.session_state['client'] = client

    st.session_state['client'].peer.connect() # Initiate connection

    while st.session_state['client'].ballot_options == None: # Request ballot until received
        st.session_state['client'].peer.request_ballot_options()
        time.sleep(1)
    
    st.session_state['client'].ui.run_ui() # Run the UI after ballot has been received


    
