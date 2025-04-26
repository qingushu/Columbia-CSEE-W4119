📚 Overview
This document describes the test plan, scenarios, and expected outcomes for validating the network layer of the Decentralized Voting System project, including:

Tracker Server (tracker_server.py)

Peer Node (peer.py)

The goal is to ensure the UDP-based peer-to-peer communication is reliable, correct, and robust before integrating blockchain and application layers.

🛠️ Environment Setup
Google Cloud VMs

Python 3.8+

Open necessary firewall rules for UDP traffic (default tracker port: 5000).

Modules under test:

tracker_server.py

peer.py

✅ Test Cases
1. Tracker Initialization Test
Test Step | Expected Result
Start tracker_server.py on VM. | Tracker binds to configured port and listens for incoming messages without errors.
Tracker prints “Listening on 0.0.0.0:5000”. | Tracker is operational.

2. Peer Registration and Peer List Reception
Test Step | Expected Result
Start peer.py on a different VM. | Peer sends REGISTER_PEER message to tracker.
Tracker logs registration event. | Tracker responds with REGISTER_ACK containing voting options and current peer list.
Peer prints received voting options and peers. | Peer initializes correctly.

3. Multiple Peer Join Test
Test Step | Expected Result
Start 2–3 additional peers. | Each new peer registers and receives updated peer list from tracker.
Tracker maintains dynamic list of connected peers. | All peers list each other correctly.

4. Vote Submission and New Block Broadcasting
Test Step | Expected Result
Call submit_vote() on a peer instance, passing a sample transaction. | Peer mines a new block and broadcasts it.
Other peers receive a NEW_BLOCK message. | Receiving peers validate and append the new block.
All blockchains grow consistently. | Confirm blockchains match across all peers.

5. Chain Synchronization Test
Test Step | Expected Result
Manually introduce a delay (simulate crash) for a peer, or start a new peer later. | Delayed/new peer sends REQUEST_CHAIN message after startup.
Existing peer responds with CHAIN_RESPONSE. | Delayed/new peer updates its blockchain to match the latest version.

6. Fork Resolution Test 
Test Step | Expected Result
Simultaneously call submit_vote() on two different peers. | Two blocks might be broadcasted simultaneously, causing forks.
Peers temporarily diverge into two chains. | Eventually, peers adopt the longer valid chain according to longest-chain rule.
Forked chain is discarded. | All peers converge on a common blockchain again.

7. Tracker Peer Leave Test
Test Step | Expected Result
Manually terminate a peer and send a LEAVE_PEER message to tracker. | Tracker removes the peer from its internal list.
New peers receive updated peer lists (excluding the departed peer). | Peers continue normal operations.

# Start tracker server
python3 tracker_server.py

# Start peer clients
python3 peer.py  # (Peer 1)
python3 peer.py  # (Peer 2)
python3 peer.py  # (Peer 3)

# In peer.py shell or through client script
peer_instance.submit_vote({
    "voter_id": "hashed_voter_1",
    "candidate_id": "Alice",
    "timestamp": "current_time"
}, mining_function)


