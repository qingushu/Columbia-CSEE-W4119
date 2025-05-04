# Blockchain-Based Decentralized Voting System – Testing Documentation

## 1. Overview

This document outlines the testing strategy, test cases, and results verification methods for the blockchain-based decentralized voting system. The goal of testing is to validate:

✅ Blockchain consistency across peers

✅ Correct handling of forks and chain synchronization

✅ Proper broadcasting of mined blocks

✅ Handling of peer join/leave and tracker heartbeats

✅ Resilience to invalid/malicious blocks

✅ Accurate vote counting

✅ Functionality of the Streamlit UI

## 2. Test Environment

- 3 Google Cloud VM instances (each acting as a peer)
- 1 tracker server hosted
- All nodes connected over UDP
- Python 3.9+ installed on all nodes
- Firewall rules configured to allow UDP traffic on required ports
- Tests performed using CLI + Streamlit UI

## 3. Test Plan

### 3.1 Functional Tests

| **Test ID** | **Description**                       | **Expected Result**                                   |
| ----------- | ------------------------------------- | ----------------------------------------------------- |
| F1          | Peer can register with tracker        | Peer receives peer list + ballot options              |
| F2          | Peer submits vote & mines block       | Block added locally, broadcast sent                   |
| F3          | Peer receives valid block broadcast   | Block validated and appended                          |
| F4          | Peer receives invalid block broadcast | Block rejected, triggers REQUEST_CHAIN                |
| F5          | Peer requests chain sync              | Peer receives full chain and replaces if valid/longer |
| F6          | Peer tally vote                       | Vote count matches expected values                    |
| F7          | Tracker removes peer on no heartbeat  | Peer removed after 3 missed POKE_ACKs                 |
| F8          | UI shows blockchain                   | UI renders blocks as cards with correct info          |
| F9          | UI shows live vote tally              | Bar chart updates with each vote                      |

### 3.2 Fork Handling Tests

| **Test ID** | **Description**                              | **Expected Result**                             |
| ----------- | -------------------------------------------- | ----------------------------------------------- |
| F10         | Two peers mine blocks simultaneously (fork)  | Shorter branch discarded, longest chain adopted |
| F11         | Peer mines block while disconnected, rejoins | Peer syncs with longer chain on reconnect       |

### 3.3 Edge & Error Handling Tests

| **Test ID** | **Description**                | **Expected Result**                            |
| ----------- | ------------------------------ | ---------------------------------------------- |
| E1          | Peer sends malformed NEW_BLOCK | Block rejected, no crash                       |
| E2          | Peer crashes & restarts        | Peer re-registers and syncs chain              |
| E3          | Tracker fails to respond       | Peer times out but keeps retrying registration |

## 4. Test Procedure

### 4.1 Peer Registration

- Start server.py on tracker VM
- Start client.py on each peer VM
- Observe tracker logs for Registered peer
- Check peer logs confirm Registered with tracker
- Verify peers received peer list and ballot options

✅ PASS if peers show registered + list populated

result log:
gushuqin@Gushus-MBP Columbia-CSEE-W4119 % python3 application/server.py 5000 127.0.0.1 'A,B,C'
[Server] Starting tracker on 127.0.0.1:5000
[Tracker] Listening on 127.0.0.1:5000
[Tracker] Registered peer 127.0.0.1:6003
[Tracker] Sent updated peer list to 127.0.0.1:6003
[Tracker] Broadcasted updated peers list.
[Tracker] Sent POKE to 127.0.0.1:6003

gushuqin@Gushus-MBP Columbia-CSEE-W4119 % streamlit run application/client.py -- 6003 127.0.0.1 5000 127.0.0.1
[Peer] Sent request to register with tracker...
[Peer] Registered with tracker.
[Peer] Registered with tracker.
[Peer] Received block 0/0
[Peer] Chain synced from peer
[Peer] Received block 0/0
[Peer] Chain synced from peer
[Peer] Updated peer list: {'127.0.0.1:6003', '127.0.0.1:6001'}
[Peer] Sent POKE-ACK to tracker at 127.0.0.1:5000
[Peer] Sent ballot request to tracker...
[Peer] Received voting options: ['A', 'B', 'C']
[Peer] Ready for casting ballot

### 4.2 Vote Submission & Mining

- Open UI for each peer
- Submit a vote
- Observe console logs: mining started..., mined block...
- Check peer logs for broadcasted NEW_BLOCK
- On other peers: check for received NEW_BLOCK + block added

✅ PASS if block propagates to all peers & visible in UI

peer1 cast a vote A and it broadcasted and block added to all other peers

result log:
[Peer] Adding transaction to new block and initiating mining...
[Peer] Successfully mined newly added block.
[Peer] Broadcasting to {'127.0.0.1:6002', '127.0.0.1:6003'}
[Peer] Broadcasted block to 127.0.0.1:6002
[Peer] Broadcasted block to 127.0.0.1:6003

### 4.3 Fork Simulation

- Disconnect peer 3 from network using the Developer/Demo Settings from the sidebar.
- Submit vote at peer 3 & mine a block
- Submit vote at peer 1 & mine a different block
- Reconnect peer 3
- Observe peer 3 syncs to longest chain

✅ PASS if peer 3 chain is replaced with longer chain

### 4.4 Heartbeat Failure

- Start all peers
- Kill peer 2 process without sending LEAVE_PEER using CTRL + C
- Observe tracker sending POKE to peer 2
- Tracker logs peer removed due to heartbeat timeout after 3 missed
- Remaining peers receive updated peer list

✅ PASS if tracker removes peer 2 after timeout

result log:
[Peer] Updated peer list: {'127.0.0.1:6003'}

### 4.5 Malicious Block Injection

- In UI sidebar, click "Add Malicious Block"
- Peer broadcasts invalid block
- Observe receiving peers log Invalid block, requesting chain sync
- Verify no invalid block added

✅ PASS if block rejected and chain sync triggered

## 5. How to Run Tests

1.  Deploy tracker server:
    python3 application/server.py 5000 127.0.0.1 'A,B,C'

2.  Start peers:
    streamlit run application/client.py -- 6002 127.0.0.1 5000 127.0.0.1
    streamlit run application/client.py -- 6001 127.0.0.1 5000 127.0.0.1
    streamlit run application/client.py -- 6003 127.0.0.1 5000 127.0.0.1

3.  Submit votes and observe logs & UI
