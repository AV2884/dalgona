from typing import Dict, Optional
from db import add_transaction as add_tx_to_db,get_latest_state_trie_root
# from p2p import publish
from mine import mine
import json

FILE_NAME = "block.json"

class Blockchain:
    def __init__(self):
        self.transactions = []
        self.blocks = []
        self.block_number = 0

    def add_transaction(self, transaction: Dict[str, str]) -> Optional[str]:
        txn_key = add_tx_to_db(transaction)
        if txn_key:
            self.transactions.append(transaction)
            
            # Check if we have 10 transactions, then create a block
            if len(self.transactions) == 10:
                self.create_block()
            return txn_key
        return None

    def create_block(self):
        self.block_number += 1

        nonce,root = mine(get_latest_state_trie_root())
        block = {
            'block_number': self.block_number,
            'data': self.transactions,  
            'nonce': nonce,
            'root':root,
            'state_root':get_latest_state_trie_root()
        }        
        self.blocks.append(block)
        with open(FILE_NAME, "w") as file:
            json.dump(block, file, indent=4)
        # publish(FILE_NAME)
        self.transactions.clear()

