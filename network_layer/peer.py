import socket
import threading
import json
import sys
import time
from blockchain_layer.blockchain import Blockchain
from blockchain_layer.transaction import Transaction
from blockchain_layer.blockchain import block_from_dict

class Peer:
    def __init__(self, tracker_addr, tracker_port, local_addr, local_port, client_instance=None):
        self.tracker_addr = tracker_addr   # Fixed tracker host
        self.tracker_port = tracker_port
        self.local_addr = local_addr
        self.local_port = local_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_addr, self.local_port))
        self.peers = set()
        self.client_instance = client_instance
        self.blockchain = []  # A list of blocks (each block contains one vote)
        self.has_registered = False
        self.voting_options = None
        self.blockchain_obj = Blockchain(difficulty=2) # Initialize the blockchain with a difficulty of 2   
        self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listen_thread.start()

    def connect(self):
       # Send register request
        payload = {"type": "REGISTER_PEER"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))

        # Wait for REGISTER_ACK
        while not self.has_registered:
            time.sleep(0.1)

        # Request ballot
        self.request_ballot_options()

        # Wait for ballot
        while self.voting_options is None:
            time.sleep(0.1)

    def listen_for_messages(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")
                if message_type == "REGISTER_ACK":
                    # Register with tracker
                    peer_addresses = message.get("peer_list", [])
                    for p in peer_addresses:
                        self.peers.add(p)
                    self.has_registered = True
                    print(f"[Peer] Registered with tracker.")

                elif message_type == "NEW_BLOCK":
                    block = message.get("block")
                    self.handle_new_block(block)

                elif message_type == "REQUEST_CHAIN":
                    self.send_chain(addr)

                elif message_type == "CHAIN_RESPONSE":
                    chain = message.get("chain")
                    self.sync_chain(chain)

                elif message_type == "BALLOT_OPTIONS":
                    print(f"[Peer] Received voting options: {message.get('voting_options')}")
                    self.client_instance.update_ballot(message.get("voting_options",[]))

                time.sleep(0.01)
            except Exception as e:
                print(f"[Peer] Error: {e}")

    def request_ballot_options(self):
        payload = {"type": "REQUEST_BALLOT"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))

    def submit_vote(self, vote_transaction):
        
        tx_obj = Transaction(
            voter_id=vote_transaction["voter_id"],
            candidate_id=vote_transaction["candidate_id"],
            timestamp=vote_transaction["timestamp"]
        )

        self.blockchain_obj.add_new_transaction(tx_obj)
        mined = self.blockchain_obj.mine_block()

        if mined:
            block_dict = self.blockchain_obj.get_last_block_dict()
            self.broadcast_block(block_dict)

    def broadcast_block(self, block):
        block_message = {
            "type": "NEW_BLOCK",
            "block": block
        }
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(block_message).encode(), (ip, int(port)))

    def handle_new_block(self, block_dict):
        

        block_obj = block_from_dict(block_dict)
        proof = block_obj.hash

        added = self.blockchain_obj.add_block(block_obj, proof)

        if added:
            print("[Peer] Valid block added")
        else:
            print("[Peer] Invalid block, requesting chain sync")
            self.request_chain()

    def validate_block(self, block):
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
        if len(received_chain) > len(self.blockchain):
            self.blockchain = received_chain
            print("[Peer] Synced chain from network.")

    def leave_network(self):
        payload = {"type": "LEAVE_PEER"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_host, self.tracker_port))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python peer.py <tracker_port> <local_port>")
        sys.exit(1)

    tracker_port = int(sys.argv[1])
    local_port = int(sys.argv[2])

    peer = Peer(tracker_port, local_port)
    peer.connect()
    peer.listen()

    # Keep main thread alive
    while True:
        time.sleep(1)
