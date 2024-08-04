import hashlib
import json
import time
import leveldb
from libp2p import new_node
from libp2p.peer.peerinfo import info_from_p2p_addr
from libp2p.network.stream.net_stream import INetStream
from libp2p.network.stream.exceptions import StreamClosed
from libp2p.tools.constants import ID
from libp2p.crypto.keys import generate_key_pair
from coincurve import PrivateKey, PublicKey
import sha3

# Constants
DIFFICULTY = 2  # Adjust difficulty for mining

# Hashing
def keccak256(data):
    k = sha3.keccak_256()
    k.update(data)
    return k.hexdigest()

# Blockchain Components
class Block:
    def __init__(self, index, previous_hash, timestamp, data, nonce=0):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return keccak256(block_string.encode())

    def __repr__(self):
        return json.dumps(self.__dict__)

class Blockchain:
    def __init__(self, db_path='blockchain_db'):
        self.db = leveldb.LevelDB(db_path)
        self.chain = self.load_chain()

    def load_chain(self):
        chain = []
        try:
            for key, value in self.db.RangeIter():
                chain.append(json.loads(value))
        except:
            chain.append(self.create_genesis_block().__dict__)
        return chain

    def create_genesis_block(self):
        genesis_block = Block(0, "0", time.time(), "Genesis Block")
        self.db.Put(str(genesis_block.index).encode(), json.dumps(genesis_block.__dict__).encode())
        return genesis_block

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        last_block = self.get_last_block()
        new_block = Block(last_block['index'] + 1, last_block['hash'], time.time(), data)
        new_block = self.proof_of_work(new_block)
        self.chain.append(new_block.__dict__)
        self.db.Put(str(new_block.index).encode(), json.dumps(new_block.__dict__).encode())
        return new_block

    def proof_of_work(self, block):
        block.nonce = 0
        while not block.hash.startswith('0' * DIFFICULTY):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

# P2P Networking
async def handle_stream(stream: INetStream) -> None:
    try:
        async for data in stream.read():
            print("Received:", data.decode())
            await stream.write(f"Echo: {data.decode()}".encode())
    except StreamClosed:
        print("Stream closed")

async def run_node():
    node = await new_node(transport_opt=["/ip4/0.0.0.0/tcp/0"])
    node.set_stream_handler(protocol_id=ID, stream_handler=handle_stream)
    await node.listen()

    # Connect to a peer (replace with actual multiaddr)
    # peer_info = info_from_p2p_addr("/ip4/127.0.0.1/tcp/12345/p2p/Qm...")
    # await node.dial_peer(peer_info)

    print("Node is running. Peer ID:", node.get_id().pretty())
    await node.get_stream_handler(ID).wait_for_close()

# Key Management
def generate_keys():
    private_key = PrivateKey()
    public_key = private_key.public_key
    return private_key, public_key

def main():
    blockchain = Blockchain()
    blockchain.add_block("First block after genesis")
    blockchain.add_block("Second block after genesis")
    for block in blockchain.chain:
        print(block)

    private_key, public_key = generate_keys()
    print("Private Key:", private_key.to_hex())
    print("Public Key:", public_key.format(True).hex())

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_node())
    main()
