import socket
import threading
import json
import sys
import time

HEARTBEAT_INTERVAL = 1
HEARTBEAT_TIMEOUT_COUNT = 3


class TrackerServer:
    """
    TrackerServer coordinates peer registration, maintains peer list,
    sends heartbeat messages, and manages ballot distribution.
    """

    def __init__(self, host='0.0.0.0', port=5000, ballot_provider=None):
        """
        Initialize the tracker server.

        Args:
            host (str): Host address to bind.
            port (int): UDP port to listen on.
            ballot_provider (function): Function that returns voting options.
        """
        self.host = host
        self.port = port
        self.peers = {}  # {peer_address: thread_id}
        self.get_ballot_options = ballot_provider
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(0.1)  # Prevent blocking for heartbeat checks

        self.sock_lock = threading.Lock()
        self.peers_lock = threading.Lock()
        self.peers_heartbeat_tracker_lock = threading.Lock()
        self.peers_heartbeat_tracker = {}

    def initialize(self):
        """Start the tracker server threads for listening and heartbeats."""
        print(f"[Tracker] Listening on {self.host}:{self.port}")
        self.listen_thread = threading.Thread(target=self.listen_for_peers, daemon=True)
        self.listen_thread.start()

        self.heartbeat_tracker_thread = threading.Thread(target=self.send_heartbeats, daemon=True)
        self.heartbeat_tracker_thread.start()

    def listen_for_peers(self):
        """
        Listen for incoming UDP messages from peers and handle them.
        Handles registration, leave requests, ballot requests, and heartbeat acknowledgments.
        """
        while True:
            try:
                with self.sock_lock:
                    data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "REGISTER_PEER":
                    with self.peers_lock:
                        self.peers[addr] = threading.get_native_id()
                    self.send_register_ack(addr)
                    print(f"[Tracker] Registered peer {addr[0]}:{addr[1]}")

                    self.broadcast_updated_peers_list()
                    print("[Tracker] Broadcasted updated peers list.")

                elif message_type == "LEAVE_PEER":
                    with self.peers_lock:
                        if addr in self.peers:
                            del self.peers[addr]
                            current_peers = [
                                f"{peer[0]}:{peer[1]}" for peer in self.peers.keys()
                            ]
                            print(f"[Tracker] Removed {addr}. Peers: {', '.join(current_peers)}")
                        else:
                            print(f"[Tracker] Ignored LEAVE_PEER from unknown {addr}")

                elif message_type == "REQUEST_BALLOT":
                    if addr not in self.peers:
                        print(f"[Tracker] Rejected REQUEST_BALLOT from unregistered {addr}")
                        continue
                    self.send_ballot_options(addr)
                    print(f"[Tracker] Sent ballot options to {addr}")

                elif message_type == "POKE-ACK":
                    with self.peers_heartbeat_tracker_lock:
                        if addr in self.peers_heartbeat_tracker:
                            self.peers_heartbeat_tracker[addr] = 0
                    print(f"[Tracker] Received POKE-ACK from {addr}")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Tracker] Error: {e}")

    def send_register_ack(self, addr):
        """
        Send a REGISTER_ACK message with the peer list to the specified address.

        Args:
            addr (tuple): (IP, port) of peer.
        """
        peer_list = [f"{ip}:{port}" for (ip, port) in self.peers.keys()]
        payload = {"type": "REGISTER_ACK", "peer_list": peer_list}
        with self.sock_lock:
            self.sock.sendto(json.dumps(payload).encode(), addr)

    def send_ballot_options(self, addr):
        """
        Send ballot options to a peer.

        Args:
            addr (tuple): (IP, port) of peer.
        """
        options = self.get_ballot_options() if self.get_ballot_options else []
        payload = {"type": "BALLOT_OPTIONS", "voting_options": options}
        with self.sock_lock:
            self.sock.sendto(json.dumps(payload).encode(), addr)

    def broadcast_updated_peers_list(self):
        """Broadcast the updated peer list to all registered peers."""
        peer_list = [f"{ip}:{port}" for (ip, port) in self.peers.keys()]
        payload = {"type": "UPDATE_PEERS", "peer_list": peer_list}

        for peer_addr in self.peers.keys():
            try:
                with self.sock_lock:
                    self.sock.sendto(json.dumps(payload).encode(), peer_addr)
                print(f"[Tracker] Sent updated peer list to {peer_addr[0]}:{peer_addr[1]}")
            except Exception as e:
                print(f"[Tracker] Failed to send peer list to {peer_addr}: {e}")

    def send_heartbeats(self):
        """
        Periodically send heartbeat (POKE) messages to peers.
        Remove peers not responding within HEARTBEAT_TIMEOUT_COUNT intervals.
        """
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            payload = {"type": "POKE"}

            with self.peers_heartbeat_tracker_lock, self.peers_lock:
                for peer_addr in self.peers.keys():
                    try:
                        with self.sock_lock:
                            self.sock.sendto(json.dumps(payload).encode(), peer_addr)
                        print(f"[Tracker] Sent POKE to {peer_addr[0]}:{peer_addr[1]}")

                        if peer_addr not in self.peers_heartbeat_tracker:
                            self.peers_heartbeat_tracker[peer_addr] = 1
                        else:
                            self.peers_heartbeat_tracker[peer_addr] += 1
                    except Exception as e:
                        print(f"[Tracker] Failed to send POKE to {peer_addr}: {e}")

            timed_out_peers = []
            with self.peers_heartbeat_tracker_lock:
                for peer, count in self.peers_heartbeat_tracker.items():
                    if count >= HEARTBEAT_TIMEOUT_COUNT:
                        timed_out_peers.append(peer)

            for peer in timed_out_peers:
                with self.peers_lock:
                    del self.peers[peer]
                self.peers_heartbeat_tracker.pop(peer, None)
                print(f"[Tracker] Removed {peer[0]}:{peer[1]} (heartbeat timeout)")

            if timed_out_peers:
                self.broadcast_updated_peers_list()


if __name__ == "__main__":
    def dummy_ballot():
        """Return example ballot options."""
        return ["Alice", "Bob", "Charlie"]

    if len(sys.argv) != 2:
        print("Usage: python tracker_server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    tracker = TrackerServer(host="0.0.0.0", port=port, ballot_provider=dummy_ballot)
    tracker.initialize()

    while True:
        pass
