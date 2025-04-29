import time
import json
from blockchain import Blockchain
from transaction import Transaction

def print_chain(blockchain):
    """Helper function to print blockchain details."""
    print("\n==== BLOCKCHAIN ====")
    print(f"Chain length: {len(blockchain.chain)}")
    
    for i, block in enumerate(blockchain.chain):
        print(f"\nBlock #{i}:")
        print(f"  Timestamp: {block.timestamp}")
        print(f"  Previous Hash: {block.previous_hash[:15]}...")
        print(f"  Hash: {block.hash[:15]}...")
        print(f"  Nonce: {block.nonce}")
        print(f"  Transactions: {len(block.transactions)}")
        
        for j, tx in enumerate(block.transactions):
            print(f"    Transaction #{j}:")
            print(f"      Voter: {tx.voter_id}")
            print(f"      Candidate: {tx.candidate_id}")
            print(f"      Time: {tx.timestamp}")

def print_vote_count(blockchain):
    """Helper function to print the vote count from blockchain."""
    print("\n==== VOTE COUNT ====")
    vote_count = blockchain.get_vote_count()
    
    if not vote_count:
        print("No votes recorded yet.")
        return
        
    total_votes = sum(vote_count.values())
    print(f"Total votes: {total_votes}")
    
    # Print votes for each candidate
    for candidate, count in sorted(vote_count.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_votes) * 100
        print(f"{candidate}: {count} votes ({percentage:.1f}%)")

def simulate_node():
    """Simulates a voting node in the network."""
    # Create a new blockchain
    print("Creating a new blockchain node...")
    blockchain = Blockchain()
    
    # Print the genesis block
    print("\nGenesis block created:")
    print_chain(blockchain)
    assert blockchain.is_valid_chain(blockchain.chain), "Genesis block should be valid"
    
    # Add some transactions (votes)
    print("\nAdding votes...")
    blockchain.add_new_transaction(Transaction("voter123", "candidateA"))
    blockchain.add_new_transaction(Transaction("voter456", "candidateB"))
    blockchain.add_new_transaction(Transaction("voter789", "candidateA"))
    
    # Print unconfirmed transactions
    print(f"Unconfirmed votes: {len(blockchain.unconfirmed_transactions)}")
    for tx in blockchain.unconfirmed_transactions:
        print(f"  {tx.voter_id} voted for {tx.candidate_id}")
    
    # Mine a block
    print("\nMining votes into a block...")
    mining_result = blockchain.mine_block()
    
    if mining_result:
        print("Block successfully mined!")
        assert blockchain.is_valid_chain(blockchain.chain), "Chain should be valid after mining"
    else:
        print("No transactions to mine!")
    
    # Print the updated chain
    print_chain(blockchain)
    
    # Print vote count after first block
    print_vote_count(blockchain)
    assert len(blockchain.get_vote_count()) == 2, "Should have votes for 2 candidates"
    assert blockchain.get_vote_count()["candidateA"] == 2, "Candidate A should have 2 votes"
    assert blockchain.get_vote_count()["candidateB"] == 1, "Candidate B should have 1 vote"
    
    # Add more votes
    print("\nAdding more votes...")
    blockchain.add_new_transaction(Transaction("voter101", "candidateC"))
    blockchain.add_new_transaction(Transaction("voter202", "candidateA"))
    
    # Mine another block
    print("\nMining more votes into a block...")
    blockchain.mine_block()
    print_chain(blockchain)
    assert blockchain.is_valid_chain(blockchain.chain), "Chain should be valid after second mining"
    
    # Print updated vote count
    print_vote_count(blockchain)
    assert len(blockchain.get_vote_count()) == 3, "Should have votes for 3 candidates"
    assert blockchain.get_vote_count()["candidateA"] == 3, "Candidate A should have 3 votes"
    assert blockchain.get_vote_count()["candidateB"] == 1, "Candidate B should still have 1 vote"
    assert blockchain.get_vote_count()["candidateC"] == 1, "Candidate C should have 1 vote"
    
    # Test chain validation
    print("\nValidating blockchain...")
    is_valid = blockchain.is_valid_chain(blockchain.chain) 
    print(f"Is blockchain valid? {is_valid}")
    assert is_valid == True, "Blockchain should be valid"
    
    return blockchain

def test_tamper_resistance():
    """Test the blockchain's resistance to tampering."""
    print("\n==== TESTING TAMPER RESISTANCE ====")
    
    # Create a blockchain with a single block
    blockchain = Blockchain()
    blockchain.add_new_transaction(Transaction("voter1", "candidateA"))
    blockchain.add_new_transaction(Transaction("voter2", "candidateB"))
    blockchain.mine_block()
    
    # Print the original state
    print("\nOriginal blockchain:")
    print_chain(blockchain)
    print_vote_count(blockchain)
    
    # Validate the blockchain
    print("\nValidating original blockchain...")
    is_valid = blockchain.is_valid_chain(blockchain.chain)  
    print(f"Is blockchain valid? {is_valid}")
    assert is_valid == True, "Original blockchain should be valid"
    
    # Tamper with the blockchain
    print("\nTampering with the blockchain (changing a vote)...")
    blockchain.chain[1].transactions[0].candidate_id = "candidateC"
    
    # Print the tampered state
    print("\nTampered blockchain:")
    print_chain(blockchain)
    
    # This direct count bypasses validation to show what the tampered count would be
    print("\nTampered vote count (not using blockchain.get_vote_count()):...")
    
    # Validate the tampered blockchain
    print("\nValidating tampered blockchain...")
    is_valid = blockchain.is_valid_chain(blockchain.chain)  
    print(f"Is blockchain valid? {is_valid}")
    assert is_valid == False, "Tampered blockchain should be invalid"
    
    return blockchain

def simulate_fork_resolution():
    """Simulates a fork in the blockchain and its resolution."""
    print("\n==== SIMULATING NETWORK FORK RESOLUTION ====")
    
    # Create three nodes with identical genesis blocks
    print("Creating three blockchain nodes...")
    node1 = Blockchain()
    node2 = Blockchain()
    node3 = Blockchain()
    
    # Ensure all nodes have the same genesis block hash
    genesis_hash = node1.chain[0].hash
    print(f"Genesis block hash: {genesis_hash[:10]}...")
    assert node1.is_valid_chain(node1.chain), "Node 1 genesis chain should be valid"
    assert node2.is_valid_chain(node2.chain), "Node 2 genesis chain should be valid"
    assert node3.is_valid_chain(node3.chain), "Node 3 genesis chain should be valid"
    
    # Node 1 mines a block
    print("\nNode 1 processes votes...")
    node1.add_new_transaction(Transaction("district1_voter1", "candidateA"))
    node1.add_new_transaction(Transaction("district1_voter2", "candidateB"))
    node1.mine_block()
    assert node1.is_valid_chain(node1.chain), "Node 1 chain should be valid after mining"
    
    # Node 2 mines two blocks (will become the longest chain)
    print("\nNode 2 processes votes...")
    node2.add_new_transaction(Transaction("district2_voter1", "candidateC"))
    node2.mine_block()
    node2.add_new_transaction(Transaction("district2_voter2", "candidateA"))
    node2.mine_block()
    assert node2.is_valid_chain(node2.chain), "Node 2 chain should be valid after mining"
    
    # Node 3 mines one block but with different transactions
    print("\nNode 3 processes votes...")
    node3.add_new_transaction(Transaction("district3_voter1", "candidateB"))
    node3.add_new_transaction(Transaction("district3_voter2", "candidateB"))
    node3.mine_block()
    assert node3.is_valid_chain(node3.chain), "Node 3 chain should be valid after mining"
    
    print("\nBefore consensus:")
    print(f"Node 1 chain length: {len(node1.chain)}")
    print(f"Node 2 chain length: {len(node2.chain)}")
    print(f"Node 3 chain length: {len(node3.chain)}")
    
    # Get chain data from all nodes
    node1_data = node1.get_chain_data()
    node2_data = node2.get_chain_data()
    node3_data = node3.get_chain_data()
    
    print(f"\nChain data lengths: Node1={len(node1_data)}, Node2={len(node2_data)}, Node3={len(node3_data)}")
    
    # Apply consensus on each node with other nodes' data
    print("\nApplying consensus algorithm...")
    
    # Node 1 receives chains from Node 2 and Node 3
    node1_replaced = node1.consensus([node2_data, node3_data])
    print(f"Node 1 chain replaced: {node1_replaced}")
    assert node1.is_valid_chain(node1.chain), "Node 1 chain should be valid after consensus"
    
    # Node 3 receives chains from Node 1 and Node 2
    node3_replaced = node3.consensus([node1_data, node2_data])
    print(f"Node 3 chain replaced: {node3_replaced}")
    assert node3.is_valid_chain(node3.chain), "Node 3 chain should be valid after consensus"
    
    # Node 2 receives chains from Node 1 and Node 3
    node2_replaced = node2.consensus([node1_data, node3_data])
    print(f"Node 2 chain replaced: {node2_replaced}")
    assert node2.is_valid_chain(node2.chain), "Node 2 chain should be valid after consensus"
    
    print("\nAfter consensus:")
    print(f"Node 1 chain length: {len(node1.chain)}")
    print(f"Node 2 chain length: {len(node2.chain)}")
    print(f"Node 3 chain length: {len(node3.chain)}")
    
    # Print vote counts after consensus
    print("\nVote counts after consensus:")
    print("Node 1 vote count:", node1.get_vote_count())
    print("Node 2 vote count:", node2.get_vote_count())
    print("Node 3 vote count:", node3.get_vote_count())
    
    # Print first few characters of each node's last block hash
    print("\nLast block hashes:")
    print(f"Node 1: {node1.chain[-1].hash[:15]}...")
    print(f"Node 2: {node2.chain[-1].hash[:15]}...")
    print(f"Node 3: {node3.chain[-1].hash[:15]}...")
    
    # Verify all nodes have the same chain length
    assert len(node1.chain) == len(node2.chain) == len(node3.chain), "Chain lengths don't match!"
    print("\nAll nodes have converged to the same chain length!")
    
    # Verify all nodes have the same last block hash
    assert node1.chain[-1].hash == node2.chain[-1].hash == node3.chain[-1].hash, "Chain contents don't match!"
    print("All nodes have the same blockchain content!")
    
    # Verify all nodes have the same vote count
    assert node1.get_vote_count() == node2.get_vote_count() == node3.get_vote_count(), "Vote counts don't match!"
    print("All nodes have the same vote count!")
    
    # Export the final blockchain to JSON
    chain_data = node1.get_chain_data()
    with open("blockchain_export.json", "w") as f:
        json.dump(chain_data, f, indent=2)
    print("\nFinal blockchain exported to 'blockchain_export.json'")


if __name__ == "__main__":
    print("===== BLOCKCHAIN VOTING SYSTEM DEMO =====")
    
    # Simulate basic blockchain operations
    blockchain = simulate_node()
    
    # Test tamper resistance
    tampered_blockchain = test_tamper_resistance()
    
    # Simulate a network with fork resolution
    simulate_fork_resolution()
    
    print("\nDemo completed successfully!")
