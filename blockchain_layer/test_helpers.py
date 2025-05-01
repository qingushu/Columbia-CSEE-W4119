def print_chain(blockchain):
    """Helper function to print blockchain details."""
    print(f"\nBlockchain length: {len(blockchain.chain)}")
    for i, block in enumerate(blockchain.chain):
        print(f" Block #{i} - Hash: {block.hash[:15]}..., Prev: {block.previous_hash[:15]}..., Nonce: {block.nonce}, Txns: {len(block.transactions)}")
