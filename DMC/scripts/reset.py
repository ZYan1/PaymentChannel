import json
from web3 import Web3
from establishment import duplex_payments, sign_node


#with open('invalidation_tree_with_signatures.json', 'r') as f:
   # tree_initial = json.load(f)

#tree = tree_initial
#safe_margin = 15
def modify_branch(tree_initial, update_A_Balance, update_B_Balance, alice_private_key, bob_private_key, safe_margin):
    """
    Resets the duplex micropayment channels when one of the channels is exhausted.
    This creates a new branch in the invalidation tree with updated balances.
    """
    #print(f"Resetting channels. Current balances: Alice {Cab_alice_balance} BTC, Bob {Cba_bob_balance} BTC")

    """
    The start node for the new branch is selected based on the timelocks of the previous branch:

    If the timelock k of node d-1 is 15s greater than d-2, then node d-1 becomes the start node.
    Otherwise, the root node T1,k (node d=1) is the start node.
    The chosen node's timelock will be reduced by 15s (or another margin Δ).
    """
    # step 1: find start node
    start_node = choose_first_node(tree_initial, safe_margin)
    print(f"Depth: {start_node["depth"]}")
          
    #redeem_script = create_funding_transaction(alice_rpc, bob_rpc)
    #main.tree, main.branch = build_invalidation_tree(alice_rpc, bob_rpc, redeem_script, 3, 100)
    
    for node in tree_initial:
        
        # Step 2: reset the timelock for start_node of the new branch
        if node["depth"] == start_node["depth"]:
            node["timelock"] = start_node["timelock"] - safe_margin
        
        node['tx_data']['alice_balance'] = update_A_Balance
        node['tx_data']['bob_balance'] = update_B_Balance

        
        signature_alice = sign_node(alice_private_key, update_A_Balance, update_B_Balance)
        signature_bob = sign_node(bob_private_key, update_A_Balance, update_B_Balance)
        # 更新节点签名
        node['signatures']['alice'] = signature_alice.signature.hex()
        node['signatures']['bob'] = signature_bob.signature.hex()

    
  
    
    #print(tree_initial)
    with open('invalidation_tree_with_signatures.json', 'w') as f:
        json.dump(tree_initial, f, indent=4)

    print("Tree modified and saved successfully, original file overwritten.")

    return tree_initial 


def choose_first_node(tree_initial, safe_margin):
    """
    Select the first node from the invalidation tree based on timelock conditions.
    If the difference in timelock between two nodes is >= 20, return that node.
    Otherwise, return the first node in the tree.
    """
    # Iterate through the tree in reverse order to check timelock differences
    for i in reversed(range(1, len(tree_initial))):   #[2,1,0]

        if tree_initial[i]['timelock'] - tree_initial[i-1]['timelock'] >= safe_margin:
            # If the condition is met, return the current node as chosen_node
            chosen_node = tree_initial[i]
            return chosen_node
            #return chosen_node
        i -= 1
        # If no node meets the condition, return the first node
    
    chosen_node = tree_initial[0]
    return chosen_node


    """node_d_minus_1 = tree[-2] # second to last
    node_d_minus_2 = tree[-3]

    # Compare timelocks
    if node_d_minus_1["timelock"] - node_d_minus_2["timelock"] >= SAFE_MARGIN:
        print(f"Choosing node at depth {node_d_minus_1['depth']} as the start node.")
        return node_d_minus_1 # Use d-1 as the start node
    else:
        print("Choosing root node (d=1) as the start node.")
        return tree[0]  # Use the root node (d=1)"""
    

# Update the invalidation tree (FIFO queue with length = 1)
"""
def update_invalidation_tree(new_branch_tx):
    import main
    
    #Simulates updating the invalidation tree by maintaining a FIFO queue with length = 1. 
    
    #tree = []
    if main.branch >= 1:
        print("Popping old branch from the tree.")
        main.branch.pop(0)  # Pop the old branch
    print("Appending new branch to the tree.")
    new_branch = main.branch.append(new_branch_tx)  # Append the new branch
    
    return new_branch"""


"""
def establish_and_reset_duplex_channel():
    alice_rpc = get_alice_rpc()
    bob_rpc = get_bob_rpc()

    # Setup initial balances for both channels
    Cab_alice_balance = 1.0  # Alice's initial balance in CAB (1 BTC)
    Cba_bob_balance = 2.0    # Bob's initial balance in CBA (2 BTC)

    # Establish the payment channels
    tx_Cab_signed_by_bob, tx_Cba_signed_by_alice, new_Cab_alice_balance, new_Cba_bob_balance, success = create_payment_transactions(
        alice_rpc, bob_rpc, "leaf_txid_placeholder", "redeem_script_placeholder", Cab_alice_balance, Cba_bob_balance
    )

    # If either channel was exhausted, reset the channels
    if not success:
        print("Reset operation completed successfully.")
    else:
        print("Channels are operational.")

# Execute the DMC setup and reset mechanism
if __name__ == "__main__":
    establish_and_reset_duplex_channel()"""