import time
from blockchain import Blockchain
from transaction import Transaction
from block import Block
from test_helpers import print_chain
from blockchain import block_from_dict

def test_single_block_propagation_and_fork_resolution():
    print("=== Test: Single Block Propagation and Fork Resolution with Network Simulation ===")

    # Create node1 with genesis + 1 block
    node1 = Blockchain()
    node1.add_new_transaction(Transaction("voter1", "candidateA"))
    node1.mine_block()
    print("Node 1 chain after mining 1 block:")
    print_chain(node1)
    assert len(node1.chain) == 2, "Node 1 should have 2 blocks (genesis + 1)"

    # Create node2 with genesis + 2 blocks (longer chain)
    node2 = Blockchain()
    node2.add_new_transaction(Transaction("voter2", "candidateB"))
    node2.mine_block()
    node2.add_new_transaction(Transaction("voter3", "candidateC"))
    node2.mine_block()
    print("Node 2 chain after mining 2 blocks:")
    print_chain(node2)
    assert len(node2.chain) == 3, "Node 2 should have 3 blocks (genesis + 2)"

    # Simulate node2 sending last block dict to node1 (single block propagation)
    node2_last_block_dict = node2.get_last_block_dict()
    node2_last_block = block_from_dict(node2_last_block_dict)
    node2_last_block_proof = node2_last_block.hash

    print("\nNode 1 attempts to add Node 2's last block (single block propagation) from dict...")
    add_block_result = node1.add_block(node2_last_block, node2_last_block_proof)
    print(f"Add block result: {add_block_result}")

    # If single block add fails but PoW is valid, do full chain sync (fork resolution)
    if not add_block_result and node2_last_block.hash.startswith('0' * node1.difficulty):
        print("Single block addition failed but PoW is valid, performing full chain sync and fork resolution on Node 1...")
        node2_chain_data = node2.get_chain_data()
        fork_resolved = node1.update_chain([node2_chain_data])
        print(f"Fork resolution result: {fork_resolved}")

    print(f"Node 1 chain length after sync: {len(node1.chain)}")
    assert len(node1.chain) == len(node2.chain), "Node 1 chain length should match Node 2 after sync"
    assert node1.is_valid_chain(node1.chain), "Node 1 chain should be valid after sync"

    # Test simpler case: Node1 mines a new block
    print("\nNode 1 mines a new block (simpler case)...")
    node1.add_new_transaction(Transaction("voter4", "candidateD"))
    mine_result = node1.mine_block()
    print(f"Mining result: {mine_result}")
    assert mine_result, "Mining should succeed"
    assert node1.is_valid_chain(node1.chain), "Chain should be valid after mining"
    print_chain(node1)

def test_malicious_block_addition():
    print("=== Test: Local Malicious Block Addition without Network Simulation ===")

    node = Blockchain()
    node.add_new_transaction(Transaction("voter1", "candidateA"))
    node.mine_block()
    print("Original chain:")
    print_chain(node)

    # Create a malicious block dict with incorrect previous_hash
    last_block_dict = node.get_last_block_dict()
    malicious_block_dict = last_block_dict.copy()
    malicious_block_dict['index'] += 1
    malicious_block_dict['previous_hash'] = "fake_previous_hash"
    malicious_block_dict['transactions'] = [{
        'voter_id': "maliciousVoter",
        'candidate_id': "maliciousCandidate",
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    }]
    # Recompute hash with PoW simulation
    malicious_block = block_from_dict(malicious_block_dict)
    nonce = 0
    proof = malicious_block.compute_hash()
    while not proof.startswith('0' * node.difficulty):
        malicious_block.nonce = nonce
        proof = malicious_block.compute_hash()
        nonce += 1
    malicious_block.hash = proof

    print("\nAttempting to add malicious block with incorrect previous_hash from dict...")
    add_result = node.add_block(malicious_block, proof)
    print(f"Add malicious block result: {add_result}")
    assert not add_result, "Malicious block should not be added"
    assert node.is_valid_chain(node.chain), "Chain should remain valid after rejecting malicious block"

def test_malicious_chain_addition():
    print("=== Test: Malicious Chain Addition with Network Simulation ===")

    node = Blockchain()
    node.add_new_transaction(Transaction("voter1", "candidateA"))
    node.mine_block()
    print("Original chain:")
    print_chain(node)

    # Create a malicious chain data with invalid block
    malicious_chain = node.get_chain_data()
    # Tamper with the second block's previous_hash to be invalid
    if len(malicious_chain) > 1:
        malicious_chain[1]['previous_hash'] = "fake_previous_hash"

    print("\nAttempting to replace chain with malicious chain data...")
    replaced = node.update_chain([malicious_chain])
    print(f"Chain replaced with malicious chain? {replaced}")
    assert not replaced, "Chain should not be replaced with malicious chain"
    assert node.is_valid_chain(node.chain), "Chain should remain valid after rejecting malicious chain"

def test_successful_single_block_propagation():
    print("=== Test: Successful Single Block Propagation with Network Simulation ===")

    # Create node1 with genesis + 1 block
    node1 = Blockchain()
    node1.add_new_transaction(Transaction("voter1", "candidateA"))
    node1.mine_block()
    print("Node 1 chain after mining 1 block:")
    print_chain(node1)
    assert len(node1.chain) == 2, "Node 1 should have 2 blocks (genesis + 1)"

    # Create node2 with same chain as node1 + 1 block
    node2 = Blockchain()
    # Sync node2 chain with node1 chain data
    node1_chain_data = node1.get_chain_data()
    node2.update_chain([node1_chain_data])
    # Add one more block to node2
    node2.add_new_transaction(Transaction("voter2", "candidateB"))
    node2.mine_block()
    print("Node 2 chain after mining 1 additional block:")
    print_chain(node2)
    assert len(node2.chain) == 3, "Node 2 should have 3 blocks (genesis + 2)"

    # Simulate node2 sending last block dict to node1 (single block propagation)
    node2_last_block_dict = node2.get_last_block_dict()
    node2_last_block = block_from_dict(node2_last_block_dict)
    node2_last_block_proof = node2_last_block.hash

    print("\nNode 1 attempts to add Node 2's last block (single block propagation) from dict...")
    add_block_result = node1.add_block(node2_last_block, node2_last_block_proof)
    print(f"Add block result: {add_block_result}")
    assert add_block_result, "Single block addition should succeed"
    assert len(node1.chain) == len(node2.chain) - 1 + 1, "Node 1 chain length should increase by 1"
    assert node1.is_valid_chain(node1.chain), "Node 1 chain should be valid after single block addition"

    print("No fork resolution needed as single block addition succeeded.")

if __name__ == "__main__":
    print("===== Running Blockchain Tests with Network Simulation =====")
    test_single_block_propagation_and_fork_resolution()
    test_malicious_block_addition()
    test_malicious_chain_addition()
    test_successful_single_block_propagation()
    print("\nAll tests completed successfully.")
