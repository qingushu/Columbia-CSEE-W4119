import sys

class Server:
    def __init__(self, port, addr, ballot_options_arg):
        self.port:int = port
        self.addr:int = addr
        self.ballot_options: list[str] = self.set_ballot_options(ballot_options_arg) #
        
        # TODO: Initialize tracker here
        # self.tracker = 
    
    def set_ballot_options(self, ballot_options_arg):
        return [option.strip() for option in ballot_options_arg.split(",")]

    def get_ballot_options(self) -> list[str]:
        return self.ballot_options
    
if __name__ == '__main__':

    if len(sys.argv) < 4:
        print("Usage: python server.py <listen_port> <addr> <ballot_options>")
        print("Example: python server.py 9000 127.0.0.1 'Candidate A,Candidate B,Candidate C'")
        sys.exit(1)
    
    listen_port = int(sys.argv[1])
    addr = int(sys.argv[2])
    ballot_options_arg = sys.argv[3] # Example: "John Doe, Tim Cook"

    server = Server(listen_port, addr, ballot_options_arg)
    # Server.tracker.init() # Initialize tracker to start listening for incoming connections
    
    # should containously send ballot_options upon being requests




