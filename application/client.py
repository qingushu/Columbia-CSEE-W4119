import sys
import time
import os
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from network_layer.peer import Peer
from client_ui import ClientUi


class Client:
    """
    Client represents the application layer for a peer.
    It initializes a Peer object, stores ballot options, and runs the UI.
    """

    def __init__(self, client_network_port, client_addr, server_addr, server_port):
        """
        Initialize a new Client instance.

        Args:
            client_network_port (int): Local UDP port for this peer.
            client_addr (str): Local IP address of this peer.
            server_addr (str): Tracker server IP address.
            server_port (int): Tracker server port.
        """
        self.peer_port = client_network_port
        self.peer_addr = client_addr
        self.server_addr = server_addr
        self.server_port = server_port

        self.peer = Peer(
            tracker_addr=server_addr,
            tracker_port=self.server_port,
            local_addr=client_addr,
            local_port=self.peer_port,
            client_instance=self
        )
        self.ballot_options = None
        self.ui = ClientUi()

    def update_ballot(self, ballot_options):
        """
        Update the ballot options received from the tracker.

        Args:
            ballot_options (list): List of candidate names/options.
        """
        self.ballot_options = ballot_options


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python client.py <client_network_port> <client_addr> <server_port> <server_addr>")
        sys.exit(1)

    client_network_port = int(sys.argv[1])
    client_addr = sys.argv[2]
    server_port = int(sys.argv[3])
    server_addr = sys.argv[4]

    if 'client' not in st.session_state:
        # Initialize Client and store in Streamlit session state
        client = Client(client_network_port, client_addr, server_addr, server_port)
        st.session_state['client'] = client

        # Perform initial connection once (streamlit reruns code on UI interaction)
        st.session_state['client'].peer.connect()
        st.session_state['client'].peer.request_ballot_options()

    # Run the Streamlit UI
    st.session_state['client'].ui.run_ui()
