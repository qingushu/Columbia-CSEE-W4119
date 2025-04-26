from client_ui import ClientUi
import sys 

# import peer from ...

class Client:
    def __init__(self, client_network_port, client_app_port, client_addr, 
                       server_addr, server_port):
        self.peer = DummyPeer() # TODO: Initialize peer here; using dummy for now
        self.ui = ClientUi(client_app_port, client_addr, self.peer)

# TODO: Note--dummy peer object for testing
class DummyPeer:
    def __init__(self):
        self.options = ['A', 'B', 'C']

if __name__ == '__main__':
    client_network_port = int(sys.argv[1]) # port nubmer for p2p communication
    client_app_port = int(sys.argv[2]) # port nubmer for streamlit web interface
    client_addr = sys.argv[3]
    server_port = int(sys.argv[4])
    server_addr = sys.argv[5]

    # initialize client and ui
    client = Client(client_network_port, client_app_port, client_addr, server_addr, server_port)

    # TODO: Initialize connection
    # client.peer.connect() -> Should register with the tracker
    # client.peer.request_ballot() -> Should request for candidates

    # TODO: For testing purposes, creating a dummy peer. Remove later
    client.ui.run_ui()
    


