"""
from web3 import Web3
import json

# Connect to Ethereum (Ganache)
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Function to build the invalidation tree
def build_invalidation_tree(alice_fund, bob_fund, depth=3, max_timelock=100):
    tree_initial = []
    
    for i in range(1, depth + 1):  # Depth of 3
        timelock = max_timelock
# Create the branch node with Alice and Bob's balances
        branch_node = [
            i,  # Depth
            timelock,  # Timelock for the branch
            f"txid_{i}",  # Simulate a transaction ID
            {
                "alice_balance": alice_fund,
                "bob_balance": bob_fund
            }
        ]
        tree_initial.append(branch_node)
        """
"""      # Simulate branch transaction (off-chain)
        branch_tx = {
            'alice_balance': alice_fund,
            'bob_balance': bob_fund,
            'depth': i,
            'timelock': timelock
        }
        # Append the branch node (with balances) to the tree
        tree_initial.append({
            "depth": i,
            "timelock": timelock,
            "txid": f"txid_{i}",  # Simulate a transaction ID
            "output_alice": alice_fund, 
            "output_bob": bob_fund
        })"""

"""# Return the last (leaf) node
    leaf_node = tree_initial[-1]
    leaf_txid = leaf_node["txid"]
    
    return tree_initial, leaf_txid

# Initialize funds
alice_fund = web3.toWei(1, 'ether')  # Alice's initial fund
bob_fund = web3.toWei(1, 'ether')    # Bob's initial fund

# Build the invalidation tree
tree_initial, leaf_txid = build_invalidation_tree(alice_fund, bob_fund)

# Retrieve the leaf node
leaf_node = tree_initial[-1]

# Save the leaf node data (balances) to a file
leaf_node_data = {
    "leaf_txid": leaf_node["txid"],
    "alice_balance": leaf_node["output_alice"],
    "bob_balance": leaf_node["output_bob"]
}

with open('leaf_node_data.json', 'w') as f:
    json.dump(leaf_node_data, f, indent=4)

with open('invalidation_tree.json', 'w') as f:
    json.dump(tree_initial, f, indent=4)



print(f"Invalidation tree built and leaf node saved to 'leaf_node_data.json'.")
"""