from web3 import Web3
import json
import time

from reset import modify_branch
from establishment import duplex_payments, duplex_payments_HighValue, build_invalidation_tree, confirm_signatures_alice, confirm_signatures_bob, sign_funding_transaction
from closure import closureChannel


# Connect to Ethereum (Ganache)
ganache_url = "http://127.0.0.1:8545"  # Adjust to your local Ganache instance
web3 = Web3(Web3.HTTPProvider(ganache_url))


# Ensure connection is successful
if web3.is_connected():
    print("Connected to Ethereum network")
else:
    raise Exception("Failed to connect to Ethereum network")

# Contract ABI and Address (replace with actual values)
contract_address = "0x680774AB298f5b7Df6Edb6dfE029703c67cd7EdC"
with open('artifacts/contracts/BidirectionalPaymentChannel.sol/BidirectionalPaymentChannel.json', 'r') as abi_file:
    contract_data = json.load(abi_file)
abi_data = contract_data['abi']
# Load the contract
contract = web3.eth.contract(address=contract_address, abi=abi_data)

# Accounts (replace with actual addresses)
alice = web3.eth.accounts[0]  # Alice
bob = web3.eth.accounts[1]    # Bob
depth = 3
max_timelock = 100
safe_margin = 5

### --- Low Value ---
alice_fund = web3.to_wei(1, 'ether')  # Alice's initial funding for her side of the channel
bob_fund = web3.to_wei(2, 'ether')    # Bob's initial funding for his side of the channel
AMOUNT_A_TO_B = web3.to_wei(60, 'gwei')  # Alice sends 0.2 ETH to Bob
AMOUNT_B_TO_A = web3.to_wei(80, 'gwei')  # Bob sends 0.35 ETH to Alice

### --- High value : Remember to modify the deploy.js  ---
#alice_fund = web3.to_wei(100000, 'ether')  # Alice's initial funding for her side of the channel
#bob_fund = web3.to_wei(200000, 'ether')    # Bob's initial funding for his side of the channel
#AMOUNT_A_TO_B = web3.to_wei(300, 'ether')  # Alice sends 0.2 ETH to Bob
#AMOUNT_B_TO_A = web3.to_wei(500, 'ether')  # Bob sends 0.35 ETH to Alice

alice_private_key = '0xa35d8f18431d53c18fcae8cfae43db953629b23a13574030e27e4a9be2b3e5cb'
bob_private_key = '0xb436bebe368a8159e456e4a79a0f22ecc83c895c33c0d5c13229465feed63787'
#with open('invalidation_tree_with_signatures.json', 'r') as f:
 #   tree_initial = json.load(f)

#tree = tree_initial

def main():
    """
    alice_balance_in_contract = contract.functions.getAliceDeposit().call()
    bob_balance_in_contract = contract.functions.getBobBalance().call()
    print(f"Alice Balance in Contract: {alice_balance_in_contract}")
    print(f"Bob Balance in Contract: {bob_balance_in_contract}")

    """
    tree_initial, leaf_node = build_invalidation_tree(alice_fund, bob_fund, depth, max_timelock, alice_private_key, bob_private_key)
    #print(leaf_node)
    # Save the entire tree to a JSON file for later use or modification
    filename = "invalidation_tree_with_signatures.json"
 
    with open(filename, 'w') as file:
        json.dump(tree_initial, file, indent=4)
    print("create JSON successfully")

    confirm_signatures_alice(contract)
    confirm_signatures_bob(contract)
    
    
    # 1. funding Transaction broadcast
    sign_funding_transaction(contract, alice_fund, bob_fund)

    update_A_Balance, update_B_Balance, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA = duplex_payments(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key)  
    #update_A_Balance, update_B_Balance, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA = duplex_payments_HighValue(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key)  
    
    #alice_account = web3.eth.account.from_key(alice_private_key)
    #alice_address = alice_account.address
    #print(f"alice_address: {alice_address}")
    #print(f"alice: {alice}")
    #bob_account = web3.eth.account.from_key(bob_private_key)
  

    #balance_A = web3.eth.get_balance(alice_address)
    
    #balance_B = web3.eth.get_balance(bob_address)
    #print(f"Alice's balance: {web3.from_wei(balance_A, 'ether')} ETH")
    
    #print(f"Bob's balance: {web3.from_wei(balance_B, 'ether')} ETH")

    for i in range (0, depth):
        print(f"reset round: {i+1}")
        tree_update = modify_branch(tree_initial, update_A_Balance, update_B_Balance, alice_private_key, bob_private_key, safe_margin)
        leaf_node = tree_update[-1]
        #print(leaf_node)
        # after build the new active branch, the offchain payment works again in create_payment_transactions() with updated balances
        update_A_Balance, update_B_Balance, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA = duplex_payments(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key)
        #update_A_Balance, update_B_Balance, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA = duplex_payments_HighValue(leaf_node, AMOUNT_A_TO_B, AMOUNT_B_TO_A, alice_private_key, bob_private_key)
    tree = tree_update
    #branch = branch_update   
    print(f"Alice's final balance is: {web3.from_wei(update_A_Balance, 'ether')} ETH, Bob's final balance is {web3.from_wei(update_B_Balance, 'ether')}")
   
    alice_account = web3.eth.account.from_key(alice_private_key)
    alice_address = alice_account.address

    #bob_account = web3.eth.account.from_key(bob_private_key)
    #bob_address = bob_account.address

    #balance_A = web3.eth.get_balance(alice_address)
    #balance_B = web3.eth.get_balance(bob_address)
    #print(f"Alice's balance: {web3.from_wei(balance_A, 'ether')} ETH")
    #print(f"Bob's balance: {web3.from_wei(balance_B, 'ether')} ETH")

    # Attempt to close the channel
    closureChannel(update_A_Balance, update_B_Balance, alice_private_key, bob_private_key, contract, 
                   contract_address, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA)

if __name__ == "__main__":
    main()
