from eth_account import Account
from eth_account.messages import encode_defunct
from blockchain import Blockchain
from db import get_account_state,get_transaction,update_account_state


if __name__ == "__main__":
    blockchain = Blockchain()

    sender_address = '0xbd281AE5D72050dEB0243b91a81018709AFA1994'
    sender_key = '39092b4d8f20dd79c73928e501230b714a7730956755738be7523b7a19773ece'
    sender_account = Account.from_key(sender_key)

    update_account_state(sender_address, 1_000_000)

    receiver_account = Account.create()
    amount = 10
    message = f"{sender_account.address}:{receiver_account.address}:{amount}"
    message = encode_defunct(text=message)
    signature = Account.sign_message(message, sender_account.key).signature.hex()

    transaction = {
        'Sender': sender_account.address,
        'Receiver': receiver_account.address,
        'Amount': str(amount),
        'signature': signature
    }

    # Adding the transaction
    for x in range(10_000):
        txn_key = blockchain.add_transaction(transaction)
        print(f"{sender_account.address[-5:]} : {amount} --> {receiver_account.address[-5:]}")
        print(f"{sender_account.address[-5:]} Balance = {get_account_state(sender_account.address)['balance']}\n{receiver_account.address[-5:]} Balance = {get_account_state(receiver_account.address)['balance']}")
    
    # Check balances after the transaction
    

    # Display the created blocks
    for block in blockchain.blocks:
        print(block)

    if txn_key:
        retrieved_transaction = get_transaction(txn_key)
        if retrieved_transaction:
            print("Retrieved transaction:", retrieved_transaction)
        else:
            print("Transaction not found.")
    else:
        print("Invalid transaction.")