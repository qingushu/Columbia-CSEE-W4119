import sys
import time
from network_layer.peer import Peer
from client_ui import ClientUi

class Client:
    def __init__(self, client_network_port, client_addr, server_addr, server_port):
        self.peer_port = client_network_port
        self.peer_addr = client_addr
        self.server_addr = server_addr
        self.server_port = server_port

        self.peer = Peer(tracker_port=self.server_port, local_port=self.peer_port)
        self.peer.connect()
        self.peer.listen()
        
        time.sleep(1)  # Give peer time to request and receive ballot

        self.ballot_options = self.peer.voting_options
        self.ui = ClientUi(self)

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python client.py <client_network_port> <client_addr> <server_port> <server_addr>")
        sys.exit(1)

    client_network_port = int(sys.argv[1])
    client_addr = sys.argv[2]  # currently unused but reserved for future
    server_port = int(sys.argv[3])
    server_addr = sys.argv[4]  # currently unused as tracker_host is fixed in peer.py

    client = Client(client_network_port, client_addr, server_addr, server_port)
    client.ui.run_ui()



