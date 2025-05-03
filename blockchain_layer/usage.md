# Blockchain Layer Usage

This module provides a decentralized voting blockchain system with features including:

- Creating and managing a blockchain with proof-of-work consensus.
- Adding and mining transactions (votes).
- Validating the blockchain integrity.
- Resolving forks via consensus with peer chains.
- Simulating network conditions with block and chain data propagation.

## Running the Test

The `blockchain_test.py` file contains comprehensive tests simulating realistic network scenarios:

- Single block propagation with proof-of-work validation.
- Fork resolution by full chain synchronization.
- Handling malicious blocks and chains.
- Successful single block propagation without requiring fork resolution.

```bash
python blockchain_test.py
```
Ensure you run this command from the `blockchain_layer` dir or provide the correct path.

## Key Functions

- Intra-Node actions
    - `Blockchain.add_new_transaction(transaction)`: Add a new vote transaction.
    - `Blockchain.mine_block()`: Mine a block with pending transactions. Also the block is immediately appended to the local chain
- Inter-Node actions
    - `Blockchain.add_block(block, proof)`: Add a block from a block received with verification of proof-of-work and previous hash verification.
    - `Blockchain.update_chain(chain_dicts_from_peers)`: Resolve forks by adopting the longest valid chain.
    - `Blockchain.get_last_block_dict()`: Get the last block as a dict that could be dumped for network propagation.
    - `block_from_dict(block_dict)`: Reconstruct a Block object from its dictionary representation.

## Usage Examples

### Malicious Block Addition and propagation rejection Simulation

```python
def test_malicious_block_addition():
    print("=== Test: Malicious Block Addition Network Simulation ===")

    # Create a blockchain and mine a malicious block
    node = Blockchain()
    node.add_new_transaction(Transaction("voter1", "candidateA"))
    node.mine_malicious_block() # Forcefully append a malicious block onto local chain
    malicious_block = node.last_block
    print("Malicious block mined on node:")
    print(f"Block index: {malicious_block.index}, previous_hash: {malicious_block.previous_hash}, hash: {malicious_block.hash}")

    # Create a new clean blockchain instance
    node2 = Blockchain()

    # Attempt to add the malicious block to the new blockchain
    print("\nAttempting to add malicious block to a new blockchain instance...")
    add_result = node2.add_block(malicious_block, malicious_block.hash)
    print(f"Add malicious block result: {add_result}")
    assert not add_result, "Malicious block should not be added to a clean blockchain"

    # The malicious block chain on node should be invalid
    is_valid = node.is_valid_chain(node.chain)
    print(f"Is the malicious chain valid? {is_valid}")
    assert not is_valid, "Malicious chain should be invalid"

    # The clean blockchain should remain valid
    is_valid_clean = node2.is_valid_chain(node2.chain)
    print(f"Is the clean blockchain valid? {is_valid_clean}")
    assert is_valid_clean, "Clean blockchain should remain valid"
```

### Single Block Propagation and Fork Resolution

```python
node1 = Blockchain()
node1.add_new_transaction(Transaction("voter1", "candidateA"))
node1.mine_block()

node2 = Blockchain()
node2.add_new_transaction(Transaction("voter2", "candidateB"))
node2.mine_block()
node2.add_new_transaction(Transaction("voter3", "candidateC"))
node2.mine_block()

# In Node 2
node2_last_block_dict = node2.get_last_block_dict()
# network layer then serialize this and send to node 1


# In Node 1, we shall reconstruct the dict from serialized data
# last_block_dict_received = json load...(received dump)
received_last_block = block_from_dict(last_block_dict_received)
received_last_block_proof = received_last_block.hash 

# Node1 tries to add Node2's last block
added = node1.add_block(received_last_block, received_last_block_proof) 
# this func verifies PoW and 
# previous_hash alignment for that new block
# Return True if the local chain added the new block.

assert not added # if the 'add_block' returned true, then
# there will be no further actions
# but here bc node 2/chain 2 is longer, node 1 should sync up to chain 2/ node 2

if not added and node2_last_block.hash.startswith('0' * node1.difficulty):
    # the sync only happens when PoW of that propagated block
    #  has valid PoW, this PoW should be checked manually as here

    # Full chain sync if single block add fails but PoW valid
    
    # Node 1 here should request node 2 for full chain
    # node1.request_full_chain()

    # Inside Node 2, it should receive that request and dump its chain
    node2_chain_data = node2.get_chain_data() # list of dicts
    # node2.send(node2_chain_data), send it to 1

    # Node 1 receives the whole chain info from node 2, update
    update_result=node1.update_chain([node2_chain_data]) 
    # this update only happen if the node2's chain is valid,
    #  and this op will return True if update happened
    assert update_result == True
```

### Successful Single Block Propagation

```python
node1 = Blockchain()
node1.add_new_transaction(Transaction("voter1", "candidateA"))
node1.mine_block()

node2 = Blockchain()
node2.update_chain([node1.get_chain_data()])
node2.add_new_transaction(Transaction("voter2", "candidateB"))
node2.mine_block()

node2_last_block_dict = node2.get_last_block_dict()
node2_last_block = block_from_dict(node2_last_block_dict)
node2_last_block_proof = node2_last_block.hash

added = node1.add_block(node2_last_block, node2_last_block_proof)
# added should be True, no fork resolution needed
```

## Notes

- The blockchain uses a proof-of-work difficulty to secure blocks.
- Transactions represent votes with voter and candidate IDs.
- The system supports network synchronization by propagating blocks and chains as serialized data.
- The tests simulate network conditions to ensure robustness against malicious data and fork scenarios.

For detailed usage examples, refer to the `blockchain_test.py` file.
