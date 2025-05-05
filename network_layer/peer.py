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
    LEAVING = 6
    CLOSED = 7

class Peer:
    def __init__(self, tracker_addr, tracker_port, local_addr, local_port, client_instance):
        """ 
        Initializes a Peer instance.

        Args:
            tracker_addr (str): IP address of the tracker server.
            tracker_port (int): Port of the tracker server.
            local_addr (str): Local IP address of this peer.
            local_port (int): Local port for this peer to bind.
            client_instance: Reference to the client UI/application layer.
        """
        self.tracker_addr = tracker_addr
        self.tracker_port = tracker_port
        self.local_addr = local_addr
        self.local_port = local_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.local_addr, self.local_port))
        self.sock.settimeout(0.5)

        self.peers = set()
        self.client_instance = client_instance
        self.blockchain = []
        self.has_registered = False
        self.voting_options = None
        self.blockchain_obj = Blockchain(difficulty=2)
        self.state = PeerState.INIT
        self.temp_chain = {}
        self.temp_total_blocks = None

        self.message_handler_thread = threading.Thread(target=self.message_handler, daemon=True)
        self.message_handler_thread.start()

        self.broadcasting_and_listening_enabled = True

    def message_handler(self):
        """
        Listens for incoming UDP messages and handles them according to message type.
        This method runs in a dedicated thread.
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if message_type == "POKE": # Move POKE condition here to enable continued heartbeat response for fork demonstration
                    self.heartbeat_response()

                if not self.broadcasting_and_listening_enabled:
                    continue

                if message_type == "REGISTER_ACK" and self.state == PeerState.REGISTERING:
                    peer_addresses = message.get("peer_list", [])
                    self.peers = {p for p in peer_addresses if p != f"{self.local_addr}:{self.local_port}"}
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
                    self.peers = {p for p in new_peers if p != f"{self.local_addr}:{self.local_port}"}
                    print(f"[Peer] Updated peer list: {self.peers}")

                elif message_type == "CHAIN_BLOCK":
                    block_dict = message["block"]
                    index = message["index"]
                    total_blocks = message["total_blocks"]
                    self.temp_chain[index] = block_from_dict(block_dict)
                    self.temp_total_blocks = total_blocks
                    print(f"[Peer] Received block {index}/{total_blocks - 1}")
                    if len(self.temp_chain) == self.temp_total_blocks:
                        new_chain = [self.temp_chain[i] for i in sorted(self.temp_chain.keys())]

                        if self.blockchain_obj.is_valid_chain(new_chain) and len(new_chain) > len(self.blockchain_obj.chain):
                            self.blockchain_obj.chain = new_chain
                            print("[Peer] Chain synced from peer (valid chain accepted).")
                        else:
                            print("[Peer] Received chain is invalid or not longer → rejected.")

                        self.temp_chain.clear()
                        self.temp_total_blocks = None
            except socket.timeout:
                if self.state == PeerState.REGISTERING:
                    payload = {"type": "REGISTER_PEER"}
                    self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
                    print("[Peer] Sent request to register with tracker...")
                elif self.state == PeerState.REQUESTING_BALLOT:
                    payload = {"type": "REQUEST_BALLOT"}
                    self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
                    print("[Peer] Sent ballot request to tracker...")
            except Exception as e:
                print(f"[Peer] Error: {e}")

    def request_ballot_options(self):
        """
        Sends a request for ballot options to the tracker.
        Blocks until ballot options are received.
        """
        self.state = PeerState.REQUESTING_BALLOT
        while self.state == PeerState.REQUESTING_BALLOT:
            time.sleep(0.1)
        print("[Peer] Ready for casting ballot")

    def connect(self):
        """
        Connects the peer to the tracker and requests chain synchronization.
        Blocks until registration is acknowledged.
        """
        self.state = PeerState.REGISTERING
        while self.state == PeerState.REGISTERING:
            time.sleep(0.1)
        self.request_chain()
        print("[Peer] Registered with tracker.")

    def submit_vote(self, vote_transaction):
        """
        Submits a new vote transaction, mines it into a block, and broadcasts the block.

        Args:
            vote_transaction (Transaction): The vote transaction to be mined.
        """
        
        self.blockchain_obj.add_new_transaction(vote_transaction)
        print("[Peer] Adding transaction to new block and initiating mining...")
        mined = self.blockchain_obj.mine_block()
        if mined:
            print("[Peer] Successfully mined newly added block.")
            block_dict = self.blockchain_obj.get_last_block_dict()
            self.broadcast_block(block_dict)

    def leave_network(self):
        """
        Leaves the network by notifying the tracker.
        """
        payload = {"type": "LEAVE_PEER"}
        self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
        self.state = PeerState.CLOSED
        print("[Peer] Sent LEAVE_PEER to tracker. Closing peer...")

    def broadcast_block(self, block):
        """
        Broadcasts a newly mined block to all known peers.

        Args:
            block (dict): The block to broadcast (in dict form).
        """
        if not self.broadcasting_and_listening_enabled:
            print("[Peer] Broadcasting is disabled. Skipping broadcast.")
            return
        block_message = {"type": "NEW_BLOCK", "block": block}
        print(f"[Peer] Broadcasting to {self.peers}")
        for peer in self.peers:
            try:
                ip, port = peer.split(":")
                port = int(port)
                self.sock.sendto(json.dumps(block_message).encode(), (ip, port))
                print(f"[Peer] Broadcasted block to {ip}:{port}")
            except Exception as e:
                print(f"[Peer] Failed to broadcast to {peer}: {e}")

    def handle_new_block(self, block_dict):
        """
        Handles an incoming NEW_BLOCK message by validating and adding the block.
        If a fork is detected, requests chain sync.

        Args:
            block_dict (dict): The received block as a dictionary.
        """
        block_obj = block_from_dict(block_dict)
        if block_obj.index < len(self.blockchain_obj.chain):
            local_block = self.blockchain_obj.chain[block_obj.index]
            if local_block.hash != block_obj.hash:
                print(f"[Peer] Detected fork at block {block_obj.index}! Requesting chain sync...")
                self.request_chain()
            else:
                print(f"[Peer] Received duplicate block {block_obj.index}, ignoring.")
        proof = block_obj.hash
        added = self.blockchain_obj.add_block(block_obj, proof)
        if added:
            print("[Peer] Valid block added")
        else:
            print("[Peer] Invalid block, requesting chain sync")
            self.request_chain()

    def validate_block(self, block):
        """
        Validates a block's linkage to the last known block.

        Args:
            block (dict): The block to validate.

        Returns:
            bool: True if valid linkage; False otherwise.
        """
        if not self.blockchain:
            return True
        last_block = self.blockchain[-1]
        return block["previous_hash"] == last_block["hash"]

    def request_chain(self):
        """
        Sends a REQUEST_CHAIN message to all peers to initiate chain synchronization.
        """
        payload = {"type": "REQUEST_CHAIN"}
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(payload).encode(), (ip, int(port)))

    def send_chain(self, addr):
        """
        Sends the entire blockchain to a requesting peer, block by block.

        Args:
            addr (tuple): Address of the requesting peer.
        """
        total_blocks = len(self.blockchain_obj.chain)
        for i, block in enumerate(self.blockchain_obj.chain):
            payload = {"type": "CHAIN_BLOCK", "index": i, "block": self.block_to_dict(block), "total_blocks": total_blocks}
            self.sock.sendto(json.dumps(payload).encode(), addr)

    def block_to_dict(self, block):
        """
        Converts a Block object to a dictionary representation.

        Args:
            block (Block): The block to convert.

        Returns:
            dict: The block as a dictionary.
        """
        return {
            'index': block.index,
            'transactions': [tx.to_dict() for tx in block.transactions],
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash
        }

    def sync_chain(self, received_chain):
        """
        Syncs the local chain with a received chain if it's longer and valid.

        Args:
            received_chain (list): List of block dictionaries representing the received chain.
        """
        new_chain = []
        for block_dict in received_chain:
            new_chain.append(block_from_dict(block_dict))
        if len(new_chain) > len(self.blockchain_obj.chain):
            is_valid = self.blockchain_obj.is_valid_chain(new_chain)
            if is_valid:
                self.blockchain_obj.chain = new_chain
                print("[Peer] Synced chain from network (accepted longer valid chain).")
            else:
                print("[Peer] Received invalid chain → ignored.")
        else:
            print("[Peer] Received chain but it’s not longer → ignored.")

    def heartbeat_response(self):
        """
        Sends a POKE-ACK response to the tracker.
        """
        payload = {"type": "POKE-ACK"}
        try:
            self.sock.sendto(json.dumps(payload).encode(), (self.tracker_addr, self.tracker_port))
            print(f"[Peer] Sent POKE-ACK to tracker at {self.tracker_addr}:{self.tracker_port}")
        except Exception as e:
            print(f"[Peer] Failed to send POKE-ACK to tracker: {e}")

    def set_broadcasting_and_listening(self, enable):
        """
        Enables or disables broadcasting and listening for demo/testing purposes.

        Args:
            enable (bool): True to enable; False to disable.
        """
        self.broadcasting_and_listening_enabled = enable
        if enable:
            print("[Peer] Broadcasting and listening enabled.")
        else:
            print("[Peer] Broadcasting and listening disabled.")

    def add_malicious_block_and_broadcast(self):
        """
        Adds a malicious block to the chain and broadcasts it (for demo purposes).
        """
        malicious_transaction = Transaction("malicious_voter", "malicious_candidate")
        self.blockchain_obj.add_new_transaction(malicious_transaction)
        self.blockchain_obj.mine_malicious_block()
        malicious_block = self.blockchain_obj.last_block
        print("[Peer] Added and mined malicious block to local blockchain")
        print(f"[Peer] Malicious block index: {malicious_block.index}, previous_hash: {malicious_block.previous_hash}")
        malicious_block_dict = self.blockchain_obj.get_last_block_dict()
        self.broadcast_block(malicious_block_dict)
        print("[Peer] Broadcasted malicious block.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python peer.py <tracker_port> <local_port>")
        sys.exit(1)

    tracker_port = int(sys.argv[1])
    local_port = int(sys.argv[2])
    peer = Peer(tracker_port, local_port)
    peer.connect()
    peer.listen()
    while True:
        time.sleep(1)