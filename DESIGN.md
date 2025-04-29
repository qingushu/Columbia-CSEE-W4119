# DESIGN.md

**Team No. 22**  
**Team Members:** Kevin Li, Ian Li, Gushu Qin

## 1. Overview
This project implements a simplified blockchain-based **Decentralized Voting System** using a peer-to-peer (P2P) architecture. The blockchain enables a group of nodes to reach consensus on voting results without a centralized authority. Each peer maintains a local copy of the blockchain, validates transactions (votes), mines blocks, handles forks, detects and rejects invalid blocks, and communicates with other peers in the network.

The system includes a tracker to manage peer discovery and a network of at least 3 peers running on Google Cloud VMs. The blockchain ensures tamper resistance, vote integrity, and transparency of the election process.

---

## 2. Blockchain Design

### 2.1 Block Structure
Each block includes:
- `index`: Position in the chain
- `timestamp`: UTC time of block creation
- `transactions`: List of vote transactions
- `previous_hash`: Hash of the previous block
- `nonce`: Used in Proof-of-Work mining
- `hash`: SHA-256 hash of the block contents

### 2.2 Mining & Consensus
- **Consensus Algorithm:** Proof of Work (PoW) with adjustable difficulty.
- **Mining Process:** When a peer submits a vote, it immediately initiates mining a block containing that vote. Each block only contains one vote transaction. This design eliminates the need for a global transaction pool and allows easier testing.
- **Fork Resolution:** If two blocks are mined concurrently, the network may temporarily split. Peers resolve forks by adopting the longest valid chain, discarding shorter branches.
- **Malicious Block Handling:** Each node validates every received block to ensure it matches the expected hash, satisfies PoW, and links to the known chain. Invalid or tampered blocks are rejected.

### 2.3 Chain Initialization
- The blockchain starts empty. There is no predefined genesis block.
- The first peer to join and register with the tracker begins the chain by submitting and mining the first vote.

---

## 3. Peer-to-Peer Protocol

### 3.1 Tracker Node
- Acts as a coordination service to track active peers.
- Maintains an up-to-date list of active peers (IP and port).
- Peers register on join and deregister on leave.
- Sends updated peer lists to newly joining nodes.

### 3.2 Peer Node Responsibilities
Each peer:
- Registers with the tracker and receives the peer list.
- Maintains a local copy of the blockchain.
- Submits and stores new votes.
- Mines a block **immediately upon vote submission** (no transaction pool).
- Verifies and adds received blocks.
- Rejects invalid or tampered blocks.
- Broadcasts newly mined blocks.
- Resolves forks using the longest chain rule.

### 3.3 Communication
- Implemented using UDP sockets.
- JSON is used for message formatting.
- Message types include:
  - `NEW_VOTE`: Sent by a peer to submit a new vote and trigger mining.
  - `NEW_BLOCK`: Broadcast a newly mined block.
  - `REQUEST_CHAIN`: Request full chain sync from a peer.
  - `REGISTER_PEER`: Sent to the tracker to register.
- Peers bind to local UDP ports and handle async messages from the tracker and other peers.

---

## 4. Demo Application: Decentralized Voting System

### 4.1 Features
- Voters submit votes which are mined into blocks immediately.
- Each block contains a single vote transaction.
- Blockchain is updated and broadcast after mining.
- Each peer tallies votes independently based on its local blockchain.
- Forks are resolved using the longest chain policy.

### 4.2 Full Voting Workflow

1. **Tracker Initialization:**
   - The tracker node starts and listens on a fixed UDP port.
   - It maintains a dynamic list of active peers by handling `REGISTER_PEER` and `LEAVE_PEER` messages.

2. **Peer Registration and Startup:**
   - When a peer boots, it sends a `REGISTER_PEER` message to the tracker.
   - The tracker responds with the current list of active peers.
   - The peer then syncs its chain (if any) using `REQUEST_CHAIN` messages to existing peers.

3. **Vote Submission:**
   - Each peer is both a voter and a miner. Upon deciding on a vote, the peer constructs a `NEW_VOTE` transaction locally.
   - The vote is validated and triggers immediate mining of a new block containing that vote.
   - *Redundancy found in vote validation and truning vote into a transaction.*

4. **Block Mining:**
   - The peer runs the PoW algorithm to find a valid nonce.
   - Once the block is mined, it is appended to the local blockchain.
   - A `NEW_BLOCK` message is broadcast to all known peers.

5. **Block Propagation and Validation:**
   - Peers receiving a `NEW_BLOCK` message verify the block’s validity (hash, nonce, previous hash).
   - If valid, the block is added to the local blockchain.
   - If it creates a fork, the peer uses the longest chain rule to resolve it.
   - Invalid or tampered blocks are rejected.

6. **Result Tallying:**
   - Peers can be queried (via CLI/UI) for the current voting results.
   - The vote count is computed by scanning the local blockchain and aggregating candidate IDs.
   - As all nodes maintain the same valid blockchain, each node independently computes the correct result. There is no need to query other peers.

7. **Resilience:**
   - In case a peer falls behind or restarts, it can request the full chain using `REQUEST_CHAIN`.
   - Forks due to concurrent mining are resolved automatically via the longest chain rule.


---

## 5. Code Structure & Module Responsibilities

### High-Level Design

- `block.py`: Defines the Block class and its hashing/mining logic.
- `blockchain.py`: Manages the chain of blocks, mining, validation, and fork resolution.
- `transaction.py`: Defines a Vote transaction structure (voter_id, candidate_id, timestamp).
- `tracker_server.py`: Maintains the active peer list and shares it with joining peers.
- `peer.py`: Represents a peer node. Handles blockchain state, networking, vote submission, mining, and message broadcasting and retrival of voting results.
- `merkletree.py`: Supports efficient block verification if multiple transactions per block are implemented.
- `voting_api.py`: Flask-based HTTP interface for vote submission and result querying (optional for demo).

### Application Flow

1. A peer creates a vote transaction.
2. The peer immediately mines a block with that single vote using PoW.
3. The block is broadcast to all other peers.
4. Peers validate the block and append it if valid.
5. Each peer independently tallies results by reading from its own chain.

---

## 6. Work Division

### Person 1: Blockchain Layer + Testing and integration

- `block.py`: Block structure, hash computation, PoW logic. Potential attributes and methods:
  - `index`: int
  - `timestamp`: str
  - `transactions`: List[Transaction]
  - `previous_hash`:str
  - `nonce`: int
  - `hash`: str
  - `compute_hash()`
- `blockchain.py`: Manages the chain of blocks, mining, validation, fork resolution, and vote tallying. Attributes and methods:
  - `chain`: List[Block] - Stores blocks as a list but can traverse as a linked list using previous_hash attributes
  - `difficulty`: int - Number of leading 0s required for valid hash
  - `orphan_blocks`: dict - Stores blocks that can't be immediately added (parent unknown)
  - `known_block_hashes`: set - Tracks all block hashes to avoid redundant processing
  
  Key methods:
  - `add_block()` - Validates and adds a block to the chain
  - `mine_block()` - Creates and mines a new block with given transactions
  - `is_valid_proof()` - Verifies block hash satisfies difficulty requirement
  - `is_valid_chain()` - Validates entire blockchain for integrity
  - `consensus()` - Implements longest chain rule for fork resolution
  - `_process_orphans()` - Connects orphaned blocks when their parent arrives
  - `_handle_fork()` - Manages chain reorganization when longer fork is detected
  - `chain_to_dict()` / `chain_from_dict()` - Serialization for network transfer
  - `get_blocks_after()` / `get_missing_blocks()` - Selective block synchronization
  - `get_vote_tally()` - Counts votes for each candidate from blockchain

- `transaction.py`: Transaction model and integrity checks. Potential attributes and methods:

  - `voter_id`: str
  - `candidate_id`: str
  - `timestamp`: str
  - `to_dict()` - to return attributes as dict. Useful for UI.

- User testing, deployment, and integration.

### Person 2: Networking Layer

- `tracker_server.py`: Peer registration, status updates, and vote option initialization and broadcasting. Multithreaded design to constantly listen for incoming UDP messages and handle main logic thread (broadcasting peer list and voting options). This class will be used by the application layer `server.py`. Example class methods include:
  - `initialize()`: To create a server that constantly listens for incoming UDP messages and responds accordingly.
- `peer.py`: UDP networking logic, message handling, block/vote broadcasting. Create a multithread architecture to constantly listen for incoming UDP messages and handling main logic thread. This class will be used by application layer `client.py` to create a class instance for peer client.Potential API functions to be called by application layer `client.py` include:
  - `connect()`: To register the peer with the tracker. Fetches and returns the peer list and voting options from the tracker. To be called by application layer `client.py`.
  - `submit_vote()`: To send a transaction for mining. Upon successful mining of newly create block, should append local to blockchain and broadcast results. To be called by application layer `client.py`/`client_ui.py`.
- Message types:
  - Tracker <-> Peer:
    - `REGISTER_PEER` (Peer -> Tracker): For peer to initiate connection to network.
    - `REGISTER_ACK` (Tracker -> Peer): Contains voting options
    - `LEAVE_PEER` (Peer -> Tracker): To inform tracker that it is leaving network.
  - Peer <-> Peer:
    - `NEW_BLOCK`: Sent when a peer broadcasts its newest block to other peers.
    - `REQUEST_CHAIN`: Used by new peers to request most up-to-date chains.
    - `CHAIN_RESPONSE`: Used to respond to REQUEST_CHAIN

### Person 3: Application Layer + Integration

- `client_ui.py`: Provides the front-end UI using Streamlit library or React components. Allows peers (voters) to submit votes, visualize their local blockchain, and view current vote tallies. Submits votes to peer.py.

- `client.py`: Serves as P2P node. Launches `client_ui.py` to render frontend. Initializes the peer instance by creating peer.py instance and calls on class functions. On startup, it registers with the tracker and requests the voting options. API functions include:

  - `update_ui() (optional, dependning on UI logic implementation)` to refresh UI based on changes in the blockhain. To be called by network layer `peer.py`. Not required if state is introduced to UI (automatically rerenders upon updating the blockchain).

- `server.py`: Serves as back-end server managing tracker initialization. Takes in CLI arguments to configure voting candidates to be broadcasted to each peer upon receiving a connection request message. Invokes `tracker_server.py`, passing in CLI arguments to configure voting candidates to be broadcasted to each peer.

- Application layer work is dependent on the completion of all lower-level layers and requires integrating all above code files from other team members.

- `merkletree.py (Optional)`: For verifying transaction consistency in blocks.

### High-level Diagram

      +----------------------------------------------------------------------------------------------------+
      |                                           Tracker VM                                               |
      |                                     server.py (tracker_server.py)                                  |
      +----------------------------------------------------------------------------------------------------+
                     ▲                                  ▲                                    ▲
                     |                                  |                                    |

                  Peers send msg to tracker_server upon initialization to request voting options.
                                 Request for peer node addresses during broadcasting.

                     |                                  |                                    |
                     ▼                                  ▼                                    ▼
      +---------------------------+       +---------------------------+       +---------------------------+
      |         Peer VM 1         | <---> |         Peer VM 2         | <---> |         Peer VM 3         |
      |  UI + client.py (peer.py) |       |  UI + client.py (peer.py) |       |  UI + client.py (peer.py) |
      +---------------------------+       +---------------------------+       +---------------------------+

      (Peers broadcast newly added block to all other peers following the
      request to tracker_server.py for peer node addresses.)
      ...

---

## 7. Technologies Used

- **Language**: Python3 and potentially JavaScript for UI
- **UI Frameworks/Libraries**: Streamlit UI/ ReactJS
- **Networking**: UDP sockets
- **Hashing**: SHA-256 via `hashlib`
- **Deployment**: Google Cloud VMs for tracker and peer nodes
- **API Server**: Flask (optional for user-facing interaction)

---

## 8. Security & Integrity

- Cryptographic hashes link all blocks.
- Tampering with any block invalidates all following blocks.
- Voter identities are anonymized.
- Invalid or duplicate votes are detected and discarded.

---

## 9. Resilience Demonstration

- Simulated forks demonstrate fork resolution via longest chain rule.
- Invalid blocks are rejected across all peers.
- Peer restart with full sync from other nodes using `REQUEST_CHAIN`.

---

## 10. Summary

This design provides a lightweight yet functional decentralized voting system. It demonstrates the core principles of blockchain, including decentralized consensus, tamper resistance, and peer-to-peer trustless interaction. The no-pool, peer-mined model ensures that vote submission and block creation are tightly coupled, eliminating the need for a shared transaction pool or predefined genesis block.
