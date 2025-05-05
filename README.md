# Columbia-CSEE-W4119

# Decentralized Voting Blockchain (P2P Network)

This project implements a **decentralized voting system** on a blockchain using a custom peer-to-peer (P2P) protocol over UDP. Peers register with a tracker server, receive a list of peers, request ballot with options defined on the server side, and exchange blockchain data to maintain consensus.

---

## Imported Libraries/Frameworks

- **Streamlit (1.44.1)**: Used for creating the application layer UI
- **Watchdog (6.0.0)**: To improve rendering performance of UI

## 🚀 How to Run

1. To run the application, create a virtual environment using `python -m venv venv`
2. Activate the virtual environment. For Mac users: `source venv/bin/activate`
3. Install project dependencies from the root repository. For Mac users: `pip install -r requirements.txt`.
4. Ensure you are in the top-most directory.

### 1️⃣ Start the Tracker-Server via the command line (CLI)

`python application_layer/server.py <tracker_port> <tracker_ip_address> <string_of_comma_separated_ballot_options>`

Example: python server.py 8005 127.0.0.1 'Adam,Bob,Catherine'

The example above will create a server instance containing the ballot options 'Adam', 'Bob', and 'Catherine.' A tracker will also be created. Note that the tracker only stores the list of peers and the application-layer server.py will store the ballot options that tracker.py will access when receiving other client-peers requests.

### 2️⃣ Start the Peers + UI

Run client.py which will serve as the main entry point for the client side application. Each instance will run a peer.

`streamlit run application_layer/client.py --server.port <streamlit_ui_port> --server.address <streamlit_ui_addr> <peer_port> <peer_addr> <tracker_port> <addr>`.

Please note that the separate port and addr required for streamlit_ui is simply for UI rendering and does not interfere with the designed network protocol.

Example, run the following command for the streamlit UI to be run on port 8080, the peer to be run on port 8081, and the tracker to be run on port 8005.

`streamlit run application/client.py --server.port 8080 --server.address 127.0.0.1 8081 127.0.0.1 8005 127.0.0.1`

NOTE: Please do not run CTRL + R in the browser when using the UI. Refreshing like this will NOT work due to Streamlit rendering. Either gracefully terminate the application by clicking on the 'Leave + Terminate' or CTRL + C in the client-running terminal to forcibly disconnect the client, which will cause the tracker to remove it after 3 seconds (as per the implemented heartbeat mechanism).

📝 **Usage Notes**

✅ Client-peer will:

- Register with the tracker
- Get a list of other peers
- Sync chain with other peers (upon initial connection and fork resolution)
- Continuously submit votes → mine a block locally → broadcast the block

✅ Server-tracker will:

- Maintain peer list
- Send heartbeat POKE messages every second to check if peers are alive
- Remove peers that fail to respond 3 times

💡 **Protocol Messages**
| Type | Description |
| --------------- | ------------------------------------------------ |
| REGISTER_PEER | Peer asks to join the tracker |
| REGISTER_ACK | Tracker sends back peer list |
| UPDATE_PEERS | Tracker sends updated peer list |
| REQUEST_BALLOT | Peer requests voting options |
| BALLOT_OPTIONS | Tracker sends voting options |
| NEW_BLOCK | Peer broadcasts a mined block |
| REQUEST_CHAIN | Peer requests full chain from another peer |
| CHAIN_BLOCK | Peer sends a block in response to REQUEST_CHAIN |
| POKE | Tracker heartbeats to check peer liveness |
| POKE-ACK | Peer replies to heartbeat |
| LEAVE_PEER | Peer gracefully leaves the network |

🏗️ **Design**

✅ Peers store and broadcast individual blocks, the block will be propagated once mined.

✅ Other peer receives the block and verifies the previous_hash field for local chain alignment.
- if the block satisfies previous_hash alignment with local chain's last block and has valid PoW, it will be added into local chain with no further actions
- if the block does not satisfy previous_hash:
  - If PoW fails, abort
  - If PoW is satisfies, trigger chain sync

✅ Chain sync is block-by-block transfer (rather than entire chain at once) to overcome UDP packet size limit
- a peer verified the chain for PoW and hash links when syncing.

✅ Tracker does NOT store chain → only peer list

✅ Upon initializing a peer instance in client.py, the application layer will request to be registered with the tracker. Once successfully registered, it will request a ballot. Once a ballot has been received, the streamlit UI will be rendered. If you see the streamlit UI loading but not the interface, this means that the peer was not registered with the tracker or the ballot has not been received. Please check logs to determine the issue.

✅ The network layer has been set up to include blocking connect() and request_ballot() functions to be called by the application layer. If network conditions prevent requests/responses from being successfully delivered, the peer will continue to send requests until it fulfills the request.

✅ **Key Features**

- Custom blockchain implementation with proof-of-work
- Peer-to-peer messaging over UDP
- Tracker server with heartbeat monitoring
- Fork detection and chain synchronization
- Streamlit UI for vote submission and real-time rendering of blockchain and total votes across all peers.

**Authors**

- Ian Li
- Kevin Li
- Gushu Qin
