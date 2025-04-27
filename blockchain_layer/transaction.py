import time

class Transaction:
    """
    A class representing a transaction in the voting system.
    Each transaction consists of a voter's ID, the candidate they voted for,
    and a timestamp indicating when the vote was cast.

    Attributes:
        voter_id (str): The ID of the voter.
        candidate_id (str): The ID of the candidate voted for.
        timestamp (str): The time when the vote was cast, formatted as YYYY-MM-DD HH:MM:SS.
    
    Usage: 
        tx = Transaction(voter_id="voter123", candidate_id="candidateA")
        print(tx.to_dict())  # {'voter_id': 'voter123', 'candidate_id': 'candidateA', 'timestamp': '2028-01-01 00:00:00'}
    """
    def __init__(self, voter_id, candidate_id, timestamp=None):
        self.voter_id = voter_id
        self.candidate_id = candidate_id
        self.timestamp = timestamp if timestamp else time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    def to_dict(self):
        return {
            'voter_id': self.voter_id,
            'candidate_id': self.candidate_id,
            'timestamp': self.timestamp
        }
