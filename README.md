# Columbia-CSEE-W4119

# Decentralized Voting Blockchain (P2P Network)

This project implements a **decentralized voting system** on a blockchain using a custom peer-to-peer (P2P) protocol over UDP. Peers register with a tracker server, receive a list of peers, and exchange blockchain data to maintain consensus.

---

## 🚀 How to Run

1. To run the application, create a virtual environment using `python3 -m venv venv`
2. Activate the virtual environment. For Mac users: `source venv/bin/activate`
3. Install project dependencies from the root repository. For Mac users: `pip install -r requirements.txt`.

### 1️⃣ Start the tracker server

```bash```
`python tracker_server.py <tracker_port>`

Example:
python tracker_server.py 5000

### 2️⃣ Start multiple peers

Each peer needs:
tracker_port: the port where the tracker is running
local_port: unique port for the peer

```bash```
`python peer.py <tracker_port> <local_port>`

Example (starting 3 peers):
python peer.py 5000 6001
python peer.py 5000 6002
python peer.py 5000 6003

### 3️⃣ Start the client interface (UI)

Run the Streamlit Application. Note that `client_ui.py` contains the UI and `client.py` will serve as the main entry point for the client side application. Run the following command 

```bash```
`streamlit run client.py --server.port <ui_port> --server.address <addr> <peer.py port> <streamlit_ui_port> <addr> <tracker_port> <addr>`.

Example, run the following command for the streamlit UI to be run on port 8080, the application to be run on 8081, and the tracker to be run on port 8000
`streamlit run client.py --server.port 8080 --server.address 127.0.0.1 8081 127.0.0.1 8000 127.0.0.1`


📝 Usage Notes
✅ A peer will:

Register with the tracker
Get a list of other peers
Sync chain with other peers
Submit votes → mine a block locally → broadcast the block

✅ Tracker will:

Maintain peer list
Send heartbeat POKE messages every second to check if peers are alive
Remove peers that fail to respond 3 times

💡 Protocol Messages
| Type            | Description                                      |
| --------------- | ------------------------------------------------ |
| REGISTER_PEER  | Peer asks to join the tracker                    |
| REGISTER_ACK   | Tracker sends back peer list                     |
| UPDATE_PEERS   | Tracker sends updated peer list                  |
| REQUEST_BALLOT | Peer requests voting options                     |
| BALLOT_OPTIONS | Tracker sends voting options                     |
| NEW_BLOCK      | Peer broadcasts a mined block                    |
| REQUEST_CHAIN  | Peer requests full chain from another peer       |
| CHAIN_BLOCK    | Peer sends a block in response to REQUEST\_CHAIN |
| POKE            | Tracker heartbeats to check peer liveness        |
| POKE-ACK        | Peer replies to heartbeat                        |
| LEAVE_PEER     | Peer gracefully leaves the network               |


🏗️ Design Assumptions
✅ Peers store and broadcast individual blocks
✅ Chain sync is block-by-block transfer (rather than entire chain at once) to overcome UDP packet size limit
✅ Tracker does NOT store chain → only peer list

⚠️ Corner Cases / Limitations
Chain sync happens only when fork detected or explicitly requested (no periodic sync)
If multiple peers mine conflicting blocks at same index, the node will trigger a REQUEST_CHAIN and adopt the longest valid chain
If a peer broadcasts a block before syncing latest chain → may result in fork

✅ Key Features
Custom blockchain implementation with proof-of-work
Peer-to-peer messaging over UDP
Tracker server with heartbeat monitoring
Fork detection and chain synchronization
Optional web interface (Streamlit UI)

🙏 Authors
Ian Li
Kevin Li
Gushu Qin

