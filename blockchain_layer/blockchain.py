from hashlib import sha256
import json
import time
from .block import Block
from .transaction import Transaction

class Blockchain:
    """
    A class representing a blockchain for a decentralized voting system.
    
    This class manages the blockchain data structure, including:
    - Adding new blocks
    - Mining unconfirmed transactions
    - Validating the blockchain
    - Maintaining consensus between nodes
    
    Attributes:
        difficulty (int): The difficulty level for proof-of-work algorithm
        unconfirmed_transactions (list): List of unconfirmed Transaction objects
        chain (list): The blockchain (list of Block objects)
    """

    #difficulty = 2  # Difficulty level for proof-of-work

    def __init__(self,difficulty=4):
        """Initialize a new blockchain with empty transaction list and chain, default difficulty set to 2."""
        self.difficulty = difficulty  # Difficulty level for proof-of-work
        self.unconfirmed_transactions = []  # List of Transaction objects
        self.chain = []  # List of Block objects
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Creates the genesis block and appends it to the chain.
        The block has index 0, no transactions, and a valid hash.
        """
        
        genesis_block = Block(0, [], timestamp="2000-01-01 00:00:00", previous_hash="0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        """Returns the last block in the chain"""
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        Adds a block to the chain after verification.
        
        Args:
            block (Block): The block to be added
            proof (str): The hash value that satisfies our PoW criteria
            
        Returns:
            bool: True if block was added, False otherwise
        """
        previous_hash = self.last_block.hash

        # Check if the previous_hash field of the block matches
        # the hash of the latest block in the chain
        if previous_hash != block.previous_hash:
            return False

        # Check if the proof is valid
        if not self.is_valid_proof(block, proof):
            return False

        # If all checks pass, add the block to the chain
        block.hash = proof
        self.chain.append(block)
        return True

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        
        Args:
            block (Block): The block for which to find a valid hash
            
        Returns:
            str: The hash value that meets the difficulty criteria
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        """
        Adds a new transaction to the list of unconfirmed transactions.
        
        Args:
            transaction (Transaction): The transaction to add
        """
        self.unconfirmed_transactions.append(transaction)


    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        
        Args:
            block (Block): The block to check
            block_hash (str): The hash to verify
            
        Returns:
            bool: True if valid, False otherwise
        """
        if block.index == 0:
            return True  # Skip genesis block PoW

        if (block_hash.startswith('0' * self.difficulty) and
                block_hash == block.compute_hash()):
            #print(f"the block{block.index} satisfies the difficulty criteria")
            return True
        else:
            print(f"the block{block.index} does not satisfy the difficulty criteria")
            print(f"the block{block.index} hash is {block_hash}")
            print(f"the block{block.index} computed hash is {block.compute_hash()}")
            print(f"the difficulty is {self.difficulty}")
            return False

 
    def is_valid_chain(self, chain):
        """
        Checks if the entire blockchain is valid.
        
        Args:
            chain (list): List of Block objects
            
        Returns:
            bool: True if valid, False otherwise
        """
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            
            # Store the original hash
            
            
            # Compute what the hash should be based on the block's contents
            # computed_hash = block.compute_hash()
            
            # Check if the stored hash matches the computed hash and links properly
            if not self.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            previous_hash = block_hash

        return result

    def mine_block(self):
        """
        Interface to add pending transactions to the blockchain
        by adding them to a block and finding a valid proof of work.
        
        Returns:
            bool: True if mining was successful, False if no transactions to mine
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            previous_hash=last_block.hash
        )

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []
        return True
    
    def mine_malicious_block(self):
        """
        Interface to add pending transactions to the blockchain
        by adding them to a block and finding a valid proof of work.
        
        Returns:
            bool: True this malicious mining is successful
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(
            index=last_block.index + 1,
            transactions=self.unconfirmed_transactions,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            previous_hash=last_block.hash
        )

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.chain[-1].hash = "malicious_previous_hash"
        self.chain[-1].nounce = 0
        self.unconfirmed_transactions = []
        return True

    def get_chain_data(self):
        """
        Returns the blockchain data in a format that can be easily serialized.
        
        Returns:
            list: List of dictionaries containing block data
        """
        chain_data = []
        for block in self.chain:
            block_dict = {
                'index': block.index,
                'transactions': [tx.to_dict() for tx in block.transactions],
                'timestamp': block.timestamp,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'hash': block.hash
            }
            chain_data.append(block_dict)
        return chain_data

    def update_chain(self, chain_dicts_from_peers):
        """
        Implements the consensus algorithm.
        Resolves conflicts by accepting the longest valid chain from peers.
        
        Args:
            chain_dicts_from_peers (list): List of chain data from different peers
                Each item is a list of dictionaries representing blocks
                
        Returns:
            bool: True if our chain was replaced, False if our chain is the best
        """
        longest_chain = None
        current_len = len(self.chain)
        
        # Find the longest valid chain among all peers
        for chain_dict in chain_dicts_from_peers:
            try:
                # Skip if this is our own chain (same genesis block and same length or shorter)
                if len(chain_dict) <= len(self.chain) and chain_dict[0]['hash'] == self.chain[0].hash:
                    continue
                
                # Create a blockchain from the chain dict
                temp_blockchain = self.create_chain_from_dict(chain_dict)
                
                # Get the length of this chain
                chain_length = len(temp_blockchain.chain)
                
                # Check if this chain is longer and valid for consensus
                if chain_length > current_len:
                    # Verify the chain's integrity
                    is_valid = True
                    for i in range(1, chain_length):
                        current_block = temp_blockchain.chain[i]
                        prev_block = temp_blockchain.chain[i-1]
                        
                        # Check if the previous hash references are correct
                        if current_block.previous_hash != prev_block.hash:
                            is_valid = False
                            break
                        
                        # Check if the hash is valid for the block's content
                        computed_hash = current_block.compute_hash()
                        if not computed_hash.startswith('0' * self.difficulty) or computed_hash != current_block.hash:
                            is_valid = False
                            break
                    
                    if is_valid:
                        current_len = chain_length
                        longest_chain = temp_blockchain.chain
            except Exception as e:
                # Skip invalid chains, but print the error for debugging
                print(f"Error validating chain: {str(e)}")
                continue
        
        # Replace our chain if we found a longer valid chain
        if longest_chain:
            self.chain = longest_chain
            return True
            
        return False


    def create_chain_from_dict(self, chain_dict):
        """
        Recreates a blockchain from a list of dictionaries representing blocks.
        Useful when receiving chain data from other nodes.
        
        Args:
            chain_dict (list): List of dictionaries with block data
            
        Returns:
            temp_blockchain: A blockchain instance with the reconstructed chain
            
        Raises:
            Exception: If the chain dict is invalid
        """
        # Create a blockchain from the chain dict
        temp_blockchain = Blockchain()
        
        # Rebuild the chain manually from the dict
        for idx, block_data in enumerate(chain_dict):
            if idx == 0:
                # Recreate genesis block
                temp_blockchain.chain = []  # Clear the default genesis block
                genesis_block = Block(
                    index=block_data["index"],
                    transactions=[],
                    timestamp=block_data["timestamp"],
                    previous_hash=block_data["previous_hash"],
                    nonce=block_data["nonce"]
                )
                genesis_block.hash = block_data["hash"]
                temp_blockchain.chain.append(genesis_block)
                continue
            
            # Create Transaction objects from transaction data
            transactions = []
            for tx_data in block_data["transactions"]:
                transaction = Transaction(
                    voter_id=tx_data["voter_id"],
                    candidate_id=tx_data["candidate_id"],
                    timestamp=tx_data["timestamp"]
                )
                transactions.append(transaction)
                
            # Recreate the block
            block = Block(
                index=block_data["index"],
                transactions=transactions,
                timestamp=block_data["timestamp"],
                previous_hash=block_data["previous_hash"],
                nonce=block_data["nonce"]
            )
            
            # Set the hash directly
            block.hash = block_data["hash"]
            temp_blockchain.chain.append(block)

        return temp_blockchain

    def get_vote_count(self):
        """
        Counts votes for each candidate across the entire blockchain.
        
        Returns:
            dict: Dictionary with candidate_id as key and vote count as value
        """
        vote_count = {}
        
        # Skip genesis block (index 0) as it has no transactions
        for block in self.chain[1:]:
            for transaction in block.transactions:
                # Ensure we're only counting transactions that are votes
                if hasattr(transaction, 'candidate_id'):
                    candidate_id = transaction.candidate_id
                    
                    # Increment vote count for this candidate
                    if candidate_id in vote_count:
                        vote_count[candidate_id] += 1
                    else:
                        vote_count[candidate_id] = 1
        
        return vote_count

    def get_last_block_dict(self):
        """
        Returns the last block in the chain as a dictionary representation.
        Useful for broadcasting the newly mined block to peers.
        
        Returns:
            dict: Dictionary representation of the last block.
        """
        last_block = self.last_block
        block_dict = {
            'index': last_block.index,
            'transactions': [tx.to_dict() for tx in last_block.transactions],
            'timestamp': last_block.timestamp,
            'previous_hash': last_block.previous_hash,
            'nonce': last_block.nonce,
            'hash': last_block.hash
        }
        return block_dict

def block_from_dict(block_dict):
    """
    Reconstruct a Block object from a dictionary representation.
    
    Args:
        block_dict (dict): Dictionary containing block data.
        
    Returns:
        Block: Reconstructed Block object.
    """
    transactions = []
    for tx_data in block_dict.get('transactions', []):
        transaction = Transaction(
            voter_id=tx_data.get('voter_id'),
            candidate_id=tx_data.get('candidate_id'),
            timestamp=tx_data.get('timestamp')
        )
        transactions.append(transaction)
    
    block = Block(
        index=block_dict.get('index'),
        transactions=transactions,
        timestamp=block_dict.get('timestamp'),
        previous_hash=block_dict.get('previous_hash'),
        nonce=block_dict.get('nonce', 0)
    )
    block.hash = block_dict.get('hash')
    return block
