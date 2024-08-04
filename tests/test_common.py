import plyvel
import trie
from trie import HexaryTrie
from eth_utils import keccak

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

db = plyvel.DB('mpt11_db', create_if_missing=True )
db_wrapper = PlyvelDictWrapper(db)
trie = HexaryTrie(db_wrapper)

trie[b'key1'] = b'value1'
print(f'Root after setting key1: {trie.root_hash.hex()}')

trie[b'key2'] = b'value255555555'
print(f'Root after setting key2: {trie.root_hash.hex()}')

trie[b'key3'] = b'value3'
print(f'Root after setting key3: {trie.root_hash.hex()}')

# value1 = trie[b'key1']
# value2 = trie[b'key2']
# value3 = trie[b'key3']

# # Print the retrieved values
# print(value1)  # Output: b'value1'
# print(value2)  # Output: b'value2'
# print(value3)  # Output: b'value3'









# mpt.put(b'key1', b'value1')

# mpt (b'key1', b'value1')
# mpt[b'key2'] = b'value2'
# mpt[b'key3'] = b'value3'

# # Serialize the MPT root hash
# root_hash = serialize_trie(mpt)

# # Store the latest root in LevelDB
# db.put(b'latest_root', root_hash)

# # Retrieve the latest root from LevelDB
# latest_root_hash = db.get(b'latest_root')
# print("Latest Root Hash:", latest_root_hash.hex())

# # Retrieve and print all key-value pairs
# for key in mpt.keys():
#     value = mpt[key]
#     print(f"Key: {key.decode()}, Value: {value.decode()}")

# Close the LevelDB
db.close()
