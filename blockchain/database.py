import plyvel
import json
from eth_utils import keccak
from trie import HexaryTrie

class Database:
    def __init__(self, db_path='dalgona.db'):
        # Initialize a single LevelDB database
        self.db = plyvel.DB(db_path, create_if_missing=True)
        
        # Create tries with prefixes to store different types of data within the same DB
        self.state_trie = HexaryTrie(self.db.prefixed_db(b'state_'))
        self.storage_trie = HexaryTrie(self.db.prefixed_db(b'storage_'))
        self.transaction_trie = HexaryTrie(self.db.prefixed_db(b'transaction_'))
        self.receipt_trie = HexaryTrie(self.db.prefixed_db(b'receipt_'))

    def get_latest_root(self):
        latest_root = self.db.get(b'state_latest_root')
        return latest_root.decode() if latest_root else None

    def add_block(self, block):
        block_key = f'block_{block.height}'.encode()
        self.db.put(block_key, json.dumps(block.to_dict()).encode())
        self.db.put(b'state_latest_root', str(block.height).encode())

    def get_last_block(self):
        last_height = self.db.get(b'state_latest_root').decode()
        last_block_data = self.db.get(f'block_{last_height}'.encode())
        return Block.from_dict(json.loads(last_block_data))

    def get_block(self, height):
        block_data = self.db.get(f'block_{height}'.encode())
        if block_data:
            return Block.from_dict(json.loads(block_data))
        return None

    def add_transaction(self, transaction, genesis=False):
        sender_balance = self.get_account_balance(transaction['sender'])
        total_cost = transaction['amount']
        if genesis or sender_balance >= total_cost:
            if not genesis:
                # Update sender balance
                self.update_account_balance(transaction['sender'], sender_balance - total_cost)
            
            # Update recipient balance
            recipient_balance = self.get_account_balance(transaction['recipient'])
            self.update_account_balance(transaction['recipient'], recipient_balance + transaction['amount'])
            
            # Add transaction to the transaction trie
            tx_key = f'{self.get_last_block().height}_{transaction["nonce"]}' if not genesis else f'0_{transaction["recipient"]}'
            self.transaction_trie[keccak(tx_key.encode())] = json.dumps(transaction).encode()

            # Recalculate and store the new state root
            if not genesis:
                new_state_root = self.recalculate_state_root()
                return True, new_state_root
            return True, None
        else:
            return False, None

    def get_account_balance(self, address):
        account_state = self.get_account_state(address)
        return account_state.get('balance', 0) if account_state else 0

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

    def update_account_balance(self, address, balance):
        self.update_account_state(address, balance=balance)

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

    def add_receipt_to_trie(self, block_height, transaction_receipt):
        receipt_key = keccak(f'{block_height}_{transaction_receipt["index"]}'.encode())
        self.receipt_trie[receipt_key] = json.dumps(transaction_receipt).encode()

    def get_receipt_from_trie(self, block_height, transaction_index):
        receipt_key = keccak(f'{block_height}_{transaction_index}'.encode())
        receipt_data = self.receipt_trie[receipt_key]
        if receipt_data:
            return json.loads(receipt_data)
        return None
