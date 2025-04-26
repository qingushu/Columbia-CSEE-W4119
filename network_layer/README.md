Decentralized Voting System (Blockchain Final Project)
Team No. 22
Team Members: Kevin Li, Ian Li, Gushu Qin

📚 Overview
This project implements a Decentralized Voting System using a simplified blockchain and a peer-to-peer (P2P) network.
Each node (peer) can independently submit votes, mine blocks, validate blocks from others, resolve forks, and maintain a local copy of the blockchain — without trusting any other node.

Key features:

No centralized server.
Each block contains exactly one vote transaction.
Forks are resolved using the longest valid chain rule.
UDP sockets used for peer-to-peer communication.
Tracker node manages peer registration and peer discovery.

File/Module | Purpose
tracker_server.py | Tracker server that registers peers and shares voting options and peer list
peer.py | Peer node class that handles network messages, vote submission, mining, and blockchain maintenance
block.py (planned) | Defines block structure and mining logic (PoW)
blockchain.py (planned) | Blockchain management, validation, and fork resolution
transaction.py (planned) | Defines the vote transaction object
client.py (planned) | Launches a peer client
server.py (planned) | Launches the tracker server
client_ui.py (optional) | (Optional) Front-end UI for submitting votes

🚀 How to Run
1. Set Up Google Cloud VMs
Set up at least 4 VMs (1 for Tracker + 3 Peers).
Make sure UDP traffic is allowed in firewall settings.
Install Python 3 on each VM.

2. Launch the Tracker Node
SSH into the Tracker VM:
python3 tracker_server.py
This starts the tracker, which listens for incoming peer registration.
Default UDP port: 5000

3. Launch Peer Nodes
SSH into each Peer VM:
python3 peer.py
(Or through a client script like client.py which will initialize Peer instances)

Each peer will:
Connect to the tracker via UDP.
Fetch the list of other peers and voting options.
Start listening for incoming UDP messages.

4. Submit a Vote
Each peer can submit a vote by calling:
peer_instance.submit_vote(vote_transaction, mining_function)
Voting triggers immediate mining of a new block containing that vote.
After mining, the peer broadcasts the new block to other peers.

5. Blockchain Synchronization
If a peer detects an invalid block or falls behind, it automatically requests the latest chain from the network.
Forks are resolved by adopting the longest valid chain.

🔥 Message Types
REGISTER_PEER — Peer -> Tracker: Request to join network.
REGISTER_ACK — Tracker -> Peer: Sends voting options and current peer list.
LEAVE_PEER — Peer -> Tracker: Inform tracker on leaving.
NEW_BLOCK — Peer -> Peers: Broadcast a newly mined block.
REQUEST_CHAIN — Peer -> Peers: Request full blockchain for sync.
CHAIN_RESPONSE — Peer -> Peer: Send current blockchain to requesting peer.

📦 Requirements
Python 3.8+

Libraries:
socket
threading
json
hashlib

📊 Example Workflow
Tracker starts.
Peer 1, Peer 2, Peer 3 start and register.
Peer 1 submits a vote for Candidate A → mines block → broadcasts new block.
Peer 2 and Peer 3 receive the new block → validate → add to their blockchain.
Peer 2 submits a vote for Candidate B → mines → broadcasts → and so on.
All peers maintain an independently growing blockchain that stays consistent across the network!

🧠 Notes
No predefined genesis block: the first block is created when the first vote is submitted.
Immediate mining after vote creation simplifies transaction handling.
Designed to run on Google Cloud VMs for a distributed setup demonstration.
All communication happens over UDP for simplicity and reduced overhead.


