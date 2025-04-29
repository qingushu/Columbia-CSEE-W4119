# Blockchain Voting System Guide

## Basic Usage

```python
from blockchain import Blockchain
from transaction import Transaction

# Create a blockchain
blockchain = Blockchain()

# Add votes
blockchain.add_new_transaction(Transaction("voter1", "candidateA"))
blockchain.add_new_transaction(Transaction("voter2", "candidateB"))

# Mine the votes into a block
blockchain.mine_block()

# Get vote count
vote_count = blockchain.get_vote_count()
print("Vote Count:", vote_count)  # {'candidateA': 1, 'candidateB': 1}
```

## Consensus Mechanism

The blockchain uses a consensus mechanism to ensure all nodes in the network agree on the same chain state. Here's how it works:

1. **Longest Chain Rule**: The system follows the longest valid chain rule
   - When conflicts occur, nodes accept the longest valid chain
   - This ensures network convergence to a single truth

2. **Chain Validation**: Each chain must pass these checks:
   - All blocks have valid proof-of-work
   - All block hashes are correctly linked
   - All transactions in blocks are valid
   - The genesis block excepted.

Example of consensus in action:

```python
# Create three blockchain nodes
node1 = Blockchain()
node2 = Blockchain()
node3 = Blockchain()

# Node 1: Add and mine votes
node1.add_new_transaction(Transaction("voter1", "candidateA"))
node1.mine_block()  # Chain length = 2 (genesis + 1 block)

# Node 2: Add and mine more votes (creates longer chain)
node2.add_new_transaction(Transaction("voter2", "candidateB"))
node2.mine_block()
node2.add_new_transaction(Transaction("voter3", "candidateA"))
node2.mine_block()  # Chain length = 3 (genesis + 2 blocks)

# Node 3: Add and mine different votes
node3.add_new_transaction(Transaction("voter2", "candidateB"))
node3.mine_block()  # Chain length = 2 (genesis + 1 block)

# Get chain data from all nodes
node1_data = node1.get_chain_data()  # Length 2
node2_data = node2.get_chain_data()  # Length 3 (longest)
node3_data = node3.get_chain_data()  # Length 2

# Apply consensus
# Node 1 and 3 will adopt Node 2's chain since it's longer
node1.consensus([node2_data, node3_data])  # Returns True (chain was updated)
node3.consensus([node1_data, node2_data])  # Returns True (chain was updated)
node2.consensus([node1_data, node3_data])  # Returns False (kept own chain)

# Verify consensus
print("Final chain lengths:", 
      len(node1.chain),  # 3
      len(node2.chain),  # 3
      len(node3.chain))  # 3

# All nodes now have same vote count
print("Node 1 votes:", node1.get_vote_count())
print("Node 2 votes:", node2.get_vote_count())
print("Node 3 votes:", node3.get_vote_count())
```

## Tampering Example

```python
# Create blockchain and add votes
blockchain = Blockchain()
blockchain.add_new_transaction(Transaction("voter1", "candidateA"))
blockchain.add_new_transaction(Transaction("voter2", "candidateB"))
blockchain.mine_block()

# Print original votes
print("\nOriginal votes:", blockchain.get_vote_count())

# Try to tamper with a vote
print("\nTampering with the blockchain...")
blockchain.chain[1].transactions[0].candidate_id = "candidateC"  # Change first vote

# Verify the chain
is_valid = blockchain.is_valid_chain(blockchain.chain)
print("Is blockchain still valid?", is_valid)  # Will print False - tampering detected!

# During consensus, tampered chains will be rejected
# Other nodes will keep their valid chains
```

*Check the [blockchain_test.py](./blockchain_test.py) for details*