import plyvel
import hashlib
import time
import json

class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash

    def to_dict(self):
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'data': self.data,
            'hash': self.hash
        }

    @staticmethod
    def from_dict(data):
        return Block(
            data['index'],
            data['previous_hash'],
            data['timestamp'],
            data['data'],
            data['hash']
        )


class Blockchain:
    def __init__(self, db_path='blockchain.db'):
        self.db = plyvel.DB(db_path, create_if_missing=True)
        self.genesis_block = self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", int(time.time()), "Genesis Block", self.hash_block(0, "0", int(time.time()), "Genesis Block"))
        self.db.put(b'0', json.dumps(genesis_block.to_dict()).encode())
        self.db.put(b'latest_root', b'0')
        return genesis_block

    def hash_block(self, index, previous_hash, timestamp, data):
        block_string = f"{index}{previous_hash}{timestamp}{data}".encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_block(self, data):
        last_block = self.get_last_block()
        new_index = last_block.index + 1
        new_timestamp = int(time.time())
        new_hash = self.hash_block(new_index, last_block.hash, new_timestamp, data)
        new_block = Block(new_index, last_block.hash, new_timestamp, data, new_hash)
        self.db.put(str(new_index).encode(), json.dumps(new_block.to_dict()).encode())
        self.db.put(b'latest_root', str(new_index).encode())

    def get_last_block(self):
        last_index = self.db.get(b'latest_root').decode()
        last_block_data = self.db.get(last_index.encode())
        return Block.from_dict(json.loads(last_block_data))

    def get_block(self, index):
        block_data = self.db.get(str(index).encode())
        if block_data:
            return Block.from_dict(json.loads(block_data))
        return None

    def get_latest_root(self):
        latest_root = self.db.get(b'latest_root')
        return latest_root.decode() if latest_root else None

# Example Usage
blockchain = Blockchain()
blockchain.add_block("First block after genesis")
print(f"Latest root: {blockchain.get_latest_root()}")  # Should print the index of the latest block
