import socket
import threading
import json

class TrackerServer:
    def __init__(self, host='0.0.0.0', port=5000, voting_options=None):
        self.host = host
        self.port = port
        self.peers = {}  # {peer_address: timestamp}
        self.voting_options = voting_options or ["Alice", "Bob", "Charlie"]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def initialize(self):
        print(f"[Tracker] Listening on {self.host}:{self.port}")
        threading.Thread(target=self.listen_for_peers, daemon=True).start()

    def listen_for_peers(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "REGISTER_PEER":
                    self.peers[addr] = threading.get_native_id()
                    self.send_register_ack(addr)
                elif message_type == "LEAVE_PEER":
                    if addr in self.peers:
                        del self.peers[addr]
            except Exception as e:
                print(f"[Tracker] Error: {e}")

    def send_register_ack(self, addr):
        peer_list = [f"{ip}:{port}" for (ip, port) in self.peers.keys()]
        payload = {
            "type": "REGISTER_ACK",
            "voting_options": self.voting_options,
            "peer_list": peer_list
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

if __name__ == "__main__":
    tracker = TrackerServer(host="0.0.0.0", port=5000)
    tracker.initialize()

    # Keep main thread alive
    while True:
        pass