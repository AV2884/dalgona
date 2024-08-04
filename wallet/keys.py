import json
from eth_keys import keys
from eth_account import Account

def generate_key_pair():
    account = Account.create()
    private_key = account.key
    public_key = account.address
    return private_key, public_key

def save_keys_to_json(filename='genesis_keys.json', num_keys=10, initial_balance=1_000_000_000):
    key_data = []
    for _ in range(num_keys):
        private_key, public_key = generate_key_pair()
        key_data.append({
            'private_key': private_key.hex(),
            'public_address': public_key,
            'initial_balance': initial_balance
        })

    with open(filename, 'w') as f:
        json.dump(key_data, f, indent=4)

save_keys_to_json()
