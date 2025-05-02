import hashlib
import json
import time
from .transaction import Transaction

class Block:
    """
    A class representing a block in the blockchain.
    Each block contains a list of Transactions objects, a timestamp, a reference to the previous block's hash,
    a nonce for mining, and the block's own hash.

    The block's hash is computed using SHA-256 hashing algorithm based on its contents.

    Variables:
        index (int): The index of the block in the blockchain.
        transactions (list): A list of Transaction objects contained in the block.
        timestamp (str): The time when the block was created, formatted as YYYY-MM-DD
        HH:MM:SS.   
        previous_hash (str): The hash of the previous block in the blockchain.
        nonce (int): A number used in the mining process to find a valid hash.
        hash (str): The hash of the block, computed using SHA-256.

    Usage:
        block = Block(index=1, transactions=[Transaction('voter1', 'A')], timestamp=time.strftime("%Y-%m-%d %H:%M:%S"), previous_hash='0')
        print(block.hash)  # Prints the hash of the block
        print(block.nonce)  # Prints the nonce used for mining
        print(block.hash)  # Prints the mined hash with leading zeros
    """
    def __init__(self, index, transactions: Transaction , timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions  # list of Transaction objects
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash() # a str representing the block's hash

    def compute_hash(self):
        """
        Compute SHA-256 hash of the block contents.
        """
        # Convert transactions to list of dicts for hashing
        transactions_dicts = [tx.to_dict() for tx in self.transactions]

        block_string = json.dumps({
            'index': self.index,
            'transactions': transactions_dicts,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest() # the length of the hash str is 64 characters

    
