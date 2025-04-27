import time
import hashlib
from block import Block
from blockchain_layer.transaction import Transaction

class Blockchain:
    """
    A class representing a blockchain for a decentralized voting system.
    The blockchain is a list of blocks, each containing a single vote transaction.
    The blockchain enforces consensus through Proof of Work and longest chain rule.
    Uses a Bitcoin-inspired block-by-block synchronization approach.
    
    Attributes:
        chain (list): A list of Block objects.
        difficulty (int): The number of leading zeros required in a valid block hash.
        orphan_blocks (dict): Blocks that have been received but can't be added yet because their parent is unknown.
        known_block_hashes (set): Hashes of blocks that we know about (either in chain or orphaned).
    """
    
    def __init__(self, difficulty=2):
        self.chain = []  # Starts empty - no genesis block
        self.difficulty = difficulty
        self.orphan_blocks = {}  # Hash -> Block mapping for blocks with unknown parents
        self.known_block_hashes = set()  # Set of all block hashes we know about
    
    def get_last_block(self):
        """
        Returns the last block in the chain.
        
        Returns:
            Block: The last block in the chain, or None if the chain is empty.
        """
        return self.chain[-1] if self.chain else None
    
    def get_block_by_hash(self, block_hash):
        """
        Returns a block by its hash, if it exists in our chain.
        
        Args:
            block_hash (str): The hash of the block to find.
            
        Returns:
            Block: The block if found, None otherwise.
        """
        for block in self.chain:
            if block.hash == block_hash:
                return block
        
        # Check orphan blocks too
        if block_hash in self.orphan_blocks:
            return self.orphan_blocks[block_hash]
            
        return None
    
    def add_block(self, block):
        """
        Adds a block to the chain after validation.
        
        Args:
            block (Block): The block to be added.
        
        Returns:
            bool: True if the block was added successfully, False otherwise.
        """
        # If we already know about this block, skip
        if block.hash in self.known_block_hashes:
            return True
            
        # Add to known hashes
        self.known_block_hashes.add(block.hash)
        
        # Verify the proof of work
        if not self.is_valid_proof(block, block.hash):
            print(f"Invalid proof for block: {block.hash}")
            return False
        
        # If chain is empty (this is the first block ever)
        if not self.chain:
            # For the first block, previous_hash should be "0"
            if block.previous_hash != "0":
                print(f"First block must have previous_hash='0', got {block.previous_hash}")
                return False
                
            self.chain.append(block)
            return True
            
        # If chain is not empty, verify block links to our chain
        last_block = self.get_last_block()
        
        # Direct extension of our chain
        if block.previous_hash == last_block.hash:
            self.chain.append(block)
            
            # Process any orphan blocks that might now connect
            self._process_orphans()
            return True
            
        # This block doesn't extend our chain - could be a fork or orphan
        parent_block = self.get_block_by_hash(block.previous_hash)
        
        if parent_block:
            # This is a fork - handle according to longest chain rule
            self._handle_fork(block)
            return True
        else:
            # This is an orphan block (parent unknown) - store it for later
            self.orphan_blocks[block.hash] = block
            return False
    
    def _process_orphans(self):
        """
        Process orphan blocks that might now connect to our chain.
        """
        # Keep track of orphans to remove
        processed = []
        
        # Check all orphans against the new last block
        last_block = self.get_last_block()
        for orphan_hash, orphan_block in self.orphan_blocks.items():
            if orphan_block.previous_hash == last_block.hash:
                # This orphan now connects
                self.chain.append(orphan_block)
                processed.append(orphan_hash)
                last_block = orphan_block  # Update in case of a chain of orphans
        
        # Remove processed orphans
        for orphan_hash in processed:
            del self.orphan_blocks[orphan_hash]
        
        # If we processed any orphans, try again in case more can connect now
        if processed:
            self._process_orphans()
    
    def _handle_fork(self, fork_block):
        """
        Handle a potential blockchain fork according to the longest chain rule.
        
        Args:
            fork_block (Block): A block that creates a fork.
        """
        # Reconstruct the fork
        fork_chain = []
        current_hash = fork_block.hash
        
        # Create a temporary mapping of all blocks we know about
        all_blocks = {block.hash: block for block in self.chain}
        all_blocks.update(self.orphan_blocks)
        all_blocks[fork_block.hash] = fork_block
        
        # Build the fork chain back to where it diverges
        while current_hash != "0":
            if current_hash not in all_blocks:
                # Fork is incomplete (has unknown blocks)
                return False
                
            block = all_blocks[current_hash]
            fork_chain.insert(0, block)
            current_hash = block.previous_hash
            
            # If we reach a block in our main chain, we've found the divergence point
            if self.get_block_by_hash(current_hash) and current_hash != "0":
                break
        
        # Find the common ancestor in our main chain
        common_ancestor_hash = fork_chain[0].previous_hash
        
        # Find index of common ancestor in main chain
        common_index = -1
        for i, block in enumerate(self.chain):
            if block.hash == common_ancestor_hash:
                common_index = i
                break
        
        if common_index == -1:
            # Shouldn't happen if we've properly tracked orphans
            return False
        
        # Determine which chain is longer
        main_chain_length = len(self.chain) - (common_index + 1)
        fork_chain_length = len(fork_chain)
        
        # If fork is longer, replace the portion of our chain after the common ancestor
        if fork_chain_length > main_chain_length:
            self.chain = self.chain[:common_index + 1] + fork_chain
            
            # Move blocks from old chain to orphan pool
            for i in range(common_index + 1, len(self.chain) - len(fork_chain) + 1):
                old_block = self.chain[i]
                self.orphan_blocks[old_block.hash] = old_block
            
            return True
        
        return False
    
    def is_valid_proof(self, block, block_hash):
        """
        Checks if a block hash is valid (satisfies the difficulty requirement).
        
        Args:
            block (Block): The block being validated.
            block_hash (str): The hash of the block.
        
        Returns:
            bool: True if the hash is valid, False otherwise.
        """
        # Verify the hash value
        return (block_hash.startswith('0' * self.difficulty) and
                block_hash == block.compute_hash())
    
    def mine_block(self, transactions):
        """
        Mines a new block with the given transactions.
        
        Args:
            transactions (list): A list of Transaction objects.
        
        Returns:
            Block: The mined block.
        """
        last_block = self.get_last_block()
        
        if not last_block:
            # This is the first block in the chain
            index = 0
            previous_hash = "0"
        else:
            index = last_block.index + 1
            previous_hash = last_block.hash
        
        block = Block(
            index=index,
            transactions=transactions,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            previous_hash=previous_hash
        )
        
        # Finding a valid nonce (mining)
        while True:
            if self.is_valid_proof(block, block.hash):
                break
            block.nonce += 1
            block.hash = block.compute_hash()
        
        return block
    
    def is_valid_chain(self, chain_to_validate):
        """
        Checks if a given chain is valid.
        
        Args:
            chain_to_validate (list): A list of Block objects.
        
        Returns:
            bool: True if the chain is valid, False otherwise.
        """
        if not chain_to_validate:
            return True  # Empty chain is valid according to our design
        
        # If first block, make sure previous_hash is "0"
        if chain_to_validate[0].previous_hash != "0":
            return False
        
        # Check each block
        for i in range(len(chain_to_validate)):
            block = chain_to_validate[i]
            
            # Check hash validity
            if not self.is_valid_proof(block, block.hash):
                return False
            
            # Check block linkage (except for first block)
            if i > 0:
                previous_block = chain_to_validate[i-1]
                if block.previous_hash != previous_block.hash:
                    return False
        
        return True
    
    def replace_chain(self, new_chain):
        """
        Replaces the local chain with a new chain if:
        1. The new chain is longer than the current chain
        2. The new chain is valid
        
        Args:
            new_chain (list): A list of Block objects.
        
        Returns:
            bool: True if the chain was replaced, False otherwise.
        """
        if len(new_chain) <= len(self.chain):
            return False
        
        if not self.is_valid_chain(new_chain):
            return False
        
        self.chain = new_chain
        
        # Update known blocks
        self.known_block_hashes = set()
        for block in self.chain:
            self.known_block_hashes.add(block.hash)
        
        return True
    
    def chain_to_dict(self):
        """
        Converts the chain to a list of dictionaries.
        Useful for serialization to JSON for network transmission.
        
        Returns:
            list: A list of dictionaries representing the chain.
        """
        chain_dict = []
        for block in self.chain:
            block_dict = {
                'index': block.index,
                'timestamp': block.timestamp,
                'transactions': [tx.to_dict() for tx in block.transactions],
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'hash': block.hash
            }
            chain_dict.append(block_dict)
        return chain_dict
    
    @staticmethod
    def chain_from_dict(chain_dict):
        """
        Reconstructs a chain from a list of dictionaries.
        
        Args:
            chain_dict (list): A list of dictionaries representing a chain.
        
        Returns:
            list: A list of Block objects.
        """
        chain = []
        for block_dict in chain_dict:
            # Convert dictionary transactions back to Transaction objects
            transactions = []
            for tx_dict in block_dict['transactions']:
                transaction = Transaction(
                    voter_id=tx_dict['voter_id'],
                    candidate_id=tx_dict['candidate_id'],
                    timestamp=tx_dict['timestamp']
                )
                transactions.append(transaction)
            
            # Recreate block
            block = Block(
                index=block_dict['index'],
                transactions=transactions,
                timestamp=block_dict['timestamp'],
                previous_hash=block_dict['previous_hash'],
                nonce=block_dict['nonce']
            )
            block.hash = block_dict['hash']
            chain.append(block)
        
        return chain
    
    def get_blocks_after(self, block_hash):
        """
        Gets all blocks in our chain that come after the specified block.
        Useful for block-by-block synchronization.
        
        Args:
            block_hash (str): Hash of the block to start after.
            
        Returns:
            list: List of blocks after the specified block, or the entire chain if 
                  block_hash is not found or is "0" (start from beginning).
        """
        if block_hash == "0":
            return self.chain
            
        for i, block in enumerate(self.chain):
            if block.hash == block_hash:
                return self.chain[i+1:]
                
        return self.chain  # If hash not found, return full chain
    
    def get_missing_blocks(self, block_hashes):
        """
        Returns blocks from our chain that the requester is missing.
        
        Args:
            block_hashes (list): List of block hashes the requester already has.
            
        Returns:
            list: List of blocks the requester is missing.
        """
        # Convert to set for O(1) lookups
        hash_set = set(block_hashes)
        
        # Find blocks we have that aren't in the requester's set
        missing_blocks = []
        for block in self.chain:
            if block.hash not in hash_set:
                missing_blocks.append(block)
                
        return missing_blocks
    
    def get_vote_tally(self):
        """
        Count votes for each candidate from all transactions in the blockchain.
        
        Returns:
            dict: A dictionary with candidate_ids as keys and vote counts as values.
        """
        tally = {}
        # Keep track of voters who have already voted to prevent double voting
        voters = set()
        
        # Go through all blocks and their transactions
        for block in self.chain:
            for tx in block.transactions:
                # Skip genesis block or empty transactions
                if not hasattr(tx, 'voter_id') or not hasattr(tx, 'candidate_id'):
                    continue
                    
                # Prevent double voting (only count first vote from each voter)
                if tx.voter_id in voters:
                    continue
                    
                voters.add(tx.voter_id)
                
                # Count the vote
                if tx.candidate_id in tally:
                    tally[tx.candidate_id] += 1
                else:
                    tally[tx.candidate_id] = 1
        
        return tally