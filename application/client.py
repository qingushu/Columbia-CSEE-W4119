from client_ui import ClientUi
import sys 

# import peer from ...

class Client:
    def __init__(self, client_network_port, client_addr, 
                       server_addr, server_port):
        self.peer = None
        self.blockchain = None
        self.ballot_options = ['A', 'B', 'C'] # Dummy for testing. TODO: Change to None
        self.ui = ClientUi(client_network_port, client_addr, self.ballot_options, self.blockchain)

if __name__ == '__main__':
    client_network_port = int(sys.argv[1]) # port nubmer for p2p communication
    client_addr = sys.argv[2]
    server_port = int(sys.argv[3])
    server_addr = sys.argv[4]

    # initialize client and ui
    client = Client(client_network_port, client_addr, server_addr, server_port)
    
    # TODO: Initialize connection
    # client.peer.connect() -> Should register with the tracker
    # self.ballot_options = client.peer.request_ballot() -> Should request for candidates

    # TODO: For testing purposes, creating a dummy peer. Remove later
    client.ui.run_ui()
    


