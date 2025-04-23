# DESIGN.md

## 1. Overview
This project implements a simplified blockchain-based **Decentralized Voting System** using a peer-to-peer (P2P) architecture. The blockchain enables a group of nodes to reach consensus on voting results without a centralized authority. Each peer maintains a local copy of the blockchain, validates transactions (votes), mines blocks, handles forks, and communicates with other peers in the network.

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
- **Mining Process:** When a peer submits a vote, it immediately initiates mining a block containing that vote. There is no global transaction pool — each voting action triggers block creation locally.
- **Fork Resolution:** If two blocks are mined concurrently, the network may temporarily split. Peers resolve forks by adopting the longest valid chain, discarding shorter branches.

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
   - The vote is validated and triggers immediate mining of a new block containing the vote.
   - The vote is validated and immediately turned into a `NEW_VOTE` transaction locally.
   - This triggers mining of a new block with that single vote.

4. **Block Mining:**
   - The peer runs the PoW algorithm to find a valid nonce.
   - Once the block is mined, it is appended to the local blockchain.
   - A `NEW_BLOCK` message is broadcast to all known peers.

5. **Block Propagation and Validation:**
   - Peers receiving a `NEW_BLOCK` message verify the block’s validity (hash, nonce, previous hash).
   - If valid, the block is added to the local blockchain.
   - If it creates a fork, the peer uses the longest chain rule to resolve it.

6. **Result Tallying:**
   - Peers can be queried (via CLI/API) for the current voting results.
   - The vote count is computed by scanning the local blockchain and aggregating candidate IDs.

7. **Resilience:**
   - In case a peer falls behind, it can request the full chain using `REQUEST_CHAIN` upon restart.
   - Forks due to concurrent mining are resolved automatically.

---

## 5. Code Structure & Module Responsibilities

### High-Level Design
- `block.py`: Defines the Block class and its hashing/mining logic.
- `blockchain.py`: Manages the chain of blocks, mining, validation, and fork resolution.
- `transaction.py`: Defines a Vote transaction structure (voter_id, candidate_id, timestamp).
- `tracker_server.py`: Maintains the active peer list and shares it with joining peers.
- `peer.py`: Represents a peer node. Handles blockchain state, networking, vote submission, mining, and message broadcasting.
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

### Person 1: Partial Blockchain Layer + Testing and integration
- `block.py`: Block structure, hash computation, PoW logic.
- `blockchain.py`: Chain validation, append logic, fork resolution.
- User testing, deployment, and integration.

### Person 2: Networking Layer
- `tracker_server.py`: Peer registration, status updates.
- `peer.py`: UDP networking logic, message handling, block/vote broadcasting.

### Person 3: Partial Blockchain Layer + Application Layer
- `transaction.py`: Transaction model and integrity checks.
- `merkletree.py`: For verifying transaction consistency in blocks.
- `voting_api.py`: HTTP API for vote submission and result retrieval.
- Application protocol design.

---

## 7. Technologies Used
- **Language**: Python 3
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

