import socket
import threading
import json
import sys
import time
from enum import Enum
from blockchain_layer.blockchain import Blockchain
from blockchain_layer.transaction import Transaction
from blockchain_layer.blockchain import block_from_dict


class PeerState(Enum):
    """
    Enumeration of the possible states of a Peer.
    """
    INIT = 1
    REGISTERING = 2
    CONNECTED = 3
    REQUESTING_BALLOT = 4
    CONNECTED_WITH_BALLOT = 5


class Peer:
    """
    Represents a peer node in the P2P blockchain voting network.

    Each peer handles:
    - Registering with the tracker
    - Maintaining local blockchain state
    - Submitting votes and mining blocks
    - Broadcasting blocks
    - Receiving and validating blocks
    - Synchronizing blockchain with other peers
    """

    def __init__(self, tracker_addr, tracker_port, local_addr,
                 local_port, client_instance=None):
        """
        Initializes a Peer instance.

        Args:
            tracker_addr (str): IP address of tracker.
            tracker_port (int): Port number of tracker.
            local_addr (str): Local IP address.
            local_port (int): Local port number.
            client_instance (object): Optional reference to UI client.
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
        self.blockchain_obj = Blockchain(difficulty=2)
        self.has_registered = False
        self.voting_options = None
        self.state = PeerState.INIT

        self.message_handler_thread = threading.Thread(
            target=self.message_handler, daemon=True)
        self.message_handler_thread.start()

    def message_handler(self):
        """
        Continuously listens for incoming UDP messages and handles them.
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
                message = json.loads(data.decode())
                message_type = message.get("type")

                if (message_type == "REGISTER_ACK" and
                        self.state == PeerState.REGISTERING):
                    peer_addresses = message.get("peer_list", [])
                    for p in peer_addresses:
                        self.peers.add(p)
                    self.has_registered = True
                    self.state = PeerState.CONNECTED
                    print("[Peer] Registered with tracker.")

                elif message_type == "NEW_BLOCK":
                    block = message.get("block")
                    self.handle_new_block(block)

                elif message_type == "REQUEST_CHAIN":
                    self.send_chain(addr)

                elif message_type == "CHAIN_RESPONSE":
                    chain = message.get("chain")
                    self.sync_chain(chain)

                elif (message_type == "BALLOT_OPTIONS" and
                        self.state == PeerState.REQUESTING_BALLOT):
                    self.state = PeerState.CONNECTED_WITH_BALLOT
                    print(f"[Peer] Received voting options: "
                          f"{message.get('voting_options')}")
                    self.client_instance.update_ballot(
                        message.get("voting_options", []))

                elif message_type == "UPDATE_PEERS":
                    new_peers = message.get("peer_list", [])
                    self.peers = new_peers

            except socket.timeout:
                if self.state == PeerState.REGISTERING:
                    payload = {"type": "REGISTER_PEER"}
                    self.sock.sendto(json.dumps(payload).encode(),
                                     (self.tracker_addr, self.tracker_port))
                    print("[Peer] Retrying registration...")
                elif self.state == PeerState.REQUESTING_BALLOT:
                    payload = {"type": "REQUEST_BALLOT"}
                    self.sock.sendto(json.dumps(payload).encode(),
                                     (self.tracker_addr, self.tracker_port))
                    print("[Peer] Retrying ballot request...")

            except Exception as e:
                print(f"[Peer] Error: {e}")

    def request_ballot_options(self):
        """
        Requests ballot options from tracker and blocks until received.
        """
        self.state = PeerState.REQUESTING_BALLOT
        while self.state == PeerState.REQUESTING_BALLOT:
            time.sleep(0.1)
        print("[Peer] Ready for casting ballot")

    def connect(self):
        """
        Registers peer with tracker and blocks until registration completes.
        """
        self.state = PeerState.REGISTERING
        while self.state == PeerState.REGISTERING:
            time.sleep(0.1)
        print("[Peer] Registered with tracker.")

    def submit_vote(self, vote_transaction):
        """
        Submits a vote transaction, mines a block, and broadcasts it.

        Args:
            vote_transaction (dict): Vote transaction data.
        """
        self.blockchain_obj.add_new_transaction(vote_transaction)
        mined = self.blockchain_obj.mine_block()

        if mined:
            block_dict = self.blockchain_obj.get_last_block_dict()
            self.broadcast_block(block_dict)

    def broadcast_block(self, block):
        """
        Broadcasts a block to all known peers.

        Args:
            block (dict): Dictionary representation of block to broadcast.
        """
        block_message = {"type": "NEW_BLOCK", "block": block}
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(block_message).encode(),
                             (ip, int(port)))

    def handle_new_block(self, block_dict):
        """
        Handles receiving a new block: validate and add to local chain.

        Args:
            block_dict (dict): Received block data.
        """
        block_obj = block_from_dict(block_dict)

        if block_obj.index < len(self.blockchain_obj.chain):
            local_block = self.blockchain_obj.chain[block_obj.index]
            if local_block.hash != block_obj.hash:
                print(f"[Peer] Detected fork at block {block_obj.index}! "
                      f"Requesting chain sync...")
                self.request_chain()
            else:
                print(f"[Peer] Received duplicate block {block_obj.index}, "
                      "ignoring.")
        else:
            proof = block_obj.hash
            added = self.blockchain_obj.add_block(block_obj, proof)
            if added:
                print("[Peer] Valid block added")
            else:
                print("[Peer] Invalid block, requesting chain sync")
                self.request_chain()

    def request_chain(self):
        """
        Requests full blockchain from all known peers.
        """
        payload = {"type": "REQUEST_CHAIN"}
        for peer in self.peers:
            ip, port = peer.split(":")
            self.sock.sendto(json.dumps(payload).encode(),
                             (ip, int(port)))

    def send_chain(self, addr):
        """
        Sends local blockchain to requesting peer.

        Args:
            addr (tuple): Address of requesting peer (IP, port).
        """
        payload = {
            "type": "CHAIN_RESPONSE",
            "chain": self.blockchain_obj.get_chain_data()
        }
        self.sock.sendto(json.dumps(payload).encode(), addr)

    def sync_chain(self, received_chain):
        """
        Syncs local blockchain if received chain is longer.

        Args:
            received_chain (list): Received blockchain data.
        """
        new_chain = [block_from_dict(b) for b in received_chain]
        if len(new_chain) > len(self.blockchain_obj.chain):
            self.blockchain_obj.chain = new_chain
            print("[Peer] Synced chain from network.")

    def leave_network(self):
        """
        Sends LEAVE_PEER notification to tracker.
        """
        payload = {"type": "LEAVE_PEER"}
        self.sock.sendto(json.dumps(payload).encode(),
                         (self.tracker_addr, self.tracker_port))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python peer.py <tracker_port> <local_port>")
        sys.exit(1)

    tracker_port = int(sys.argv[1])
    local_port = int(sys.argv[2])

    peer = Peer(tracker_port, local_port)
    peer.connect()

    while True:
        time.sleep(1)
