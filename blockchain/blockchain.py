import plyvel
import hashlib
import time
import json
from eth_utils import keccak
from trie import HexaryTrie
from blockchain.block import Block
from blockchain.gas import GasCalculator
from wallet.transaction import Transaction
from wallet.keys import save_keys_to_json

class Blockchain:
    def __init__(self, db_path='dalgona.db'):
        # Initialize a single LevelDB database
        self.db = plyvel.DB(db_path, create_if_missing=True)
        
        # Create tries with prefixes to store different types of data within the same DB
        self.state_trie = HexaryTrie(self.db.prefixed_db(b'state_'))
        self.storage_trie = HexaryTrie(self.db.prefixed_db(b'storage_'))
        self.transaction_trie = HexaryTrie(self.db.prefixed_db(b'transaction_'))
        self.receipt_trie = HexaryTrie(self.db.prefixed_db(b'receipt_'))
        
        self.balances = {}
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
                'gas_price': 0,
                'gas_limit': 21000,  # Minimum gas limit for a transaction
                'timestamp': int(time.time()),
                'nonce': 0,
                'data': '',
                'v': 0, 'r': 0, 's': 0  # Signature components (0 for genesis transactions)
            }
            transactions.append(tx)

        # Add transactions to the transaction trie
        for index, tx in enumerate(transactions):
            tx_key = f'{0}_{index}'
            self.transaction_trie[keccak(tx_key.encode())] = json.dumps(tx).encode()

        # Calculate transaction root
        transaction_root = self.transaction_trie.root_hash

        genesis_block = Block(
            height=0,
            previous_hash="0",
            timestamp=int(time.time()),
            data=json.dumps(transactions),
            hash=self.hash_block(0, "0", int(time.time()), json.dumps(transactions)),
            status="valid",
            extra_data="",
            burnt_fees=0,
            size=0,
            difficulty=1,
            gas_used=0
        )

        self.db.put(b'block_0', json.dumps(genesis_block.to_dict()).encode())
        self.db.put(b'state_latest_root', b'0')

        # Store the initial balances in the state trie
        for public_address, balance in initial_balances.items():
            account_state = {
                'balance': balance,
                'nonce': 0,
                'storage_root': '',
                'code_hash': ''
            }
            self.state_trie[keccak(public_address.encode())] = json.dumps(account_state).encode()

        self.recalculate_state_root()
        return genesis_block

    def hash_block(self, height, previous_hash, timestamp, data, nonce=0):
        block_string = f"{height}{previous_hash}{timestamp}{data}{nonce}".encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_block(self, data, status="valid", extra_data="", burnt_fees=0, size=0, difficulty=1, gas_used=0):
        last_block = self.get_last_block()
        new_height = last_block.height + 1
        new_timestamp = int(time.time())
        new_hash = self.hash_block(new_height, last_block.hash, new_timestamp, data)
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

        # Calculate transaction root
        transaction_root = self.transaction_trie.root_hash

        self.db.put(f'block_{new_height}'.encode(), json.dumps(new_block.to_dict()).encode())
        self.db.put(b'state_latest_root', str(new_height).encode())

    def get_last_block(self):
        last_height = self.db.get(b'state_latest_root').decode()
        last_block_data = self.db.get(f'block_{last_height}'.encode())
        return Block.from_dict(json.loads(last_block_data))

    def get_block(self, height):
        block_data = self.db.get(f'block_{height}'.encode())
        if block_data:
            return Block.from_dict(json.loads(block_data))
        return None

    def get_latest_root(self):
        latest_root = self.db.get(b'state_latest_root')
        return latest_root.decode() if latest_root else None

    def add_transaction(self, transaction):
        sender_balance = self.balances.get(transaction.sender, 0)
        gas_calculator = GasCalculator(transaction.gas_price, transaction.gas_limit)
        total_cost = transaction.amount + gas_calculator.calculate_gas_cost()
        if sender_balance >= total_cost:
            # Update sender and recipient balances
            self.balances[transaction.sender] -= total_cost
            self.balances[transaction.recipient] = self.balances.get(transaction.recipient, 0) + transaction.amount
            
            # Update the state trie
            self.update_account_state(transaction.sender, balance=self.balances[transaction.sender])
            self.update_account_state(transaction.recipient, balance=self.balances[transaction.recipient])
            
            # Update gas used and miner balance
            transaction.gas_used = gas_calculator.gas_used
            self.balances['miner'] = self.balances.get('miner', 0) + transaction.gas_used * transaction.gas_price
            self.update_account_state('miner', balance=self.balances['miner'])
            
            # Add transaction to the transaction trie
            tx_key = f'{self.get_last_block().height}_{transaction["nonce"]}'
            self.transaction_trie[keccak(tx_key.encode())] = json.dumps(transaction).encode()

            # Recalculate and store the new state root
            new_state_root = self.recalculate_state_root()
            return True, new_state_root
        else:
            return False, None

    def get_account_state(self, address):
        account_data = self.state_trie[keccak(address.encode())]
        if account_data:
            return json.loads(account_data)
        return None

    def update_account_state(self, address, balance=None, nonce=None, storage_root=None, code_hash=None):
        account_state = self.get_account_state(address) or {}
        if balance is not None:
            account_state['balance'] = balance
        if nonce is not None:
            account_state['nonce'] = nonce
        if storage_root is not None:
            account_state['storage_root'] = storage_root
        if code_hash is not None:
            account_state['code_hash'] = code_hash
        self.state_trie[keccak(address.encode())] = json.dumps(account_state).encode()

    def recalculate_state_root(self):
        # Calculate the root hash of the state trie
        state_root_hash = self.state_trie.root_hash
        
        # Store the updated state root hash in the database
        self.db.put(b'state_latest_root', state_root_hash)

        return state_root_hash

    def get_storage_value(self, contract_address, storage_key):
        storage_data = self.storage_trie[keccak(f'{contract_address}_{storage_key}'.encode())]
        if storage_data:
            return json.loads(storage_data)
        return None

    def update_storage_value(self, contract_address, storage_key, value):
        self.storage_trie[keccak(f'{contract_address}_{storage_key}'.encode())] = json.dumps(value).encode()

    def add_transaction_to_trie(self, block_height, transaction):
        transaction_key = keccak(f'{block_height}_{transaction["index"]}'.encode())
        self.transaction_trie[transaction_key] = json.dumps(transaction).encode()

    def get_transaction_from_trie(self, block_height, transaction_index):
        transaction_key = keccak(f'{block_height}_{transaction_index}'.encode())
        transaction_data = self.transaction_trie[transaction_key]
        if transaction_data:
            return json.loads(transaction_data)
        return None

    def add_receipt_to_trie(self, block_height, transaction_receipt):
        receipt_key = keccak(f'{block_height}_{transaction_receipt["index"]}'.encode())
        self.receipt_trie[receipt_key] = json.dumps(transaction_receipt).encode()

    def get_receipt_from_trie(self, block_height, transaction_index):
        receipt_key = keccak(f'{block_height}_{transaction_index}'.encode())
        receipt_data = self.receipt_trie[receipt_key]
        if receipt_data:
            return json.loads(receipt_data)
        return None
