import hashlib

def mine(latest_root: str) -> (int, str):
    nonce = 0
    hash_input = latest_root.encode()

    while True:
        hash_result = hashlib.sha256(hash_input).hexdigest()
        if hash_result.startswith("000"):
            return nonce, hash_result
        nonce += 1
        hash_input = hash_result.encode()
        print(hash_result)

# Example usage:
# latest_root = "abhiveer i am here pls test "
# nonce, mined_root = mine(latest_root)
# print(f"Nonce: {nonce}")
# print(f"Mined Root with difficulty: {mined_root}")
