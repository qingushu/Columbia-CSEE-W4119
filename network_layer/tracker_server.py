import socket
import threading
import json
import sys

class TrackerServer:
    def __init__(self, host='0.0.0.0', port=5000, ballot_provider=None):
        self.host = host
        self.port = port
        self.peers = {}  # {peer_address: timestamp}
        self.get_ballot_options = ballot_provider
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def initialize(self):
        print(f"[Tracker] Listening on {self.host}:{self.port}")
        self.listen_thread = threading.Thread(target=self.listen_for_peers, daemon=True)
        self.listen_thread.start()
        # threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "REGISTER_PEER":
                    self.peers[addr] = threading.get_native_id()
                    self.send_register_ack(addr)
                    print(f"[Tracker] Registered peer")
                elif message_type == "LEAVE_PEER":
                    if addr in self.peers:
                        del self.peers[addr]
                elif message_type == "REQUEST_BALLOT":
                    self.send_ballot_options(addr)
                    print(f"[Tracker] Sent ballot")
            except Exception as e:
                print(f"[Tracker] Error: {e}")

    def send_register_ack(self, addr):
        peer_list = [f"{ip}:{port}" for (ip, port) in self.peers.keys()]
        payload = {
            "type": "REGISTER_ACK",
            "peer_list": peer_list
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

    def send_ballot_options(self, addr):
        options = self.get_ballot_options() if self.get_ballot_options else []
        payload = {
            "type": "BALLOT_OPTIONS",
            "voting_options": options
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

# Only used when running directly
if __name__ == "__main__":
    def dummy_ballot():
        return ["Alice", "Bob", "Charlie"]

    if len(sys.argv) != 2:
        print("Usage: python tracker_server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    tracker = TrackerServer(host="0.0.0.0", port=port, ballot_provider=dummy_ballot)
    tracker.initialize()

    while True:
        pass
