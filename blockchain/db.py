import json
from eth_account import Account
from eth_account.messages import encode_defunct
from typing import Dict, Optional
from eth_utils import keccak
import plyvel
from trie import HexaryTrie

class PlyvelDictWrapper:
    def __init__(self, db):
        self.db = db

    def __getitem__(self, key):
        value = self.db.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        self.db.put(key, value)

    def __delitem__(self, key):
        if self.db.get(key) is None:
            raise KeyError(key)
        self.db.delete(key)

    def __contains__(self, key):
        return self.db.get(key) is not None

# Initialize the LevelDB database
db = plyvel.DB('b1', create_if_missing=True)

# Load the existing root hash from the database, or use the default empty root
root_key = b'state_latest_root'
existing_root = db.get(root_key) or HexaryTrie().root_hash

# Initialize the tries with the wrapper
state_trie = HexaryTrie(PlyvelDictWrapper(db.prefixed_db(b'state_')), root_hash=existing_root)
storage_trie = HexaryTrie(PlyvelDictWrapper(db.prefixed_db(b'storage_')))
transaction_trie = HexaryTrie(PlyvelDictWrapper(db.prefixed_db(b'transaction_')))
receipt_trie = HexaryTrie(PlyvelDictWrapper(db.prefixed_db(b'receipt_')))

def get_latest_state_trie_root() -> str:
    return state_trie.root_hash.hex()

def verify_signature(transaction: Dict[str, str]) -> bool:
    message = f"{transaction['Sender']}:{transaction['Receiver']}:{transaction['Amount']}"
    encoded_message = encode_defunct(text=message)
    recovered_address = Account.recover_message(encoded_message, signature=transaction['signature'])
    return recovered_address == transaction['Sender']

def get_account_state(address: str) -> Dict[str, int]:
    state = state_trie.get(address.encode())
    if state:
        return json.loads(state)
    return {"balance": 0, "nonce": 0}

def get_balance(address: str):
    state = get_account_state(address)
    return state['balance']

def update_account_state(address: str, balance_change: int):
    state = get_account_state(address)
    state['balance'] += balance_change
    state['nonce'] += 1
    state_trie[address.encode()] = json.dumps(state).encode()
    
    # Persist the latest state trie root in the database
    db.put(root_key, state_trie.root_hash)

def add_transaction(transaction: Dict[str, str]) -> Optional[str]:
    if verify_signature(transaction):
        sender = transaction['Sender']
        receiver = transaction['Receiver']
        amount = int(transaction['Amount'])

        sender_state = get_account_state(sender)
        if sender_state['balance'] < amount:
            print("Insufficient balance")
            return None

        update_account_state(sender, -amount)
        update_account_state(receiver, amount)

        transaction_data = json.dumps(transaction)

        txn_key = keccak(transaction_data.encode()).hex()

        transaction_trie[txn_key.encode()] = transaction_data.encode()
        
        return txn_key
    return None

def get_transaction(txn_key: str) -> Optional[Dict[str, str]]:
    txn_data = transaction_trie.get(txn_key.encode())
    if txn_data:
        return json.loads(txn_data)
    return None

if __name__ == "__main__":
    # sender_account = Account.create()
    sender_address = '0xbd281AE5D72050dEB0243b91a81018709AFA1994'
    sender_key = '39092b4d8f20dd79c73928e501230b714a7730956755738be7523b7a19773ece'
    sender_account = Account.from_key(sender_key)

    receiver_account = Account.create()
    amount = 10
    # print(get_latest_state_trie_root())
    # update_account_state(sender_account.address, 100)
    message = f"{sender_account.address}:{receiver_account.address}:{amount}"
    message = encode_defunct(text=message)
    signature = Account.sign_message(message, sender_account.key).signature.hex()

    transaction = {
        'Sender': sender_account.address,
        'Receiver': receiver_account.address,
        'Amount': amount,
        'signature': signature
    }

    # print(f"Sender's Address: {sender_account.address}")
    # print(f"Receiver's Address: {receiver_account.address}")
    # print(f"Sender's Private Key: {sender_account.key.hex()}")
    # print(f"Signature: {signature}")

    txn_key = add_transaction(transaction)
    print(f"{sender_account.address[-5:]} : {amount} --> {receiver_account.address[-5:]}")
    print(f"{sender_account.address[-5:]} Balance = {get_account_state(sender_account.address)['balance']}\n{receiver_account.address[-5:]} Balance = {get_account_state(receiver_account.address)['balance']}")
    if txn_key:
        # print(f"Transaction added successfully with key: {txn_key}")
        retrieved_transaction = get_transaction(txn_key)
        # if retrieved_transaction:
        #     print("Retrieved transaction:", retrieved_transaction)
        # else:
        #     print("Transaction not found.")
    else:
        print("Invalid transaction.")
