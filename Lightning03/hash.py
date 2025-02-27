import hashlib
from eth_account import Account
from eth_account.messages import encode_defunct

# 示例：生成 Commitment Transaction 哈希
def generate_commitment_hash(alice_balance, bob_balance, contract_address, index, broadcaster):
    message = f"{contract_address}{alice_balance}{bob_balance}{index}{broadcaster}".encode()
    commitmentHash = hashlib.sha256(message).hexdigest()
    return commitmentHash

# Revocable Delivery Transaction, balance could be Alice or Bob's
def generate_RD_hash(balance, timelock, commitmentHash):
    message = f"{commitmentHash}{balance}{timelock}".encode()
    return hashlib.sha256(message).hexdigest()
"""
def generate_RDofBob_hash(bob_balance, timelock, commitmentHash):
    message = f"{commitmentHash}{bob_balance}{timelock}".encode()
    return hashlib.sha256(message).hexdigest()"""

# Breach Remedy Transaction for CiA, CiB
def generate_BR_hash(balance, commitmentHash):
    message = f"{commitmentHash}{balance}".encode()
    return hashlib.sha256(message).hexdigest()

# 示例：生成签名
def sign_message(private_key, message_hash):
    account = Account.from_key(private_key)
    message = encode_defunct(hexstr=message_hash)
    signed_message = Account.sign_message(message, private_key=private_key)
    return signed_message.signature.hex()

# 使用
contract_address = "0xYourContractAddress"
alice_balance = 1000
bob_balance = 500
index = 0
broadcaster = "alice", "bob"
timelock = 100

# 3 hash of 3 transactions for exchanging signatures
commitment_hash_A = generate_commitment_hash(alice_balance, bob_balance, contract_address, index, "alice")
commitment_hash_B = generate_commitment_hash(alice_balance, bob_balance, contract_address, index, "bob")

revocable_hash_A = generate_RD_hash(alice_balance, timelock, commitment_hash_A)
revocable_hash_B = generate_RD_hash(bob_balance, timelock, commitment_hash_B)

breach_hash_A = generate_BR_hash(alice_balance, commitment_hash_A) # supersede RD_A in CiA, Alice's balance go to be Bob's.
breach_hash_B = generate_BR_hash(bob_balance, commitment_hash_B)



# 假设 Alice 和 Bob 各自有私钥
alice_private_key = "0xAlicePrivateKey"
bob_private_key = "0xBobPrivateKey"

# 签名
alice_signature_C = sign_message(alice_private_key, commitment_hash_A)
bob_signature_C = sign_message(bob_private_key, commitment_hash_B)

alice_signature_RD = sign_message(alice_private_key, revocable_hash_A)
bob_signature_RD = sign_message(bob_private_key, revocable_hash_B)

alice_signature_BR = sign_message(alice_private_key, breach_hash_A)
bob_signature_BR = sign_message(bob_private_key, breach_hash_B)
