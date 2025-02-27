from web3 import Web3
import time
from eth_account.messages import encode_defunct
import json
import time
from save_data import save_Fee_to_excel, save_Latency_to_excel, save_Throughput_to_excel, save_fundingFee_to_excel

# Connect to the Ethereum node (e.g., Ganache)
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Assume we have the smart contract ABI and address
contract_address = "0xfd84059dE5a5917E5970aaCcF0e66b24085c18e1"
with open('artifacts/contracts/EltooChannel.sol/EltooChannel.json', 'r') as abi_file:
    contract_data = json.load(abi_file)
abi_data = contract_data['abi']

contract = web3.eth.contract(address=contract_address, abi=abi_data)

# Alice and Bob's private keys
alice_private_key = "0xcdd6f91ebcd7479f2abc0af6d930550419508357e2e441ddfcbac5e4a8e87a47"
bob_private_key = "0x71e26c79321a1e2886763767a390932733bc91186e44c8fea26ee2b9fb23c630"
alice = web3.eth.account.from_key(alice_private_key)
bob = web3.eth.account.from_key(bob_private_key)

alice_balance = Web3.to_wei(1, 'ether')  # Alice initial funds
bob_balance = Web3.to_wei(2, 'ether')    # Bob initial funds
amount = 60 # Alice everytime transfer 0.1 ETH
amount = Web3.to_wei(amount, 'gwei')
timelock_period = 10  # 10s

#alice_balance = Web3.to_wei(100000, 'ether')  # Alice initial funds
#bob_balance = Web3.to_wei(200000, 'ether')    # Bob initial funds
#amount = 300 # Alice everytime transfer 0.1 ETH
#amount = Web3.to_wei(300, 'ether')

# 
update_transactions = []
settlement_transactions = []

# generate Trigger Transaction data
trigger_transaction = {
    "balanceAlice": alice_balance,
    "balanceBob": bob_balance,
    "version": 1,
    "timelock": int(time.time()) + timelock_period
    #"timelock": timelock_period
}
initial_settle_time = trigger_transaction['timelock']   # the initial settlement tx can be broadcasted earliest 10s after trigger tx is broadcasted
# First, perform a hash operation on the transaction content to obtain the tx_hash.
def get_tx_hash(transaction):
    message = web3.solidity_keccak(['uint256', 'uint256',  'uint256', 'uint256', 'uint256'], [
            transaction['id'],   # for matching update tx and corresponding settlement tx
            transaction['balanceAlice'],
            transaction['balanceBob'], 
            transaction['version'],
            transaction['timelock']        
        ])
    message_hash = encode_defunct(message)
    return message_hash

def create_initial_SettleTX(id, alice_balance, bob_balance, version, timelock):  # this will also be used for later create Update tx and settlement tx
    settle_tx = {
        "id": id,
        "balanceAlice": alice_balance,
        "balanceBob": bob_balance,
        "version": version,
        #"timelock": int(time.time()) + timelock_period
        "timelock": timelock_period
    }
    
    return settle_tx

# I. Channel establishment
# 1. sign and exchange initial settlement tx
initial_settle_tx = create_initial_SettleTX(1, alice_balance, bob_balance, 1, timelock_period)
# First, perform a hash operation on the transaction content to obtain the tx_hash.
initial_settle_message_hash = get_tx_hash(initial_settle_tx)
# Then, Alice and Bob use their respective private keys to sign the hash value, confirming that both parties acknowledge this initial transaction.
signed_initial_A = web3.eth.account.sign_message(initial_settle_message_hash, private_key=alice_private_key) 
signed_initial_B = web3.eth.account.sign_message(initial_settle_message_hash, private_key=bob_private_key) 

# 2. sign and exchange trigger tx

trigger_message = web3.solidity_keccak(['uint256', 'uint256', 'uint256', 'uint256'], [
            trigger_transaction['balanceAlice'],
            trigger_transaction['balanceBob'], 
            trigger_transaction['version'],
            trigger_transaction['timelock']        
        ])
trigger_message_hash = encode_defunct(trigger_message)

signed_trigger_A = web3.eth.account.sign_message(trigger_message_hash, private_key=alice_private_key) 
signed_trigger_B = web3.eth.account.sign_message(trigger_message_hash, private_key=alice_private_key) 

def sign_funding_transaction(contract, alice_balance, bob_balance):
    tx_hash = contract.functions.signFundingTransaction(alice_balance, bob_balance).transact({
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

sign_funding_transaction(contract, alice_balance, bob_balance) #broadcast funding tx
# II. Send offchain payments
# everytime alice transfers  60 gwei to Bob
def offchain_payments(id, alice_balance, bob_balance, amount, timelock, version):  
    start_time = time.time()
    i = 0
    #id, version == 1   # initial id == 1, version == 1, since trigger tx is 0 
    while alice_balance > Web3.to_wei(0.99990, 'ether'):
        alice_balance -= amount
        bob_balance += amount
        #print(f"alice balance: {alice_balance}, bob balance: {bob_balance}")

        id += 1
        version += 1
        i += 1 
        # 1. create a new pair
        update_tx = create_initial_SettleTX(id, alice_balance, bob_balance, version, timelock_period)
        settle_tx = create_initial_SettleTX(id, alice_balance, bob_balance, version, timelock_period)

        update_transactions.append(update_tx)
        settlement_transactions.append(settle_tx)
        # 2. sign settle tx
        settle_message_hash = get_tx_hash(settle_tx)
        signed_settle_A = web3.eth.account.sign_message(settle_message_hash, private_key=alice_private_key) 
        signed_settle_B = web3.eth.account.sign_message(settle_message_hash, private_key=bob_private_key) 

        # 3. sign update tx
        update_message_hash = get_tx_hash(update_tx)
        signed_update_A = web3.eth.account.sign_message(update_message_hash, private_key=alice_private_key) 
        signed_update_B = web3.eth.account.sign_message(update_message_hash, private_key=bob_private_key) 
    
    end_time = time.time()  
    throughput = i / (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"Throughput: {throughput}")

    return id, alice_balance, bob_balance, amount, timelock, version, update_transactions, settlement_transactions

# everytime alice transfers 300 ETH to Bob
def offchain_payments_HighValue(id, alice_balance, bob_balance, amount, timelock, version):  
    start_time = time.time()
    i = 0
    #alice_balance = Web3.to_wei(100000, 'ether')
    #bob_balance = Web3.to_wei(200000, 'ether')
    #amount =  Web3.to_wei(300, 'ether')
    #id, version == 1   # initial id == 1, version == 1, since trigger tx is 0 
    while alice_balance > Web3.to_wei(90000, 'ether'):
        alice_balance -= amount
        bob_balance += amount
        #print(f"alice balance: {alice_balance}, bob balance: {bob_balance}")

        id += 1
        version += 1
        i += 1 
        # 1. create a new pair
        update_tx = create_initial_SettleTX(id, alice_balance, bob_balance, version, timelock_period)
        settle_tx = create_initial_SettleTX(id, alice_balance, bob_balance, version, timelock_period)

        update_transactions.append(update_tx)
        settlement_transactions.append(settle_tx)
        # 2. sign settle tx
        settle_message_hash = get_tx_hash(settle_tx)
        signed_settle_A = web3.eth.account.sign_message(settle_message_hash, private_key=alice_private_key) 
        signed_settle_B = web3.eth.account.sign_message(settle_message_hash, private_key=bob_private_key) 

        # 3. sign update tx
        update_message_hash = get_tx_hash(update_tx)
        signed_update_A = web3.eth.account.sign_message(update_message_hash, private_key=alice_private_key) 
        signed_update_B = web3.eth.account.sign_message(update_message_hash, private_key=bob_private_key) 
    
    end_time = time.time()  
    throughput = i / (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"Throughput: {throughput}")

    return id, alice_balance, bob_balance, amount, timelock, version, update_transactions, settlement_transactions
# III. Settle the Channel
# 1. Before broadcast a update transaction, the trigger tx should be broadcasted.
# 2. the broadcasted transaction must be verified: 1. the lock time is not expired. 2. if it has larger Version Number than the current 
#   2.1 solidity should have a data structure to store the current state, expecially the version number.

def broadcast_TriggerTX(trigger_transaction):   # Either party broadcast the trigger tx, here is Alice
    message = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256'], [
            contract_address, 
            trigger_transaction['balanceAlice'],
            trigger_transaction['balanceBob']
            ]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message.signature
    start_time = time.time()
    tx = contract.functions.broadcastTriggerTX( 
        trigger_transaction['balanceAlice'],
        trigger_transaction['balanceBob'], 
        trigger_transaction['version'],
        #trigger_transaction['timelock'],
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })
    # sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)

    # send transactions
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    triggerTX_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    end_time = time.time()  
    latency_Trigger = end_time - start_time
    #latency_Trigger = format(latency_Trigger, '.4f')
    return triggerTX_receipt, latency_Trigger 

"""    ['address', 'uint256', 'uint256', 'uint256', 'uint256'], [
            contract_address, 
            update_tx['balanceAlice'],
            update_tx['balanceBob'], 
            update_tx['version'],
            update_tx['timelock'] 
            ]"""
def broadcast_UpdateTX(update_tx):
    message = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [
            contract_address, 
            update_tx['balanceAlice'],
            update_tx['balanceBob']
            ]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message.signature
    start_time = time.time()
    tx = contract.functions.updateState( 
        update_tx['balanceAlice'],
        update_tx['balanceBob'], 
        update_tx['version'],
        update_tx['timelock'],        
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })
    # sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)

    # send transactions
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    updateTX_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    
    end_time = time.time()  
    latency_Update = end_time - start_time
    #latency_Update = format(latency_Update, '.4f')

    return updateTX_receipt, latency_Update



def broadcast_SettleTX(settle_tx):
    # Get the latest block timestamp before submission

    #time.sleep(10) # the settle tx always broadcasted 10s after his correpsonding Update tx broadcasted, so he wait for 10s 
  

    message = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [
            contract_address, 
            settle_tx['balanceAlice'],
            settle_tx['balanceBob']
            ]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message.signature

    #initial_block = web3.eth.get_block('latest')
    #submission_time = initial_block['timestamp']    
    #print(f"submit time: {submission_time}")
    start_time = time.time()  
    tx = contract.functions.settleChannel( 
        settle_tx['balanceAlice'],
        settle_tx['balanceBob'], 
        settle_tx['version'],
        settle_tx['timelock'],  
        #timelock_period,      
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })
    # sign transactions
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)

    # send transactions
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    settleTX_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
 

    # Record the confirmation time from the blockchain
    #confirmation_block = web3.eth.get_block(settleTX_receipt['blockNumber'])
    #confirmation_time = confirmation_block['timestamp']
    #latency = confirmation_time - submission_time
    end_time = time.time()  
    latency = end_time - start_time
    #latency = format(latency, '.4f')
    #save_Latency_to_excel(latency)

    print(f"Transaction Latency:  {latency} seconds")
    return settleTX_receipt, latency


def broadcast_cooperateTX(cooperate_tx):   # Either party broadcast the trigger tx, here is Alice
    message = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256'], [
            contract_address, 
            cooperate_tx['balanceAlice'],
            cooperate_tx['balanceBob']
            ]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message.signature
    start_time = time.time()  
    tx = contract.functions.CooperateTX( 
        cooperate_tx['balanceAlice'],
        cooperate_tx['balanceBob'], 
        #trigger_transaction['version'],
        #trigger_transaction['timelock'],
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })
    # sign transactions
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)

    # send transactions
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    triggerTX_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    end_time = time.time()  
    latency_Settle = end_time - start_time
    latency_Settle = format(latency_Settle, '.4f')
    print("save cooperate latency")
    save_Latency_to_excel(latency_Settle)

    return triggerTX_receipt



# if before channel lifetime expires, there is no update, then the initial settlement transaction will be broadcasted
#   the channel lifetime is initial_settle_time
anyUpdate = True
if anyUpdate == False:
    triggerTX_receipt = broadcast_TriggerTX(trigger_transaction)
    print("trigger success!")

    settle_tx = create_initial_SettleTX(1, alice_balance, bob_balance, 1, timelock_period)   # the initial settlement tx has the same version number as the Trigger tx
    settleTX_receipt = broadcast_SettleTX(settle_tx)
    gas_used = settleTX_receipt.gasUsed
    gas_price = web3.to_wei('42.36', 'gwei')

    transaction_fee = gas_used * gas_price

    print(f'Transaction fee: {web3.from_wei(transaction_fee, "ether")} ETH') 

else:
     
    id, alice_balance, bob_balance, amount, timelock, version, update_transactions, settlement_transactions = offchain_payments(1, alice_balance, bob_balance, amount, timelock_period, 1)
    #if cooperate: then both create a tx with their balance
    #id, alice_balance, bob_balance, amount, timelock, version, update_transactions, settlement_transactions = offchain_payments_HighValue(1, alice_balance, bob_balance, amount, timelock_period, 1)
    
    # else:
    cooperate = True  # dispute
    if cooperate: # = true --> no dispute
        update_tx = update_transactions[-1]
        cooperateTX_receipt = broadcast_cooperateTX(update_tx)
        print("Cooperate close channel success!")
        gas_used = cooperateTX_receipt.gasUsed
        gas_price = web3.to_wei('4236', 'gwei')

        transaction_fee = gas_used * gas_price
        transaction_fee = web3.from_wei(transaction_fee, "ether")
        save_Fee_to_excel(transaction_fee)

        print(f'cooperate Transaction fee: {transaction_fee} ETH') 


    else:   # --> dispute
        print(trigger_transaction)
        triggerTX_receipt, latency_Trigger = broadcast_TriggerTX(trigger_transaction)
        print("trigger success!")

        update_tx = update_transactions[-1]
        print(update_tx)
        updateTX_receipt, latency_Update = broadcast_UpdateTX(update_tx)
        print("update success!")
        time.sleep(10)

        settle_tx = settlement_transactions[-1]
        print(settle_tx)
        #timelock
        settleTX_receipt, latency_Settle = broadcast_SettleTX(settle_tx)
        print("settle success!")
        print("success")

        gas_used = triggerTX_receipt.gasUsed + updateTX_receipt.gasUsed + settleTX_receipt.gasUsed
        #gas_used = settleTX_receipt.gasUsed
        gas_price = web3.to_wei('42.36', 'gwei')

        transaction_fee = gas_used * gas_price
        transaction_fee = web3.from_wei(transaction_fee, "ether")
        save_Fee_to_excel(transaction_fee)

        latency = latency_Trigger + latency_Update + latency_Settle
        save_Latency_to_excel(latency)

        print(f"Incooperate Transaction Latency:  {latency} seconds")

        print(f'Incooperate Transaction fee: {transaction_fee} ETH') 

