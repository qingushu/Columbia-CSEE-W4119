import socket
import threading
import json

class Peer:
    def __init__(self, tracker_host, tracker_port, local_port):
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.local_host = '0.0.0.0'
        self.local_port = local_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_host, self.local_port))
        self.peers = set()
        self.voting_options = []
        self.blockchain = []  # A list of blocks (each block contains one vote)

    def connect(self):
        payload = {"type": "REGISTER_PEER"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_host, self.tracker_port))
        data, _ = self.sock.recvfrom(4096)
        message = json.loads(data.decode())
        if message.get("type") == "REGISTER_ACK":
            self.voting_options = message["voting_options"]
            peer_addresses = message.get("peer_list", [])
            for p in peer_addresses:
                self.peers.add(p)
            print(f"[Peer] Voting options: {self.voting_options}")
            print(f"[Peer] Current peers: {self.peers}")

    def listen(self):
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "NEW_BLOCK":
                    block = message.get("block")
                    self.handle_new_block(block)
                elif message_type == "REQUEST_CHAIN":
                    self.send_chain(addr)
                elif message_type == "CHAIN_RESPONSE":
                    chain = message.get("chain")
                    self.sync_chain(chain)
            except Exception as e:
                print(f"[Peer] Error: {e}")

    def submit_vote(self, vote_transaction, mining_function):
        # Mine a new block immediately with the vote
        new_block = mining_function(vote_transaction, self.blockchain)
        if new_block:
            self.blockchain.append(new_block)
            self.broadcast_block(new_block)

    def broadcast_block(self, block):
        block_message = {
            "type": "NEW_BLOCK",
            "block": block
        }
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(block_message).encode(), (ip, int(port)))

    def handle_new_block(self, block):
        # Validate and add the block if it extends our chain correctly
        if self.validate_block(block):
            self.blockchain.append(block)
            print(f"[Peer] New valid block added: {block}")
        else:
            print("[Peer] Received invalid block, requesting full chain sync...")
            self.request_chain()

    def validate_block(self, block):
        # Basic validation: Check previous_hash matches last block's hash
        if not self.blockchain:
            return True
        last_block = self.blockchain[-1]
        return block["previous_hash"] == last_block["hash"]

    def request_chain(self):
        payload = {"type": "REQUEST_CHAIN"}
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(payload).encode(), (ip, int(port)))

    def send_chain(self, addr):
        payload = {
            "type": "CHAIN_RESPONSE",
            "chain": self.blockchain
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

    def sync_chain(self, received_chain):
        # Accept the chain if it is longer and valid
        if len(received_chain) > len(self.blockchain):
            self.blockchain = received_chain
            print("[Peer] Synced chain from network.")

    def leave_network(self):
        payload = {"type": "LEAVE_PEER"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_host, self.tracker_port))

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python peer.py <tracker_host> <tracker_port> <local_port>")
        sys.exit(1)

    tracker_host = sys.argv[1]
    tracker_port = int(sys.argv[2])
    local_port = int(sys.argv[3])

    peer = Peer(tracker_host, tracker_port, local_port)
    peer.connect()
    peer.listen()

    # Keep main thread alive
    while True:
        pass
