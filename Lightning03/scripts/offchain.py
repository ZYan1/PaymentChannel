from web3 import Web3
import time
from eth_account.messages import encode_defunct
import json
from save_data import save_Fee_to_excel, save_Latency_to_excel, save_Throughput_to_excel, save_fundingFee_to_excel
# Connect to the Ethereum node (e.g., Ganache)
web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# Assume we have the smart contract ABI and address
contract_address = "0x9945f42a4E1feC31af93A23953321EcEfbFa086C"
with open('artifacts/contracts/LightningChannel.sol/LightningChannel.json', 'r') as abi_file:
    contract_data = json.load(abi_file)
abi_data = contract_data['abi']

contract = web3.eth.contract(address=contract_address, abi=abi_data)

# private keys
alice_private_key = "0xf37b2d16a75e1dd61d42f2722d9fc745180f98391370ed5842ee1790fb19e442"
bob_private_key = "0x2d9a6e845ca44298e42dc26c5716f1e6c539c4045192ad44d84a592550cdf35c"
alice = web3.eth.account.from_key(alice_private_key)
bob = web3.eth.account.from_key(bob_private_key)

alice_balance = Web3.to_wei(1, 'ether')
bob_balance = Web3.to_wei(2, 'ether')    


commitment_transactions = []
def create_commitment_transaction(i, to_immediate, immediate_amount, rd_recipient, timelock_amount, timelock_expiry):
    commitment = {
        "id": i,
        "DTX": {
            "recipient": to_immediate,
            "amount": immediate_amount
        },
        "RDTX": {
            "recipient": rd_recipient,
            "amount": timelock_amount,
            "timelock": timelock_expiry
        },
        "BRTX": {  
            "recipient": to_immediate,
            "amount": timelock_amount
        }
    }
   
    commitment_transactions.append(commitment)
    return commitment

#timelock_duration = 86400  # timelock: 1 day
timelock_duration = 4  # 10s
C1a = create_commitment_transaction(
    i = 1,
    to_immediate=bob.address,            # DTX transfer to Bob
    immediate_amount=Web3.to_wei(2, 'ether'),
    rd_recipient=alice.address,           # RDTX transfer to Alice
    timelock_amount=Web3.to_wei(1, 'ether'),
    timelock_expiry=int(time.time()) + timelock_duration
)

C1b = create_commitment_transaction(
    i = 1,
    to_immediate=alice.address,          # DTX 给 Alice
    immediate_amount=Web3.to_wei(1, 'ether'),
    rd_recipient=bob.address,             # RDTX 给 Bob
    timelock_amount=Web3.to_wei(2, 'ether'),
    timelock_expiry=int(time.time()) + timelock_duration
)

def sign_RDTX(rdtx_data, private_key):
    message = web3.solidity_keccak(['address', 'uint256', 'uint256'], [
        rdtx_data['recipient'],
        rdtx_data['amount'], 
        rdtx_data['timelock']        
    ])
    message_hash = encode_defunct(message)
    
    signed_tx = web3.eth.account.sign_message(
        message_hash, private_key=private_key
    )
    return signed_tx

# sign RDTX of C1a and C1b 
rdtx_a = C1a['RDTX']
rdtx_b = C1b['RDTX']

signed_rdtx_a = sign_RDTX(rdtx_a, alice_private_key)    # RDTX in C1a, only need alice's signature
signed_rdtx_b = sign_RDTX(rdtx_b, bob_private_key)        # RDTX in C1b, only need Bob's signature   
print("Alice's RDTX Signature:", signed_rdtx_a.signature.hex())
print("Bob's RDTX Signature:", signed_rdtx_b.signature.hex())
# sign Commitment transactions
def sign_commitment_transaction(commitment_data, private_key):
    message = web3.solidity_keccak(['uint256', 'address', 'uint256', 'address', 'uint256', 'uint256'], [
            commitment_data['id'],
            commitment_data['DTX']['recipient'],
            commitment_data['DTX']['amount'],
            commitment_data['RDTX']['recipient'],
            commitment_data['RDTX']['amount'],
            commitment_data['RDTX']['timelock']
        ])
    message_hash = encode_defunct(message)
    signed_tx = web3.eth.account.sign_message(message_hash, private_key=private_key) 
    return signed_tx

# sign commitment transactions
signed_C1a_byAlice = sign_commitment_transaction(C1a, alice_private_key)
signed_C1a_byBob = sign_commitment_transaction(C1a, bob_private_key)
signed_C1b_byBob = sign_commitment_transaction(C1b, bob_private_key)
signed_C1b_byAlice = sign_commitment_transaction(C1b, alice_private_key)

#print("Alice's C1a Signature:", signed_C1a.signature.hex())
#print("Bob's C1b Signature:", signed_C1b.signature.hex())




def sign_BRTX(brtx_data, private_key):

    message = web3.solidity_keccak(['uint256', 'address', 'uint256'], [
            brtx_data["id"],
            brtx_data["BRTX"]['recipient'],
            brtx_data["BRTX"]['amount'], 
        ])
    message_hash = encode_defunct(message)
    signed_tx = web3.eth.account.sign_message(message_hash, private_key=private_key) 
    return signed_tx


    
""" return web3.eth.account.sign_message(
        web3.solidity_keccak(['uint256', 'address'], [
            brtx_data["id"],
            brtx_data["RBTX"]['recipient'],
            brtx_data["RBTX"]['amount'], 
        ]), private_key=private_key
    )"""


def broadcastFunding():
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
    print("broadcast Funding transaction to the blockchain")
    print(f'Funding Transaction fee: {funding_transaction_fee} ETH')
    return funding_transaction_fee, receipt_FundingTX
   
funding_transaction_fee, receipt_FundingTX = broadcastFunding()
print("Funding Transaction is signed and broadcasted to the blockchain!")

#amount = 0.1 # Alice everytime transfer 0.1 ETH
#amount = Web3.to_wei(60, 'gwei')
def offchain_payments(i, alice_balance, bob_balance, amount, targetValue):
    #i = 0
    start_time = time.time()
    #while alice_balance > Web3.to_wei(0.99995, 'ether'):
    while alice_balance > targetValue:
        i += 1
        alice_balance -= amount
        bob_balance += amount
        #print(f"alice balance: {alice_balance}, bob balance: {bob_balance}")
        
        # generate new pair of commitment transactions
        #i += 1  
        new_commitment_A = create_commitment_transaction(i, bob.address, bob_balance, alice.address, alice_balance, timelock_duration) #[-2]
        new_commitment_B = create_commitment_transaction(i, alice.address, alice_balance, bob.address, bob_balance, timelock_duration) #[-1]

        # invalidate old pair by signing BRTX
        prior_commitment_A = commitment_transactions[-4] # old pair
        prior_commitment_B = commitment_transactions[-3] 
        #print (f"prior Commitment transactions pair: {prior_commitment_A['id']}, {prior_commitment_B['id']},\n new Commiment transactions pair with id: {new_commitment_A['id']}")

        signed_BR_A = sign_BRTX(prior_commitment_A, alice_private_key)   #supersede RDTX in CiA, give Alice's money to Bob
        signed_BR_B = sign_BRTX(prior_commitment_B, bob_private_key)     #supersede RDTX in CiB, give Bob's money to Alice

        rdtx_a = new_commitment_A['RDTX']
        rdtx_b = new_commitment_B['RDTX']
        signed_rdtx_a = sign_RDTX(rdtx_a, alice_private_key)
        signed_rdtx_b = sign_RDTX(rdtx_b, bob_private_key)

        # Both parties sign and exchange signatures for new CTX pair
        signed_C1A_byAlice = sign_commitment_transaction(new_commitment_A, alice_private_key)
        signed_C1A_byBob = sign_commitment_transaction(new_commitment_A, bob_private_key)
        
        signed_C1A_byBob = sign_commitment_transaction(new_commitment_B, bob_private_key)
        signed_C1A_byAlice = sign_commitment_transaction(new_commitment_B, alice_private_key)
        


    end_time = time.time()  
    throughput = (i -1)/ (end_time - start_time)
    save_Throughput_to_excel(throughput)
    
    print (f"Throughput: {throughput}")

    return commitment_transactions, new_commitment_A, prior_commitment_A, new_commitment_B

commitment_transactions, new_commitment_A, prior_commitment_A, new_commitment_B = offchain_payments(1, alice_balance, bob_balance, Web3.to_wei(60, 'gwei'), Web3.to_wei(0.999990, 'ether'))
#commitment_transactions, new_commitment_A, prior_commitment_A, new_commitment_B = offchain_payments(1, alice_balance, bob_balance, Web3.to_wei(300, 'ether'), Web3.to_wei(50000, 'ether'))

def lastID(commitment_transactions):
    lastCommitmentID = commitment_transactions[-1]['id'], commitment_transactions[-2]['id']
    contract.function.getLastCommitmentID(lastCommitmentID)

# Alice broadcast her Commitment   --> dispute
def broadcast(new_commitment_A):
    # Prepare the message to sign
    #alice_balance = new_commitment_A['RDTX']['amount']
    #bob_balance = new_commitment_A['DTX']['amount']
    #print(alice_balance, bob_balance)
    message = Web3.solidity_keccak(
        ['address', 'uint256', 'uint256'],
        [contract_address, new_commitment_A['RDTX']['amount'], new_commitment_A['DTX']['amount']]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message_alice = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message_alice.signature
    signed_message_bob = web3.eth.account.sign_message(message_hash, private_key=bob_private_key)
    bob_signature = signed_message_bob.signature

    message = Web3.solidity_keccak(
        ['address', 'uint256'],
        [contract_address, new_commitment_A['RDTX']['amount']]
    )
    message_hash = encode_defunct(message)
    alice_signed_RDTX = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_RDTX = alice_signed_RDTX.signature

    message = Web3.solidity_keccak(
        ['address', 'uint256'],
        [contract_address, new_commitment_A['DTX']['amount']]
    )
    message_hash = encode_defunct(message)
    bob_signed_RDTX = web3.eth.account.sign_message(message_hash, private_key=bob_private_key)
    bob_RDTX = bob_signed_RDTX.signature

    #print("Message:", message.hex())
    #print("Signed Message Hash (Python):", signed_message.message_hash.hex())
    start_time01 = time.time() 
    tx = contract.functions.broadcastCTX( 
        new_commitment_A['id'],               # This ia Alice's Commitment tx
        new_commitment_A['DTX']['recipient'],   # DTX'S recipient is Bob
        new_commitment_A['DTX']['amount'],      # Bob's balance
        new_commitment_A['RDTX']['recipient'],  # recipient is Alice
        new_commitment_A['RDTX']['amount'],     # Alice's balance
        new_commitment_A['RDTX']['timelock'],
        new_commitment_A['BRTX']['recipient'],
        new_commitment_A['BRTX']['amount'],
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })

    # sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)

    # send transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    end_time01 = time.time()  
    latency01 = end_time01-start_time01

    start_time02 = time.time() 
    #print(f"timelock:{new_commitment_A['RDTX']['timelock']}")
    time.sleep(new_commitment_A['RDTX']['timelock'])
    #start_time02 = time.time() 
    
    tx_RD = contract.functions.broadcastRDTX( 
        #new_commitment_A['id'],               # This ia Alice's Commitment tx
        #new_commitment_A['DTX']['recipient'],   # DTX'S recipient is Bob
        #new_commitment_A['DTX']['amount'],      # Bob's balance
        new_commitment_A['RDTX']['recipient'],  # recipient is Alice
        new_commitment_A['RDTX']['amount'],     # Alice's balance
        #new_commitment_A['RDTX']['timelock'],
        #new_commitment_A['BRTX']['recipient'],
        #new_commitment_A['BRTX']['amount'],
        alice_RDTX
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('42.36', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })

     # sign transaction 
    signed_tx = web3.eth.account.sign_transaction(tx_RD, alice_private_key)

    # send transaction
    tx_hash_RD = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt_RD = web3.eth.wait_for_transaction_receipt(tx_hash_RD)


    end_time02 = time.time()  
    latency02 = end_time02 - start_time02
    latency = latency01 + latency02
    latency = format(latency, '.4f')
    save_Latency_to_excel(latency)

    print(f"Incooperate Transaction Latency:  {latency} seconds")
    print("success")

    gas_used_CTX = tx_receipt.gasUsed 
    #gas_used_DTX = tx_receipt_D.gasUsed
    gas_used_RDTX = tx_receipt_RD.gasUsed
    gas_total = gas_used_CTX + gas_used_RDTX
    gas_price = tx['gasPrice']


    #fee_ctx = gas_used_CTX * gas_price
    #fee_dtx = gas_used_DTX * gas_price
    #fee_rdtx = gas_used_RDTX * gas_price  
    total_transaction_fee = gas_total * gas_price

    #fee_ctx = web3.from_wei(fee_ctx, "ether")
    #fee_dtx = web3.from_wei(fee_dtx, "ether")
    #fee_rdtx = web3.from_wei(fee_rdtx, "ether") 
    total_transaction_fee = web3.from_wei(total_transaction_fee, "ether")

    save_Fee_to_excel(total_transaction_fee)

    print(f'Incooperate Transaction fee: {total_transaction_fee} ETH') 

    return tx_receipt


def settle_cooperate():
    message = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256'], [
            contract_address, 
            new_commitment_A['RDTX']['amount'],  # alice's final balance
            new_commitment_A['DTX']['amount']     # bob's final balance
            ]
    )
    message_hash = encode_defunct(message)

    # Sign the message
    signed_message = web3.eth.account.sign_message(message_hash, private_key=alice_private_key)
    alice_signature = signed_message.signature
    start_time = time.time() 
    tx = contract.functions.CooperateTX( 
        new_commitment_A['RDTX']['amount'],  # alice's final balance
        new_commitment_A['DTX']['amount'] ,
        #trigger_transaction['version'],
        #trigger_transaction['timelock'],
        alice_signature
    ).build_transaction({
        'from': alice.address,  # Specifies the address that initiates (or sends) the transaction. Ensure the transaction is recognized as being from Alice 
        'gas': 2000000,
        'gasPrice': web3.to_wei('4236', 'gwei'),
        'nonce': web3.eth.get_transaction_count(alice.address)
    })
    # sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, alice_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f'receipt: {receipt}')

    end_time = time.time()  
    latency = end_time - start_time
    latency = format(latency, '.4f')
    save_Latency_to_excel(latency)

    print(f"Cooperate Transaction Latency:  {latency} seconds")

    gas_used = receipt.gasUsed
    gas_price = tx['gasPrice']

    transaction_fee = gas_used * gas_price
    transaction_fee = web3.from_wei(transaction_fee, "ether")
    save_Fee_to_excel(transaction_fee)

    print(f'cooperate Transaction fee: {transaction_fee} ETH') 
    return receipt

cooperate = True
if cooperate: # = true
    # no dispute
    settle_cooperate()
else:
    # dispute
    broadcast(new_commitment_A)








