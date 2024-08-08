import hashlib
import time
import json

class Block:
    def __init__(self, height, previous_hash, timestamp, data, hash, nonce=0, status="valid", extra_data="", burnt_fees=0, size=0, difficulty=1, gas_used=0):
        self.height = height
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash
        self.nonce = nonce
        self.status = status
        self.extra_data = extra_data
        self.burnt_fees = burnt_fees
        self.size = size
        self.difficulty = difficulty
        self.gas_used = gas_used

    def to_dict(self):
        return {
            'height': self.height,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'data': self.data,
            'hash': self.hash,
            'nonce': self.nonce,
            'status': self.status,
            'extra_data': self.extra_data,
            'burnt_fees': self.burnt_fees,
            'size': self.size,
            'difficulty': self.difficulty,
            'gas_used': self.gas_used
        }

    @staticmethod
    def from_dict(data):
        return Block(
            data['height'],
            data['previous_hash'],
            data['timestamp'],
            data['data'],
            data['hash'],
            data.get('nonce', 0),
            data.get('status', "valid"),
            data.get('extra_data', ""),
            data.get('burnt_fees', 0),
            data.get('size', 0),
            data.get('difficulty', 1),
            data.get('gas_used', 0)
        )
