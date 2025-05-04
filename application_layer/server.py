# server.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from network_layer.tracker_server import TrackerServer


class Server:
    """
    Server class initializes and starts the tracker server for the blockchain network.

    This class provides a wrapper around TrackerServer and supplies
    voting options to peers via a ballot provider function.
    """

    def __init__(self, port, addr, ballot_options_arg):
        """
        Initialize a new Server instance.

        Args:
            port (int): Listening port for tracker.
            addr (str): IP address to bind the tracker.
            ballot_options_arg (str): Comma-separated string of ballot candidates.
        """
        self.port: int = port
        self.addr: str = addr
        self.ballot_options: list[str] = self.set_ballot_options(ballot_options_arg)
        self.tracker = TrackerServer(
            host=addr,
            port=port,
            ballot_provider=self.get_ballot_options
        )

    def set_ballot_options(self, ballot_options_arg):
        """
        Parse the input string of ballot options into a list.

        Args:
            ballot_options_arg (str): Comma-separated candidate names.

        Returns:
            list: A list of candidate names.
        """
        return [option.strip() for option in ballot_options_arg.split(",")]

    def get_ballot_options(self) -> list[str]:
        """
        Return the list of ballot options.

        Returns:
            list: The list of candidate names.
        """
        return self.ballot_options

    def start(self):
        """
        Start the tracker server to listen for incoming peer connections.
        """
        print(f"[Server] Starting tracker on {self.addr}:{self.port}")
        self.tracker.initialize()


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python server.py <listen_port> <addr> <ballot_options>")
        print("Example: python server.py 9000 127.0.0.1 'Candidate A,Candidate B,Candidate C'")
        sys.exit(1)

    listen_port = int(sys.argv[1])
    addr = sys.argv[2]
    ballot_options_arg = sys.argv[3]

    server = Server(listen_port, addr, ballot_options_arg)
    server.start()

    # Keep the main thread alive
    while True:
        pass




