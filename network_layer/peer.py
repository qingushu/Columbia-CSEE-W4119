import socket
import threading
import json
import sys
import time
from blockchain_layer.blockchain import Blockchain
from blockchain_layer.transaction import Transaction
from blockchain_layer.blockchain import block_from_dict

from enum import Enum

class PeerState(Enum):
    INIT = 1
    REGISTERING = 2
    CONNECTED = 3
    REQUESTING_BALLOT = 4
    CONNECTED_WITH_BALLOT = 5

class Peer:
    def __init__(self, tracker_addr, tracker_port, local_addr, local_port, client_instance=None):
        self.tracker_addr = tracker_addr   # Fixed tracker host
        self.tracker_port = tracker_port
        
        self.local_addr = local_addr
        self.local_port = local_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_addr, self.local_port))
        self.sock.settimeout(0.5)

        self.peers = set()
        self.client_instance = client_instance # To acccess app APIs
        self.blockchain = []  # A list of blocks (each block contains one vote)
        self.has_registered = False
        self.voting_options = None
        self.blockchain_obj = Blockchain(difficulty=2) # Initialize the blockchain with a difficulty of 2   
        
        self.state = PeerState.INIT

        self.message_handler_thread = threading.Thread(target=self.message_handler, daemon=True)
        self.message_handler_thread.start()

    def message_handler(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "REGISTER_ACK" and self.state == PeerState.REGISTERING:
                    # Register with tracker
                    peer_addresses = message.get("peer_list", [])
                    for p in peer_addresses:
                        # TODO: should ignore itself
                        self.peers.add(p)
                    self.has_registered = True
                    self.state = PeerState.CONNECTED
                    print(f"[Peer] Registered with tracker.")

                elif message_type == "NEW_BLOCK":
                    block = message.get("block")
                    self.handle_new_block(block)

                elif message_type == "REQUEST_CHAIN":
                    self.send_chain(addr)

                elif message_type == "CHAIN_RESPONSE":
                    chain = message.get("chain")
                    self.sync_chain(chain)

                elif message_type == "BALLOT_OPTIONS" and self.state == PeerState.REQUESTING_BALLOT:
                    self.state = PeerState.CONNECTED_WITH_BALLOT
                    print(f"[Peer] Received voting options: {message.get('voting_options')}")
                    self.client_instance.update_ballot(message.get("voting_options",[]))
                
                elif message_type == "UPDATE_PEERS":
                    new_peers = message.get("peer_list", [])
                    # TODO: Should ignore itself
                    self.peers = new_peers

                # TODO: Add new message type where it needs to update peers list

            except socket.timeout:
                if self.state == PeerState.REGISTERING:
                    payload = {"type": "REGISTER_PEER"}
                    self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
                    print("[Peer] Ready for casting ballot")
                elif self.state == PeerState.REQUESTING_BALLOT:
                    payload = {"type": "REQUEST_BALLOT"}
                    self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
                    print("[Peer] Ready for casting ballot")

            except Exception as e:
                print(f"[Peer] Error: {e}")

    def request_ballot_options(self):
        '''
        Application API.

        Blocking until ballot is received.
        Called from applicaiton layer.
        '''
        self.state = PeerState.REQUESTING_BALLOT

        while self.state == PeerState.REQUESTING_BALLOT:
            time.sleep(0.1)

        print("[Peer] Ready for casting ballot")

        return

    def connect(self):
        '''
        Application API. 
        
        Blocking until connected and registered with tracker.
        Changes peer state. Called by application layer
        to initiate connection. 
        '''
        self.state = PeerState.REGISTERING

        while self.state == PeerState.REGISTERING:
            time.sleep(0.1)

        print("[Peer] Registered with tracker.")
        return
    
    def submit_vote(self, vote_transaction):
        '''
        Application API. 
        
        Called by application layer
        to submit ballot.
        '''
        # First → sync with peers to make sure we’re on longest chain
        self.request_chain()
        time.sleep(2)  # wait for responses

        # Proceed to add vote and mine
        self.blockchain_obj.add_new_transaction(vote_transaction)
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

        # NEW FIX: skip if already have a block with same index
        if block_obj.index <= self.blockchain_obj.last_block.index:
            print(f"[Peer] Skipping received block {block_obj.index}, already have block at that index")
            return

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
            "chain": self.blockchain_obj.get_chain_data() 
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

    def sync_chain(self, received_chain):
        new_chain = []
        for block_dict in received_chain:
            new_chain.append(block_from_dict(block_dict))

        if len(new_chain) > len(self.blockchain_obj.chain):
            # validate new chain
            is_valid = self.blockchain_obj.is_valid_chain(new_chain)
            if is_valid:
                self.blockchain_obj.chain = new_chain
                print("[Peer] Synced chain from network (accepted longer valid chain).")
            else:
                print("[Peer] Received invalid chain → ignored.")
        else:
            print("[Peer] Received chain but it’s not longer → ignored.")

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
