from web3 import Web3
import json
from eth_account.messages import encode_defunct
from eth_account import Account
import time
from save_data import save_Fee_to_excel, save_Latency_to_excel, save_Throughput_to_excel, save_fundingFee_to_excel
# see seperate scripts in invalidationTree.py and duplex_payments.py  !!!

# Connect to Ethereum (Ganache)
ganache_url = "http://127.0.0.1:8545"  # Adjust to your local Ganache instance
web3 = Web3(Web3.HTTPProvider(ganache_url))

"""
# Ensure connection is successful
if web3.is_connected():
    print("Connected to Ethereum network")
else:
    raise Exception("Failed to connect to Ethereum network")

# Contract ABI and Address (replace with actual values)
contract_address = "0xYourContractAddress"
with open('PaymentChannel_abi.json', 'r') as abi_file:                                 # ????
    contract_abi = json.load(abi_file)

# Load the contract
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Accounts (replace with actual addresses)
alice = web3.eth.accounts[0]  # Alice
bob = web3.eth.accounts[1]    # Bob


alice_private_key = 'your_alice_private_key'
bob_private_key = 'your_bob_private_key'"""

# This hash represents the state of balances between Alice and Bob in the payment channel. 
def sign_node(sender_private_key, alice_balance, bob_balance):
    # Hash the transaction data
    tx_data = {'alice_balance': alice_balance, 'bob_balance': bob_balance}
    message_hash = Web3.solidity_keccak(['uint256', 'uint256'], [tx_data['alice_balance'], tx_data['bob_balance']])
    message_hash = encode_defunct(message_hash)
    #message_hash = encode_defunct(hexstr=message_hash.hex())
    # Sign the message
    
    signed_message = web3.eth.account.sign_message(message_hash, private_key=sender_private_key) #???
    return signed_message

# Function to build the invalidation tree
def build_invalidation_tree(alice_fund, bob_fund, depth, max_timelock, alice_private_key, bob_private_key):
    
    """
    Constructs the first branch of the invalidation tree (T1,k, T2,k, ..., Td,k).
    The leaf node (d=3) has two outputs: one for Alice's balance and one for Bob's balance.
    """
    tree_initial = []
    
    for i in range(1, depth + 1):  # Depth of 3
        timelock = max_timelock
        
        # Create the branch node with Alice and Bob's balances
        branch_node = {
            'depth': i,
            'timelock': timelock,
            'tx_data': {
                'alice_balance': alice_fund,
                'bob_balance': bob_fund
            },
            'signatures': {}
        }

        """# Alice signs the transaction
        signature_alice = sign_node(alice_private_key, alice_fund, bob_fund)
        print(f"Alice's signature: {signature_alice.signature.hex()}")
        #branch_node['signatures']['alice'] = signature_alice.signature.hex()

        # Bob signs the transaction
        signature_bob = sign_node(bob_private_key, alice_fund, bob_fund)
        print(f"Bob's signature: {signature_alice.signature.hex()}")
        #branch_node['signatures']['bob'] = signature_bob.signature.hex()"""
        # Signatures by Alice and Bob
        signature_alice = sign_node(alice_private_key, alice_fund, bob_fund)
        signature_bob = sign_node(bob_private_key, alice_fund, bob_fund)
        branch_node['signatures']['alice'] = signature_alice.signature.hex()
        branch_node['signatures']['bob'] = signature_bob.signature.hex()

        # Generate Transaction ID (Using Hash of Transaction Data as an Example)
        branch_node['txid'] = Web3.solidity_keccak(['uint256', 'uint256', 'uint256'], 
                                                   [alice_fund, bob_fund, timelock]).hex()

        # Append the branch node to the tree
        tree_initial.append(branch_node)

    
    # Return the last (leaf) node
    leaf_node = tree_initial[-1]
    leaf_txid = leaf_node["txid"]

    filename = "invalidation_tree_with_signatures.json"
    with open(filename, 'w') as file:
        json.dump(tree_initial, file, indent=4)
    

    return tree_initial, leaf_node


tree_initial, leaf_node = build_invalidation_tree(
    alice_fund=1, bob_fund=2, depth=3, max_timelock=100, 
    alice_private_key='0x68747a0d78cd7a60ded4b9ec0ce0afe81643787f311d14dee2a72a609664fc52', bob_private_key='0xbfe12bdc4eb48d42ccad77e3285a220f47284c8528d0e397154b5f432c94bfa9'
)
filename = "invalidation_tree_with_signatures.json"
 
with open(filename, 'w') as file:
    json.dump(tree_initial, file, indent=4)
# Initialize Invalidation Tree 
"""
alice_fund = web3.to_wei(1, 'ether')  # Alice's initial funding for her side of the channel
bob_fund = web3.to_wei(2, 'ether')    # Bob's initial funding for his side of the channel
depth = 3
max_timelock = 100

# Build invalidation tree and retrieve the leaf node output
tree_initial, leaf_txid = build_invalidation_tree(alice_fund, bob_fund, depth, max_timelock)
# Save the entire tree to a JSON file for later use or modification
with open('invalidation_tree_with_signatures.json', 'w') as f:
    json.dump(tree_initial, f, indent=4) """


# Retrieve balances from leaf node




#AMOUNT_A_TO_B = web3.to_wei(0.2, 'ether')  # Alice sends 0.2 ETH to Bob
#AMOUNT_B_TO_A = web3.to_wei(0.35, 'ether')  # Bob sends 0.35 ETH to Alice

# Example function to simulate signing a message for off-chain payments
def sign_payment(sender_private_key, sender, recipient, alice_balance, bob_balance):
    # Create a hashed message for signature
    message_hash = web3.solidity_keccak(['address', 'address', 'uint256', 'uint256'], [sender, recipient, alice_balance, bob_balance])
    message_hash = encode_defunct(message_hash)
    # Sign the message with sender's private key (Ganache's account key used)
    signature = web3.eth.account.sign_message(message_hash, private_key=sender_private_key)
    #signature_bob = web3.eth.account.sign_message(message_hash, private_key=sender_private_key)
    return signature.signature


def duplex_payments(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key):
    Cab_alice_balance = leaf_node["tx_data"]["alice_balance"]  # Alice's balance from the leaf node
    Cba_bob_balance = leaf_node["tx_data"]["bob_balance"]      # Bob's balance from the leaf node
    Cab_bob_balance = web3.to_wei(0, 'ether')
    Cba_alice_balance = web3.to_wei(0, 'ether')
    alice = web3.eth.accounts[0]  # Alice
    bob = web3.eth.accounts[1]    #
    target_A_to_B = web3.to_wei(0.999995, 'ether')
    target_B_to_A = web3.to_wei(0.99990, 'ether')

    start_time = time.time()
    i = 0
    # Simulate off-chain payments in a loop
    while Cab_alice_balance >= target_A_to_B and Cba_bob_balance >= target_B_to_A:
        

        Cab_alice_balance -= AMOUNT_A_TO_B
        Cab_bob_balance += AMOUNT_A_TO_B
        i += 1
        # Alice to Bob payments, exchange keys for every transaction
        aliceAB=sign_payment(alice_private_key, alice, bob, Cab_alice_balance, Cab_bob_balance)
        bobAB=sign_payment(bob_private_key, bob, alice, Cab_alice_balance, Cab_bob_balance)
        # Verify and apply the off-chain transaction logic here
        
#        print(f"New balance after Alice's payment: Alice {web3.from_wei(Cab_alice_balance, 'ether')} ETH, Bob {web3.from_wei(Cab_bob_balance, 'ether')} ETH")

        Cba_bob_balance -= AMOUNT_B_TO_A
        Cba_alice_balance += AMOUNT_B_TO_A
        i += 1
        # Bob to Alice payments
        bobBA=sign_payment(bob_private_key, bob, alice, Cba_alice_balance, Cba_bob_balance)
        aliceBA=sign_payment(alice_private_key, alice, bob, Cba_alice_balance, Cba_bob_balance)
        # Verify and apply the off-chain transaction logic here
        
#        print(f"New balance after Bob's payment: Bob {web3.from_wei(Cba_bob_balance, 'ether')} ETH, Alice {web3.from_wei(Cba_alice_balance, 'ether')} ETH")

        #time.sleep(1)  # Simulate some delay between payments

    end_time = time.time()  
    throughput = i / (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"Throughput: {throughput}")

    # Once the balances are exhausted, the channel can be closed.7
    print("The fund of one Channel exhausted, resetting the channel...")
    update_A_Balance = Cab_alice_balance + Cba_alice_balance
    update_B_Balance = Cba_bob_balance + Cab_bob_balance
    print(f"Alice's new balance: {web3.from_wei(update_A_Balance, 'ether')} ETH, Bob's new balance is {web3.from_wei(update_B_Balance, 'ether')} ETH")

    return update_A_Balance, update_B_Balance, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA

def duplex_payments_HighValue(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key):
    Cab_alice_balance = leaf_node["tx_data"]["alice_balance"]  # Alice's balance from the leaf node
    Cba_bob_balance = leaf_node["tx_data"]["bob_balance"]      # Bob's balance from the leaf node
    Cab_bob_balance = web3.to_wei(0, 'ether')
    Cba_alice_balance = web3.to_wei(0, 'ether')
    alice = web3.eth.accounts[0]  # Alice
    bob = web3.eth.accounts[1]    #
    target_value_A = web3.to_wei(95000, 'ether')
    target_value_B = web3.to_wei(150000, 'ether')
    start_time = time.perf_counter()
    i = 0
    # Simulate off-chain payments in a loop
    while Cab_alice_balance >= target_value_A and Cba_bob_balance >= target_value_B:
        i += 1
       
        # Verify and apply the off-chain transaction logic here
        Cab_alice_balance -= AMOUNT_A_TO_B
        Cab_bob_balance += AMOUNT_A_TO_B
        #print(f"New balance after Alice's payment: Alice {web3.from_wei(Cab_alice_balance, 'ether')} ETH, Bob {web3.from_wei(Cab_bob_balance, 'ether')} ETH")
         # Alice to Bob payments
        #signature_Alice_Cab = sign_payment(alice_private_key, alice, bob, Cab_alice_balance, Cab_bob_balance)
        #signature_Bob_Cab = sign_payment(bob_private_key, alice, bob, Cab_alice_balance, Cab_bob_balance)
        sign_payment(alice_private_key, alice, bob, Cab_alice_balance, Cab_bob_balance)
        sign_payment(bob_private_key, alice, bob, Cab_alice_balance, Cab_bob_balance)

      
        # Verify and apply the off-chain transaction logic here
        Cba_bob_balance -= AMOUNT_B_TO_A
        Cba_alice_balance += AMOUNT_B_TO_A
        #print(f"New balance after Bob's payment: Bob {web3.from_wei(Cba_bob_balance, 'ether')} ETH, Alice {web3.from_wei(Cba_alice_balance, 'ether')} ETH")
          # Bob to Alice payments
        #signature_Bob_Cba = sign_payment(bob_private_key, bob, alice, Cba_alice_balance, Cba_bob_balance)
        #signature_Alice_Cba = sign_payment(alice_private_key, bob, alice, Cba_alice_balance, Cba_bob_balance)
        sign_payment(bob_private_key, bob, alice, Cba_alice_balance, Cba_bob_balance)
        sign_payment(alice_private_key, bob, alice, Cba_alice_balance, Cba_bob_balance)
        #time.sleep(1)  # Simulate some delay between payments

    end_time = time.perf_counter()
    throughput = i / (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"Throughput: {throughput}")

    # Once the balances are exhausted, the channel can be closed.7
    print("The fund of one Channel exhausted, resetting the channel...")
    update_A_Balance = Cab_alice_balance + Cba_alice_balance
    update_B_Balance = Cba_bob_balance + Cab_bob_balance
    print(f"Alice's new balance: {web3.from_wei(update_A_Balance, 'ether')} ETH, Bob's new balance is {web3.from_wei(update_B_Balance, 'ether')} ETH")

    return update_A_Balance, update_B_Balance




def confirm_signatures_alice(contract):
    tx_hash = contract.functions.aliceConfirmsSignatures().transact({
        'from': web3.eth.accounts[0]  # Alice's address
    })
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Alice confirmed signatures")
    #print(f"Alice confirmed signatures: {receipt}")

# Bob confirms off-chain signatures on-chain
def confirm_signatures_bob(contract):
    tx_hash = contract.functions.bobConfirmsSignatures().transact({
        'from': web3.eth.accounts[1]  # Bob's address
    })
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Bob confirmed signatures")
    #print(f"Bob confirmed signatures: {receipt}")

# Confirm signatures (on-chain interaction)
#confirm_signatures_alice()
#confirm_signatures_bob()

# Both Alice and Bob have confirmed, now finalize the funding transaction
def sign_funding_transaction(contract, alice_fund, bob_fund):
    tx_hash = contract.functions.signFundingTransaction(alice_fund, bob_fund).transact({
        'from': web3.eth.accounts[0],  # Alice or Bob can call this
        'gas': 3000000
    })
    receipt_FundingTX = web3.eth.wait_for_transaction_receipt(tx_hash)


    print(f"Funding transaction completed")
    #print(f"Funding transaction completed: {receipt}")
    gas_used = receipt_FundingTX.gasUsed
    gas_price = web3.to_wei('42.36', 'gwei')

    funding_transaction_fee = gas_used * gas_price
    funding_transaction_fee = web3.from_wei(funding_transaction_fee, "ether")
    save_fundingFee_to_excel(funding_transaction_fee)

    print(f'Funding Transaction fee: {funding_transaction_fee} ETH')
    return funding_transaction_fee, receipt_FundingTX

# Call the on-chain function to finalize funding
#sign_funding_transaction()