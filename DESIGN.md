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
- **Mining Process:** Peers aggregate unconfirmed vote transactions and iteratively compute block hashes with incrementing `nonce` until a hash meets the difficulty requirement. This ensures computational effort and deters tampering.
- **Fork Resolution:** If two blocks are mined concurrently, the network may temporarily split. Peers resolve forks by adopting the longest valid chain, discarding shorter branches. Rejected transactions can be re-added to the pool and rebroadcast.

### 2.3 Genesis Block
The genesis block is the first block in the blockchain:
- It is hardcoded and manually created during initialization.
- Contains no transactions and a `previous_hash` of "0".
- Acts as the root of trust, ensuring consistent validation for all future blocks.

---

## 3. Peer-to-Peer Protocol

### 3.1 Tracker Node
- Maintains an up-to-date list of active peers (IP and port).
- Peers register/deregister on join/leave.
- Periodically broadcasts peer list updates to all nodes to support peer discovery.

### 3.2 Peer Node Responsibilities
Each peer:
- Registers with the tracker and receives the peer list.
- Maintains a local copy of the blockchain.
- Submits and stores new votes.
- Mines blocks by solving PoW puzzles.
- Verifies and adds received blocks.
- Broadcasts newly mined blocks.
- Resolves forks using the longest chain rule.

### 3.3 Communication
- Implemented using UDP sockets.
- JSON is used for message formatting.
- Message types include:
  - `NEW_VOTE`: Sent by a peer to submit a new vote.
  - `MINE`: Command to initiate mining.
  - `NEW_BLOCK`: Broadcast a newly mined block.
  - `REQUEST_CHAIN`: Request full chain sync from a peer.
  - `REGISTER_PEER`: Sent to the tracker to register.
- Peers bind to local UDP ports and handle async messages from the tracker and other peers.

---

## 4. Demo Application: Decentralized Voting System

### 4.1 Features
- Voters submit votes which are broadcast to all peers.
- Transactions are grouped and mined into blocks.
- Blockchain is updated and broadcast after mining.
- Each peer tallies votes independently based on its local blockchain.
- Forks are resolved using the longest chain policy.

---

## 5. Code Structure & Module Responsibilities

### High-Level Design
- `block.py`: Defines the Block class and its hashing/mining logic.
- `blockchain.py`: Manages the chain of blocks, mining, validation, and fork resolution.
- `transaction.py`: Defines a Vote transaction structure (voter_id, candidate_id, timestamp).
- `tracker_server.py`: Maintains the active peer list and shares it with joining peers.
- `peer.py`: Represents a peer node. Handles blockchain state, networking, vote submission, mining, and message broadcasting.
- `merkletree.py`: Supports efficient block verification if multiple transactions per block are implemented.

### Application Flow
1. A peer creates a vote transaction and adds it to the transaction pool.
2. Peers mine a block with current transactions using PoW.
3. The block is broadcast to all other peers.
4. Peers validate the block and append it if valid.
5. Each peer independently tallies results by reading from its own chain.

---

## 6. Work Division

### Person 1: Partial Blockchain Layer
- `block.py`: Block structure, hash computation, PoW logic.
- `blockchain.py`: Chain validation, append logic, fork resolution.

### Person 2: Networking Layer
- `tracker_server.py`: Peer registration, status updates.
- `peer.py`: UDP networking logic, message handling, block/vote broadcasting.

### Person 3: Partial Blockchain Layer + Application Layer
- `transaction.py`: Transaction model and integrity checks.
- `merkletree.py`: For verifying transaction consistency in blocks.
- Voting transaction submission interface.
- Application protocol design.
- User testing, deployment, and integration.

---

## 7. Technologies Used
- **Language**: Python 3
- **Networking**: UDP sockets
- **Hashing**: SHA-256 via `hashlib`
- **Deployment**: Google Cloud VMs for tracker and peer nodes

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

---

## 10. Summary
This design provides a lightweight yet functional decentralized voting system. It demonstrates the core principles of blockchain, including decentralized consensus, tamper resistance, and peer-to-peer trustless interaction. The modular design and team-based development plan ensure maintainability and extensibility.

