import time
import json
from blockchain.block import Block
from wallet.keys import save_keys_to_json
from database import Database

class Blockchain:
    def __init__(self, db_path='dalgona.db'):
        self.db = Database(db_path)
        self.genesis_block = self.create_genesis_block()

    def create_genesis_block(self):
        save_keys_to_json()  # Ensure the keys are generated

        with open('genesis_keys.json', 'r') as f:
            genesis_keys = json.load(f)

        initial_balances = {key['public_address']: key['initial_balance'] for key in genesis_keys}

        # Create initial transactions
        transactions = []
        for key in genesis_keys:
            tx = {
                'sender': '0x0',  # Genesis block has no sender
                'recipient': key['public_address'],
                'amount': key['initial_balance'],
                'timestamp': int(time.time()),
                'nonce': 0,
                'data': '',
                'v': 0, 'r': 0, 's': 0  # Signature components (0 for genesis transactions)
            }
            transactions.append(tx)

        # Add transactions to the transaction trie using add_transaction function
        for tx in transactions:
            self.db.add_transaction(tx, genesis=True)

        # Calculate transaction root
        transaction_root = self.db.transaction_trie.root_hash

        genesis_block = Block(
            height=0,
            previous_hash="0",
            timestamp=int(time.time()),
            data=json.dumps(transactions),
            hash=self.db.hash_block(0, "0", int(time.time()), json.dumps(transactions)),
            status="valid",
            extra_data="",
            burnt_fees=0,
            size=0,
            difficulty=1,
            gas_used=0
        )

        self.db.add_block(genesis_block)

        # Store the initial balances in the state trie
        for public_address, balance in initial_balances.items():
            self.db.update_account_state(public_address, balance=balance)

        self.db.recalculate_state_root()
        return genesis_block

    def add_block(self, data, status="valid", extra_data="", burnt_fees=0, size=0, difficulty=1, gas_used=0):
        last_block = self.db.get_last_block()
        new_height = last_block.height + 1
        new_timestamp = int(time.time())
        new_hash = self.db.hash_block(new_height, last_block.hash, new_timestamp, data)
        new_block = Block(
            height=new_height,
            previous_hash=last_block.hash,
            timestamp=new_timestamp,
            data=data,
            hash=new_hash,
            status=status,
            extra_data=extra_data,
            burnt_fees=burnt_fees,
            size=size,
            difficulty=difficulty,
            gas_used=gas_used
        )

        self.db.add_block(new_block)

    def add_transaction(self, transaction):
        return self.db.add_transaction(transaction)

    def get_last_block(self):
        return self.db.get_last_block()

    def get_block(self, height):
        return self.db.get_block(height)

    def get_latest_root(self):
        return self.db.get_latest_root()
