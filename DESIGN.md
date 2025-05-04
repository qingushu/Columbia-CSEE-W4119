# DESIGN.md

**Team No. 22**  
**Team Members:** Kevin Li, Ian Li, Gushu Qin

---

## 1. Overview

This project implements a simplified blockchain-based **Decentralized Voting System** using a peer-to-peer (P2P) architecture with UDP sockets. Each peer maintains its own blockchain, independently mines blocks containing a vote transaction, and exchanges blocks with other peers to achieve eventual consensus.

A tracker node helps coordinate peer discovery and liveness detection via heartbeat. Forks are resolved by adopting the **longest valid chain**. The system supports peer joins, departures, and synchronization after temporary disconnection.

✅ Designed to satisfy project requirements for a minimum of 3 peers communicating over Google Cloud VMs.

✅ Each peer acts as both a voter and miner.

---

## 2. Blockchain Design

### 2.1 Block Structure

Each block contains:

- `index`: Position in chain
- `timestamp`: Block creation timestamp
- `transactions`: List of vote transactions (one per block)
- `previous_hash`: Hash of the previous block
- `nonce`: Proof-of-work nonce
- `hash`: Computed SHA-256 hash of block contents

Implemented in `block.py`.

---

### 2.2 Mining & Consensus

- **Mining Trigger:** A peer mines a block **immediately upon submitting a vote** (no transaction pool).
- **Proof-of-Work (PoW):** The block is mined until its hash satisfies the configured difficulty (e.g., 2 leading zeroes).
- **Fork Handling:** If a received block conflicts with the local chain, the peer triggers a `REQUEST_CHAIN` protocol and switches to the longest valid chain.
- **Chain Synchronization:**
  - Peers only synchronize:
    - On fork detection
    - Explicit manual request
    - When starting up

There’s **no periodic chain sync** (lazy sync only upon events).

---

### 2.3 Genesis Block

✅ Created automatically when each peer initializes `Blockchain()`.

✅ Contains index 0, empty transactions, fixed timestamp, and a hardcoded hash.

This ensures all peers share the same genesis block.

---

## 3. Peer-to-Peer Protocol

### 3.1 Tracker Node

- Maintains **active peer list**
- Sends updated peer list to new peers
- Sends **heartbeat `POKE` messages every second**
- Removes peers after missing **3 consecutive `POKE_ACK` responses**

Implemented in `tracker_server.py`.

---

### 3.2 Peer Responsibilities

Each peer:

✅ Registers with tracker (`REGISTER_PEER`)  
✅ Receives list of peers  
✅ Requests most recent chain upon first registering with tracker
✅ Submits votes → triggers mining → broadcasts block  
✅ Listens for `NEW_BLOCK` from other peers  
✅ Verifies incoming blocks (hash, PoW, previous hash)  
✅ Handles forks by requesting chain and adopting longest valid chain  
✅ Responds to `POKE` from tracker with `POKE_ACK`

Implemented in `peer.py`.

---

### 3.3 Message Types

| Type          | Sender  | Receiver | Purpose                                |
| ------------- | ------- | -------- | -------------------------------------- |
| REGISTER_PEER | Peer    | Tracker  | Join the network                       |
| REGISTER_ACK  | Tracker | Peer     | Return peer list                       |
| UPDATE_PEERS  | Tracker | Peer     | Notify updated peer list               |
| NEW_BLOCK     | Peer    | Peers    | Broadcast mined block                  |
| REQUEST_CHAIN | Peer    | Peers    | Request full chain (triggered on fork) |
| CHAIN_BLOCK   | Peer    | Peer     | Response with one block at a time      |
| POKE          | Tracker | Peer     | Heartbeat ping                         |
| POKE_ACK      | Peer    | Tracker  | Heartbeat response                     |
| LEAVE_PEER    | Peer    | Tracker  | Graceful leave                         |

---

### 4. Workflow

#### 4.1 Tracker Initialization

- The tracker node (tracker_server.py) starts and binds to a fixed UDP port.
- It initializes a list of allowed voting options (candidates).
- It maintains an active peer list, tracking:
- Peers that have registered
- Peers responding to periodic POKE heartbeats
- It begins sending POKE messages every second to all known peers.

#### 4.2 Peer Registration and Startup

- A peer (peer.py) starts and binds to a local UDP port.
- It sends a REGISTER_PEER message to the tracker, providing its IP/port.
- The tracker responds with a REGISTER_ACK message, containing:
  - The allowed voting options
  - A list of currently known peers
- The peer requests the voting options and stores the voting options in the application layer (client.py) for later use.
- Upon initial connection with the tracker, the peer sends a REQUEST_CHAIN message to known peers to synchronize its local blockchain with others.
- Any responding peer sends back one block at a time via CHAIN_BLOCK messages to reconstruct the chain incrementally.

#### 4.3 Vote Submission (Peer Voting)

- A peer’s user selects a candidate to vote for.
- The peer creates a Transaction object containing:
  - voter_id
  - candidate_id
  - timestamp
- The peer calls submit_vote():
- Adds the transaction to its blockchain’s pending transactions
- Immediately triggers mining a new block containing that transaction

#### 4.4 Block Mining (Proof-of-Work)

- The peer runs mine_block():
- Builds a Block object
- Tries nonce values until hash(block_data + nonce) satisfies the difficulty (e.g., 2 leading zeros)
- Once mined:

  - The block is appended to the peer’s local blockchain
  - A NEW_BLOCK message is broadcast to all known peers

#### 4.5 Block Propagation and Validation

- Each peer continuously listens for NEW_BLOCK messages from others.
- Upon receiving a new block:
- Validate:
  - Does previous_hash match local last block hash?
  - Does the block’s hash satisfy the difficulty?
- If valid and fits directly on the current chain → append
- If index already exists but hash mismatches → fork detected!
- Peer calls request_chain() to trigger a full chain sync
- If invalid (bad hash, broken link, invalid PoW):

  - Block is rejected
  - Chain sync may be triggered depending on detection

#### 4.6 Fork Resolution

- When a peer detects a fork (incoming block index already exists but hash mismatch):
- Sends REQUEST_CHAIN to peers
- Peers respond with one block at a time (CHAIN_BLOCK messages) to rebuild missing chain
- Peer replaces its local chain with the longer valid chain received

#### 4.7 Vote Tallying

- Each peer independently computes vote results from its local blockchain.
- Tally computed by iterating over blockchain.chain and counting votes in transactions.
- Result can be queried at any time. On the UI, the tally is displayed in real-time.
- Because all valid chains should converge to the same longest chain, results are consistent across peers.

#### 4.8 Peer Liveness and Failure Handling

- Each peer responds immediately with POKE_ACK.
- Tracker tracks consecutive missed responses:
- If a peer misses 3 consecutive POKE_ACK, it is removed from the peer list.
- Removed peers are excluded from further peer list updates sent to new peers.

#### 4.9 Peer Departure

- A peer can send LEAVE_PEER message to tracker before shutdown. This can be done by clicking on the 'Leave + Terminate' button on the UI.
- Tracker removes the peer immediately from active list.
- Remaining peers retain blockchain state.
- Alternatively, the user can CTRL+C to termiante the client.py program to initiate an ungraceful termination. The tracker will eventually remove the peer from the peer list due to the heartbeat mechanism.

#### 📝 Key Differences from Standard Blockchain

✅ No global transaction pool → peer mines vote immediately

✅ No automatic periodic chain sync → sync only on fork or startup

✅ Only 1 vote per block → simplifies validation

✅ Chain sync implemented as incremental 1-block-at-a-time responses (to avoid UDP size limits)

#### 4.10 Example Interaction Timeline

1. Tracker starts.
2. Peer A, B, C join → send REGISTER_PEER → get peer list + vote options.
3. Peer A votes → mines block → broadcasts NEW_BLOCK.
4. Peer B receives block → validates → appends.
5. Peer C votes → mines its own block at same height → broadcast NEW_BLOCK.
6. Peer A/B receive conflicting block → detect fork → send REQUEST_CHAIN.
7. Peer C responds with CHAIN_BLOCK (entire chain).
8. Peer A/B adopt longer chain → discard shorter fork.
9. Peer B crashes → tracker stops receiving POKE_ACK → removes B.
10. Peer B rejoins → sends REGISTER_PEER → receives peer list → sends REQUEST_CHAIN → syncs chain.

### 5. Code Structure

| File                | Responsibility                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| `block.py`          | Block class (structure, compute_hash)                                                                   |
| `blockchain.py`     | Blockchain class (mining, validation)                                                                   |
| `transaction.py`    | Vote transaction structure                                                                              |
| `tracker_server.py` | Tracker node, peer management                                                                           |
| `peer.py`           | Peer node (voting, mining, sync, network)                                                               |
| `client.py`         | Client application class to interact with peer instance. Integrated with Streamlit and initiates UI.    |
| `client_ui.py`      | Streamlit UI code for peer                                                                              |
| `server.py`         | Tracker-server application class to intialize tracker.py. Stores ballot options based on CLI arguments. |

---

### 6. Key Design Decisions

✅ One transaction per block → simplified mining & block broadcast

✅ No transaction pool

✅ Peers broadcast mined block, not transactions

✅ Fork resolution via requesting chain only when fork detected

✅ Tracker monitors liveness via POKE/POKE_ACK protocol

✅ UDP for lightweight, lossy communication

---

### 7. Testing Notes

- Minimum 3 peers required for full demo
- Each peer submits at least 2 votes
- Validate:
  - Peers adopt longest chain after forks
  - Tracker correctly removes dead peers
  - NEW_BLOCK properly propagates across peers

---

### 8. Security Considerations

✅ Cryptographic hash links blocks

✅ Invalid blocks rejected at peer level

✅ Votes immutable once mined

✅ No vote anonymity → voter_id stored as plain string

---

### 10. Summary

- This system demonstrates a decentralized blockchain voting system with:
  - Peer-to-peer networking
  - Mining on vote submission
  - Fork resolution
  - Peer discovery via tracker
  - Liveness detection via heartbeat
  - Designed for educational demonstration of blockchain and distributed consensus principles.
