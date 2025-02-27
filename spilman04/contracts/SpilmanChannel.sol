// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SpilmanChannel {
    address public sender; // Alice
    address public recipient; // Bob
    uint256 public expiration; // Channel expiration time
    uint256 public totalAmount; // Total amount funded by Alice
    bool public isClosed; // State to indicate whether the channel is closed
    bool public isFundingComplete;

    constructor(address _recipient, uint256 _duration) payable {
        sender = msg.sender; // Alice
        recipient = _recipient;
        expiration = block.timestamp + _duration; // Channel valid for _duration seconds
        totalAmount = msg.value;
        isClosed = false; // Channel is open when deployed
    }

    function fundChannel() public payable {
        require(!isFundingComplete, "Channel already funded");
        require(msg.sender == sender, "Only Alice or Bob can fund the channel");
        totalAmount = msg.value;
        isFundingComplete = true;
      
    }

    // Bob submits signed payment from Alice to close the channel, 
    // Bob will only submit the last state when Alice's balance is depleted
    function closeChannel(uint256 alice_balance, uint256 bob_balance, bytes memory signature) public {
        require(!isClosed, "Channel is already closed.");
        require(msg.sender == recipient, "Only recipient can close the channel.");
        require(alice_balance + bob_balance <= totalAmount, "Invalid amount: exceeds funded amount.");
        require(_verifySignature(recipient, alice_balance, bob_balance, signature), "Invalid signature.");
        
        // Transfer the amount owed to Bob
        (bool success, ) = recipient.call{value: bob_balance}("");
        require(success, "Payment transfer failed.");
        
        // Mark the channel as closed
        //isClosed = true;

        // Refund remaining balance to Alice
        uint256 remainingBalance = address(this).balance;
        if (remainingBalance > 0) {
            (bool refundSuccess, ) = sender.call{value: remainingBalance}("");
            require(refundSuccess, "Refund to sender failed.");
        }
    }

    // Allow Alice to reclaim funds if the channel has expired
    function refund() public {
        require(!isClosed, "Channel is already closed.");   
        require(msg.sender == sender, "Only sender can refund.");
        require(block.timestamp >= expiration, "Channel has not expired yet.");
        
        // Mark the channel as closed
        isClosed = true;

        // Refund entire balance to Alice
        (bool success, ) = sender.call{value: address(this).balance}("");
        require(success, "Refund to sender failed.");
    }

    // Internal function to verify signature from Alice
    function _verifySignature(address signer, uint256 alice_balance, uint256 bob_balance, bytes memory signature) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(address(this), alice_balance, bob_balance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        return _recoverSigner(ethSignedMessageHash, signature) == signer;
    }

    function _getEthSignedMessageHash(bytes32 _messageHash) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", _messageHash));
    }

    function _recoverSigner(bytes32 _ethSignedMessageHash, bytes memory _signature) internal pure returns (address) {
        (uint8 v, bytes32 r, bytes32 s) = _splitSignature(_signature);
        return ecrecover(_ethSignedMessageHash, v, r, s);
    }

    function _splitSignature(bytes memory _sig) internal pure returns (uint8, bytes32, bytes32) {
        require(_sig.length == 65, "Invalid signature length.");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(_sig, 32))
            s := mload(add(_sig, 64))
            v := byte(0, mload(add(_sig, 96)))
        }

        return (v, r, s);
    }
}
