import hashlib
import time
import os

def clear_screen():
    os.system('clear')

def print_hash(block_hash, nonce, difficulty):
    clear_screen()
    print(f'Targeted hash: {"0" * difficulty}{"." * (64 - difficulty)}')
    print(f'Trying nonce --> {nonce}: hash: {block_hash}')
    time.sleep(0.1)

class Block:
    def __init__(self, block_number, transactions, previous_hash, difficulty):
        self.block_number = block_number
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.timestamp = time.time()
        self.hash = self.mine_block()

    def calculate_hash(self):
        block_header = f'{self.block_number}{self.transactions}{self.previous_hash}{self.timestamp}{self.nonce}'.encode()
        return hashlib.sha256(block_header).hexdigest()

    def mine_block(self):
        target = '0' * self.difficulty
        for self.nonce in range(2**32):  # Loop through all possible nonces
            block_hash = self.calculate_hash()
            print_hash(block_hash, self.nonce, self.difficulty)
            if block_hash[:self.difficulty] == target:
                print(f'MATCH found!!!!! Nonce --> {self.nonce}')
                print(f'Block hash: {block_hash}')
                return block_hash
        raise ValueError("No valid nonce found within the range")

block_number = 1
transactions = 'AV -> SS 20 ETH'
previous_hash = '0000000000000000000000000000000000000000000000000000000000000000'
difficulty = 2

block = Block(block_number, transactions, previous_hash, difficulty)
