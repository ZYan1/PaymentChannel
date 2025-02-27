import json
from web3 import Web3
from eth_account.messages import encode_defunct
import time
from save_data import save_Fee_to_excel, save_Latency_to_excel, save_Throughput_to_excel
# Load invalidation tree from JSON (single branch case)
def load_invalidation_tree(invalidation_tree_with_signatures):
    with open(invalidation_tree_with_signatures, 'r') as file:
        return json.load(file)

# Function to check if Bob has signed
def has_bob_signed(transaction):
    return transaction['bobSignature'] is not None

# Function to broadcast the valid branch unilaterally (for single branch)
def broadcast_valid_branch(contract, alice_private_key, branch, alice_signature, contract_address):
    data=branch[2]
    #hashes = []
    # Extract state and signatures from the branch
    latency_total = 0
    gas_used = 0
    alice_balance = data["tx_data"]["alice_balance"]
    bob_balance = data["tx_data"]["bob_balance"]
    message = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [contract_address, alice_balance, bob_balance])
    #print(f"Generated message hash (Python): {message.hex()}")

    message_encoded = encode_defunct(message)
    alice_signature = web3.eth.account.sign_message(message_encoded, private_key=alice_private_key)
    alice_signature = bytes(alice_signature.signature)


    alice_address = web3.eth.account.from_key(alice_private_key).address
    for entry in branch:
        depth = entry["depth"]
        #timelock = entry["timelock"]
        alice_balance = entry["tx_data"]["alice_balance"]
        bob_balance = entry["tx_data"]["bob_balance"]

        
        
        start_time = time.time()  
        # Call closeChannel with the valid branch data
        tx = contract.functions.broadcastBranch(
            depth,
            alice_balance,
            bob_balance,
            alice_signature
            
        ).build_transaction({
            'from': alice_address,
            'nonce': web3.eth.get_transaction_count(alice_address),
            'gas': 2000000,
            'gasPrice': web3.to_wei('42.36', 'gwei'),
        })
    
        # Sign the transaction with Alice's private key
        signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)
        try:
            # Broadcast the transaction to the blockchain
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            # Wait for the transaction to be mined
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            end_time = time.time()  
            latency = end_time - start_time
            latency_total = latency_total + latency
            gas_used = gas_used + receipt.gasUsed
            print(f"add gas {receipt.gasUsed}, have get total gas_used: {gas_used} and add latency: {latency}, total latency: {latency_total}")
        
        except Exception as e:
            print(f'An error occurred: {e}') 
            # Return default values if there is an exception
            #return None, gas_used, latency

    latency_branch = latency_total
    print (f"branch latency: {latency_branch}")
    #save_Latency_to_excel(latency_branch)

    gas_used_branch = gas_used
    #gas_price = web3.to_wei('42.36', 'gwei')
    #transaction_fee = gas_used_branch * gas_price
    #transaction_fee = web3.from_wei(transaction_fee, "ether")
    #save_Fee_to_excel(transaction_fee)
        
    #print(f'Branch Transaction fee: {transaction_fee} ETH') 
    
    return latency_branch, gas_used_branch

       
        # Hash the structured data
        #hash_value = web3.solidity_keccak(
         #   ["uint256", "uint256", "uint256", "uint256"],
          #  [depth, timelock, alice_balance, bob_balance]
        #)
        #hashes.append(hash_value.hex())
    # Convert hash strings to integers for Solidity compatibility
    #hashes_int = [int(hash_value, 16) for hash_value in hashes]
    
    #alice_balance = data['tx_data']['alice_balance']
#bob_balance = data['tx_data']['bob_balance']
    #alice_signature = data["signatures"]['alice']
    #bob_signature = data["signatures"]['bob']

def broadcast_payment_TX (contract, contract_address, alice_private_key, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA, alice_address):
    """messageAB = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [contract_address, Cab_alice_balance, Cab_bob_balance])
    #print(f"Generated message hash (Python): {message.hex()}")

    message_encoded_AB = encode_defunct(messageAB)
    alice_signatureAB = web3.eth.account.sign_message(message_encoded_AB, private_key=alice_private_key)
    alice_signatureAB = bytes(alice_signatureAB.signature)

    bob_signatureAB = web3.eth.account.sign_message(message_encoded_AB, private_key=bob_private_key)
    bob_signatureAB = bytes(bob_signatureAB.signature)


    messageBA = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [contract_address, Cba_alice_balance, Cba_bob_balance])
    #print(f"Generated message hash (Python): {message.hex()}")

    message_encoded_BA = encode_defunct(messageBA)
    alice_signatureBA = web3.eth.account.sign_message(message_encoded_BA, private_key=alice_private_key)
    alice_signatureBA = bytes(alice_signatureBA.signature)

    bob_signatureBA = web3.eth.account.sign_message(message_encoded_BA, private_key=bob_private_key)
    bob_signatureBA = bytes(bob_signatureBA.signature)"""



    #alice_address = web3.eth.account.from_key(alice_private_key).address
    start_time = time.time()  
    txAB = contract.functions.broadcastPaymentTxAB(
        Cab_alice_balance,
        Cab_bob_balance,
        #alice_r, alice_s, alice_v,
        #bob_r, bob_s, bob_v
        aliceAB,
        bobAB
    ).build_transaction({
        'from': alice_address,
        'nonce': web3.eth.get_transaction_count(alice_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
    })
    #alice_private_key = '0x33b5f0afb3f151d22c301a86423232f83531fd69cf2c468e87e7e2fadbe071f5'
    signed_tx = web3.eth.account.sign_transaction(txAB, alice_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the transaction to be mined
    receiptAB = web3.eth.wait_for_transaction_receipt(tx_hash)

    end_time = time.time()  
    latencyAB = end_time - start_time
    


    start_time = time.time() 
    txBA = contract.functions.broadcastPaymentTxBA(
        Cba_alice_balance,
        Cba_bob_balance,
        #alice_r, alice_s, alice_v,
        #bob_r, bob_s, bob_v
        aliceBA,
        bobBA
    ).build_transaction({
        'from': alice_address,
        'nonce': web3.eth.get_transaction_count(alice_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
    })
    signed_tx = web3.eth.account.sign_transaction(txBA, alice_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    # Wait for the transaction to be mined
    receiptBA = web3.eth.wait_for_transaction_receipt(tx_hash)

    end_time = time.time()  
    latencyBA = end_time - start_time
    

    latency_total = latencyAB + latencyBA
    gas_used = receiptBA.gasUsed + receiptAB.gasUsed

    print(f"latnecy for 2 payment tx: {latency_total}, gas used for 2 payment tx: {gas_used}")
    return latency_total, gas_used



# Function to cooperatively close the channel
def close_channel_cooperatively(contract, alice_private_key, update_Cab_alice_balance, update_Cba_bob_balance, alice_signature, bob_signature):
#def close_channel_cooperatively(contract, alice_private_key, update_Cab_alice_balance, update_Cba_bob_balance, alice_r, alice_s, alice_v, bob_r, bob_s, bob_v):
    alice_account = web3.eth.account.from_key(alice_private_key)
    alice_address = alice_account.address
    """
    bob_account = web3.eth.account.from_key(bob_private_key)
    bob_address = bob_account.address

    balance_A = web3.eth.get_balance(alice_address)
    balance_B = web3.eth.get_balance(bob_address)
    print(f"Alice's balance: {web3.from_wei(balance_A, 'ether')} ETH")
    print(f"Bob's balance: {web3.from_wei(balance_B, 'ether')} ETH")"""
   
    #alice_balance = web3.to_wei(2.65,'ether')
    #bob_balance = web3.to_wei(0.35, 'ether') 
    # Convert the updated balances to wei
    total_funded_balance = web3.to_wei(3, 'ether')  # Example total funded amount (adjust based on your actual amount)
    alice_balance = update_Cab_alice_balance
    bob_balance = update_Cba_bob_balance
    #total_funded_balance = web3.to_wei(300000, 'ether')

    # Verify that the total sum of balances matches the original funding amount
    if alice_balance + bob_balance != total_funded_balance:
        print(f"Error: The sum of Alice and Bob's balances ({alice_balance + bob_balance}) does not match the total funded amount ({total_funded_balance}).")
        return

    print(f"Closing the channel with Alice's balance: {alice_balance} wei and Bob's balance: {bob_balance} wei")

    #channel_open = contract.functions.isChannelClosed().call()
    #print(f"Is the channel open? {channel_open}")
    #if not channel_open:
       #print("Cannot close the channel because it is already closed.")
    
    start_time = time.time()  
    tx = contract.functions.closeChannel(
        alice_balance,
        bob_balance,
        #alice_r, alice_s, alice_v,
        #bob_r, bob_s, bob_v
        alice_signature,
        bob_signature
    ).build_transaction({
        'from': alice_address,
        'nonce': web3.eth.get_transaction_count(alice_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
    })

    # Sign the transaction with Alice's private key
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)
    try:
        # Broadcast the transaction to the blockchain
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f'Transaction sent with hash: {tx_hash.hex()}')
        # Wait for the transaction to be mined
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        #print(f'Transaction receipt: {receipt}')
        end_time = time.time()  
        gas_used = receipt.gasUsed
        gas_price = tx['gasPrice']
        #gas_price = web3.to_wei('42.36', 'gwei')
        transaction_fee = gas_used * gas_price
        transaction_fee = web3.from_wei(transaction_fee, "ether")
        save_Fee_to_excel(transaction_fee)
        
        print(f'Transaction fee: {transaction_fee} ETH') 

        
        latency = end_time - start_time
        latency = format(latency, '.4f')
        print (f"latency: {latency}")
        save_Latency_to_excel(latency)

        return receipt
    
    except Exception as e:
        print(f'An error occurred: {e}')  

  

    
# Initialize web3 connection
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Alice's private key and smart contract details
# alice_private_key = "YOUR_ALICE_PRIVATE_KEY"
#contract_address = w3.toChecksumAddress("0xYourSmartContractAddress")
#contract_abi = json.loads('[ABI_GOES_HERE]')
#payment_channel_contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Load the invalidation tree from a JSON file (single branch)
#invalidation_tree = load_invalidation_tree('invalidation_tree_with_signatures.json')
#single_branch = invalidation_tree['branch']

# Create the teardown transaction (Alice's balance, Bob's balance)
#alice_balance = 0.4  # Example balance
#bob_balance = 0.6  # Example balance
#alice_signature = "0xAliceSignature"
#bob_signature = "0xBobSignature"

# main function
def closureChannel(update_Cab_alice_balance, update_Cba_bob_balance, alice_private_key, bob_private_key, contract, 
                   contract_address, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA):
    alice_address = web3.eth.account.from_key(alice_private_key).address
    # Step 1: Alice creates and signs the message
    message = Web3.solidity_keccak(['address', 'uint256', 'uint256'], [contract_address, update_Cab_alice_balance, update_Cba_bob_balance])
    #print(f"Generated message hash (Python): {message.hex()}")

    message_encoded = encode_defunct(message)
    alice_signature = web3.eth.account.sign_message(message_encoded, private_key=alice_private_key)
    #print(f"alice signature: {alice_signature}")

    # Step 2: Send Alice's signature to Bob (in a real case, you would transmit it securely to Bob)
    # In this case, it's all in the same script
    # Bob signs the message
    bob_signature = None                                                                                 #
    bob_signature = web3.eth.account.sign_message(message_encoded, private_key=bob_private_key)          # -----> comment this to be dispute
    #print(f"bob signature: {bob_signature}")
    
    # Convert signatures from HexBytes to bytes, because Solidity expects bytes
    alice_signature = bytes(alice_signature.signature)
    
    bob_signature = bytes(bob_signature.signature)                        # -----> comment this to be dispute
    #has_bob_signed({'bobSignature': None})                                # ----->  comment  this to no_dispute
    #print(f"alice signature in bytes: {alice_signature}")

    #alice_r, alice_s, alice_v = alice_signature.r, alice_signature.s, alice_signature.v
    #bob_r, bob_s, bob_v = bob_signature.r, bob_signature.s, bob_signature.v

    #print("Check balances wether enough for sending TX ... ...")
    #balance_A = web3.eth.get_balance(alice)
    #balance_B = web3.eth.get_balance(bob)
    #print(f"Alice's balance: {web3.from_wei(balance_A, 'ether')} ETH")
    #print(f"Bob's balance: {web3.from_wei(balance_B, 'ether')} ETH")
    single_branch = load_invalidation_tree('invalidation_tree_with_signatures.json')
    #single_branch = invalidation_tree['branch']
    #print(update_Cab_alice_balance, update_Cba_bob_balance)
    # Step 3: Check if Bob has signed the transaction
    if has_bob_signed({'bobSignature': bob_signature}): # --> no dispute
        # If Bob signed, close the channel cooperatively
        print("Bob has signed, closing the channel cooperatively...")
        receipt = close_channel_cooperatively(contract, alice_private_key, update_Cab_alice_balance, 
                                              update_Cba_bob_balance, alice_signature, bob_signature)
        print(f"Channel closed cooperatively with transaction: {receipt.transactionHash.hex()}")
        #print(f"Channel closed cooperatively")
    else:
        # Step 4: If Bob hasn't signed, broadcast the single valid branch from the invalidation tree    -->dispute
        print("Bob did not sign, broadcasting the valid branch from the invalidation tree...")
        latency, gas_used = broadcast_valid_branch(contract, alice_private_key, single_branch, alice_signature, contract_address)
        latencyPayment, gas_used_Payment = broadcast_payment_TX (contract, contract_address, alice_private_key, Cab_alice_balance, Cab_bob_balance, Cba_alice_balance, Cba_bob_balance, aliceAB, aliceBA, bobAB, bobBA,alice_address)

        print(f"Transaction broadcasted unilaterally!")

        gas_price = web3.to_wei('42.36', 'gwei') 
        branch_transaction_fee = gas_used * gas_price
        branch_transaction_fee = web3.from_wei(branch_transaction_fee, "ether")
        total_transaction_fee = (gas_used + gas_used_Payment) * gas_price
        total_transaction_fee = web3.from_wei(total_transaction_fee, "ether")
        save_Fee_to_excel(total_transaction_fee)
        latency_total = latency + latencyPayment
        save_Latency_to_excel(latency_total)

        print(f'Branch Transaction fee: {branch_transaction_fee} ETH, Branch Latency: {latency}.')
        print(f'Total Transaction fee: {total_transaction_fee} ETH, total Latency: {latency_total}.')


