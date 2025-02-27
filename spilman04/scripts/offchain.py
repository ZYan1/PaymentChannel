import web3
from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account
import json
import time
from save_data import save_Fee_to_excel, save_Latency_to_excel, save_Throughput_to_excel, save_fundingFee_to_excel
# Set up the node provided by Ganache.
ganache_url = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

# Alice and Bob's private key, from Ganache running
alice_private_key = "0xb3b6a304ccc41e0d145b7ac1480f11ec92fffe6edc073e220ff074eaf1977f50"  
alice_account = Account.from_key(alice_private_key)
alice_address = alice_account.address
bob_private_key = "0x148ad9eb56b07bf63b886d0aa1252174d60e76fb568d6a7d118aa1bde4f5429d"  
bob_address = Account.from_key(bob_private_key).address
# contract address : get from deploy.js execution 
contract_address = "0x42d0Df86388115C960B4CABdBD9f3A8603201b0b"  
with open('artifacts/contracts/SpilmanChannel.sol/SpilmanChannel.json', 'r') as abi_file:
    contract_data = json.load(abi_file)
abi_data = contract_data['abi']

payment_channel = w3.eth.contract(address=contract_address, abi=abi_data)

total_funded = w3.to_wei(1, 'ether')  # 1 Ether funded by Alice      --------> comment when High Value
#total_funded = w3.to_wei(100000, 'ether')   # HIGH Value
#payment_amount = w3.to_wei(0.003, 'ether')  # Each off-chain payment of 0.001 Ether
#transferred_amount = 0  # Amount already transferred

# Create an offline signed payment.
def sign_payment_state(alice_balance, bob_balance):
    message = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [contract_address, alice_balance, bob_balance])
    message_hash = encode_defunct(message)
    # Sign the message with sender's private key (Ganache's account key used)
    signed_message_A = w3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    signed_message_B  = w3.eth.account.sign_message(message_hash, private_key=bob_private_key)

    bob_signature = bytes(signed_message_B.signature)
    return bob_signature





# Alice makes payments off-chain
def make_off_chain_payments(total_funded):
    #global transferred_amount
    #total_funded = w3.to_wei(1, 'ether') 
    target_amount = w3.to_wei(0.99995, 'ether')
    payment_amount = w3.to_wei(60, 'gwei')  # Each off-chain payment of 0.001 Ether
    transferred_amount = 0
    i = 0
    start_time = time.time()
    while total_funded >= target_amount:
        # Increment the transferred amount by the payment amount
        transferred_amount += payment_amount
        total_funded -= payment_amount
        # Sign the current state and output it
        signature = sign_payment_state(total_funded, transferred_amount)
        i += 1 
        #print(f"Off-chain payment: {w3.from_wei(transferred_amount, 'ether')} ETH transferred.")
        #print(f"Signature: {signature.hex()}")

    end_time = time.time()  
    throughput = i / (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"High value Throughput: {throughput}")

    
    # Alice's balance
    alice_balance = total_funded
    bob_balance = transferred_amount
    #bob_signature = bytes(signed_message_B.signature)

    print(f"Alice's final balance: {w3.from_wei(alice_balance, "ether")} ETH, Bob's final balance: {w3.from_wei(bob_balance, "ether")} ETH")
    return alice_balance, bob_balance

def make_off_chain_payments_HighValue(total_funded):
    #global transferred_amount
    #total_funded = w3.to_wei(100000, 'ether') 
    
    payment_amount = w3.to_wei(300, 'ether')  # Each off-chain payment of 1 million dollars
    target_amount = w3.to_wei(92500, 'ether')
    #payment_amount = w3.to_wei(2, 'ether')  # Each off-chain payment of 1 million dollars
    #target_amount = 0
    transferred_amount = 0
    i = 0
    start_time = time.time()
    while total_funded >= target_amount:
        # Increment the transferred amount by the payment amount
        transferred_amount += payment_amount
        total_funded -= payment_amount
        # Sign the current state and output it
        signature = sign_payment_state(total_funded, transferred_amount)
        i += 1 
        #print(f"Off-chain payment: {w3.from_wei(transferred_amount, 'ether')} ETH transferred.")
        #print(f"Signature: {signature.hex()}")

    end_time = time.time()  
    throughput = i / (end_time - start_time)   # 
    save_Throughput_to_excel(throughput)
    
    print (f"High value Throughput: {throughput}")

    
    # Alice's balance
    alice_balance = total_funded
    bob_balance = transferred_amount
    #bob_signature = bytes(signed_message_B.signature)

    print(f"Alice's final balance: {w3.from_wei(alice_balance, "ether")} ETH, Bob's final balance: {w3.from_wei(bob_balance, "ether")} ETH")
    return alice_balance, bob_balance


def closureChannel(alice_balance, bob_balance, bob_signature):

    start_time = time.time()  
    # Bob submits the last state of payments
    tx = payment_channel.functions.closeChannel(
        alice_balance, 
        bob_balance, 
        bob_signature  # This is Bob's signature of the state
    ).build_transaction({
        'from': bob_address,
        'nonce': w3.eth.get_transaction_count(bob_address),
        'gas': 2000000,
        'gasPrice': w3.to_wei('4236', 'gwei'), # use the average gas price of the last 3 month in 2024 or... !!!!!!!   <-------1. convert to dollars or .... more compariabel
    })

    signed_tx = w3.eth.account.sign_transaction(tx, bob_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"receipt:{receipt}")
    #print(f"signature: {signature}")

    end_time = time.time()  
    latency = end_time - start_time
    save_Latency_to_excel(latency)

    print(f"Latency: {latency:.4f} seconds")

    gas_used = receipt.gasUsed
    gas_price = tx['gasPrice']

    transaction_fee = gas_used * gas_price
    transaction_fee = w3.from_wei(transaction_fee, "ether")
    save_Fee_to_excel(transaction_fee)

    print(f'Transaction fee: {transaction_fee} ETH')

    return receipt
    #return transferred_amount, signature

# 1. broadcast funding transaction
def fundingTX ():

    tx = payment_channel.functions.fundChannel().transact({'from': alice_address, 'value': total_funded})
    receipt_FundingTX = w3.eth.wait_for_transaction_receipt(tx)

    
    # Check if the funding is complete
    is_funding_complete = payment_channel.functions.isFundingComplete().call()
    print("Is funding complete?", is_funding_complete)

    gas_used = receipt_FundingTX.gasUsed
    gas_price = w3.to_wei('42.36', 'gwei')

    funding_transaction_fee = gas_used * gas_price
    funding_transaction_fee = w3.from_wei(funding_transaction_fee, "ether")
    save_fundingFee_to_excel(funding_transaction_fee)

    print(f'Funding Transaction fee: {funding_transaction_fee} ETH')
    return funding_transaction_fee, receipt_FundingTX

fundingTX()
# 2. sending offchain payments
alice_balance, bob_balance = make_off_chain_payments(total_funded)   # low value
#alice_balance, bob_balance = make_off_chain_payments_HighValue(total_funded)   # high value

bob_signature = sign_payment_state(alice_balance, bob_balance)
closureChannel(alice_balance, bob_balance, bob_signature)





