from web3 import Web3
import json
import time

# Connect to Ethereum (Ganache)
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Load the leaf node data from the file (output from Script 1)
with open('leaf_node_data.json', 'r') as f:
    leaf_node_data = json.load(f)

# Initialize balances from leaf node
Cab_alice_balance = leaf_node_data["alice_balance"]
Cba_bob_balance = leaf_node_data["bob_balance"]

AMOUNT_A_TO_B = web3.toWei(0.2, 'ether')  # Alice sends 0.2 ETH to Bob
AMOUNT_B_TO_A = web3.toWei(0.35, 'ether')  # Bob sends 0.35 ETH to Alice

# Example function to simulate signing a message for off-chain payments
def sign_payment(sender, recipient, amount):
    message_hash = web3.solidityKeccak(['address', 'address', 'uint256'], [sender, recipient, amount])
    # Simulated signature (replace with actual signing logic)
    signature = web3.eth.account.signHash(message_hash, private_key="private_key_here")  # Add real private keys
    return signature

# Simulate off-chain payments in a loop
while Cab_alice_balance >= AMOUNT_A_TO_B and Cba_bob_balance >= AMOUNT_B_TO_A:
    # Alice to Bob payments
    signature_Alice = sign_payment(web3.eth.accounts[0], web3.eth.accounts[1], AMOUNT_A_TO_B)
    Cab_alice_balance -= AMOUNT_A_TO_B
    Cba_bob_balance += AMOUNT_A_TO_B
    print(f"New balance after Alice's payment: Alice {web3.fromWei(Cab_alice_balance, 'ether')} ETH, Bob {web3.fromWei(Cba_bob_balance, 'ether')} ETH")

    # Bob to Alice payments
    signature_Bob = sign_payment(web3.eth.accounts[1], web3.eth.accounts[0], AMOUNT_B_TO_A)
    Cba_bob_balance -= AMOUNT_B_TO_A
    Cab_alice_balance += AMOUNT_B_TO_A
    print(f"New balance after Bob's payment: Alice {web3.fromWei(Cab_alice_balance, 'ether')} ETH, Bob {web3.fromWei(Cba_bob_balance, 'ether')} ETH")

    time.sleep(1)  # Simulate delay between payments

print("Channel exhausted, closing the channel.")
