// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract BidirectionalPaymentChannel {
    address public alice;
    address public bob;
    uint256 public expiration;
    bool public isClosed;
    bool public isFundingComplete;

    uint256 public aliceDeposit;
    uint256 public bobDeposit;
    
    uint256 public aliceBalance;
    uint256 public bobBalance;

    // These states reflect the mutual agreement status off-chain
    bool public aliceSignatureComplete;
    bool public bobSignatureComplete;

    uint256 public currentDepth;
    
    // Events for better visibility of the process
    event ChannelFunded(address indexed participant, uint256 amount);
    event FundingComplete();
    event ChannelClosed(address indexed closer, uint256 aliceBalance, uint256 bobBalance);
    event FundsWithdrawn(address indexed participant, uint256 amount);

    // Constructor: Initialize the channel with Alice and Bob's addresses and an expiration time
    constructor(address _bob, uint256 _duration) payable {
        alice = msg.sender; // Alice creates the channel
        bob = _bob;
        expiration = block.timestamp + _duration;
        isClosed = false;
        isFundingComplete = false; 
        //aliceBalance = msg.value; // Alice's initial contribution is stored
        require(msg.value > 0, "Alice must deposit a non-zero amount.");
        aliceDeposit = msg.value; // Set Alice's deposit directly
        emit ChannelFunded(alice, msg.value);
    }
    function getAliceDeposit() public view returns (uint256) {
        return aliceDeposit; // Return the amount Alice has deposited
    }

    function getBobBalance() public view returns (uint256) {
        return bobDeposit;
    }

    /*
    // Bob can also fund the channel with his contribution
    function fundChannel() external payable {
        require(!isClosed, "Channel is already closed.");
        require(msg.sender == bob, "Only Bob can fund after Alice.");
        require(bobBalance == 0, "Bob has already funded.");

        bobBalance = msg.value; // Bob's contribution
        emit ChannelFunded(msg.sender, msg.value);
    }
    */

        // Alice deposits funds into the multisig contract (this is not yet the Funding TX on-chain)
    /*function fundByAlice() external payable {
        require(msg.sender == alice, "Only Alice can fund her part.");
        require(msg.value > 0, "Must deposit a non-zero amount.");
        require(!isFundingComplete, "Funding is already complete."); //?
        
        aliceDeposit = msg.value;
        emit ChannelFunded(alice, msg.value);
        
       
    }*/

    // Bob deposits funds into the multisig contract
    function fundByBob() external payable {
        require(msg.sender == bob, "Only Bob can fund his part.");
        require(msg.value > 0, "Must deposit a non-zero amount.");
        require(!isFundingComplete, "Funding is already complete.");
        
        bobDeposit = msg.value;
        emit ChannelFunded(bob, msg.value);
        
    }

    // Alice signals that she's received all signatures off-chain
    function aliceConfirmsSignatures() external {
        require(msg.sender == alice, "Only Alice can confirm her signatures.");
        aliceSignatureComplete = true;
    }

    // Bob signals that he's received all signatures off-chain
    function bobConfirmsSignatures() external {
        require(msg.sender == bob, "Only Bob can confirm his signatures.");
        bobSignatureComplete = true;
    }

    // Once both parties confirm signatures off-chain, they sign the funding transaction
    function signFundingTransaction(uint256 _aliceDeposit, uint256 _bobDeposit) external {
        require(aliceSignatureComplete && bobSignatureComplete, "Both parties must confirm signatures.");
        require(aliceDeposit > 0 && bobDeposit > 0, "Both parties must deposit funds.");
        require(!isFundingComplete, "Funding is already complete.");
        aliceBalance = _aliceDeposit;
        bobBalance = _bobDeposit;

        // Mark the funding as complete
        isFundingComplete = true;
    }

    function isChannelClosed() public view returns (bool) {
        return isClosed;
    }

    // Both parties can sign off-chain messages to update their balances
    function closeChannel(uint256 _aliceBalance, uint256 _bobBalance, bytes memory aliceSignature, bytes memory bobSignature) public {
    //function closeChannel(uint256 _aliceBalance, uint256 _bobBalance, bytes32 r, bytes32 s, uint8 v) public {
        require(!isClosed, "Channel is already closed.");
        require(_aliceBalance + _bobBalance <= aliceDeposit + bobDeposit, "Invalid balance sum.");

        // Verify the signatures of both Alice and Bob
        require(_verifySignature(alice, _aliceBalance, _bobBalance, aliceSignature), "Invalid Alice signature.");
        require(_verifySignature(bob, _aliceBalance, _bobBalance, bobSignature), "Invalid Bob signature.");
        //require(_verifySignature(alice, _aliceBalance, _bobBalance,  r, s, v), "Invalid Alice signature.");
        //require(_verifySignature(alice, _aliceBalance, _bobBalance, r, s, v), "Invalid Alice signature.");


        // Update balances
        aliceBalance = _aliceBalance;
        bobBalance = _bobBalance;
        
        // Close the channel
        //isClosed = true;
        emit ChannelClosed(msg.sender, aliceBalance, bobBalance);

        // Withdraw funds for both Alice and Bob
        _withdraw();
    }


    function broadcastBranch(uint256 _depth, uint256 _aliceBalance, uint256 _bobBalance, bytes memory aliceSignature) public {
    //function closeChannel(uint256 _aliceBalance, uint256 _bobBalance, bytes32 r, bytes32 s, uint8 v) public {
        require(!isClosed, "Channel is already closed.");
        //require(hashes.length > 0, "no hashes data.");
        //require(_aliceBalance + _bobBalance <= aliceDeposit + bobDeposit, "Invalid balance sum.");

        // Verify the signatures of both Alice and Bob
        require(_verifySignature(alice, _aliceBalance, _bobBalance, aliceSignature), "Invalid Alice signature.");
        //require(_verifySignature(bob, _aliceBalance, _bobBalance, bobSignature), "Invalid Bob signature.");
       


        // Update balances
        aliceBalance = _aliceBalance;
        bobBalance = _bobBalance;

        // If depth is 3, finalize the channel closure
        if (_depth == 9) {
            // Close the channel
            // isClosed = true;                                                ---------20.11.2024
            emit ChannelClosed(msg.sender, aliceBalance, bobBalance);
            //_withdraw();  // Withdraw funds for both Alice and Bob                 ---20.11.2024
        } else {
            // Increment depth for the next branch call
            currentDepth++;
        }

    }

    function broadcastPaymentTxAB(uint256 _aliceBalance, uint256 _bobBalance, bytes memory aliceSignature, bytes memory bobSignature) public {
        
        //require(_aliceBalance + _bobBalance <= aliceDeposit, "Invalid balance sum.");
        require(_verifySignaturePayment(alice, bob, _aliceBalance, _bobBalance, aliceSignature), "Invalid Alice signature.");
        require(_verifySignaturePayment(bob, alice, _aliceBalance, _bobBalance, bobSignature), "Invalid Bob signature.");
        _withdraw();


    }

    function broadcastPaymentTxBA(uint256 _aliceBalance, uint256 _bobBalance, bytes memory aliceSignature, bytes memory bobSignature) public {
        
        //require(_aliceBalance + _bobBalance <= bobDeposit, "Invalid balance sum.");
        require(_verifySignaturePayment(alice, bob, _aliceBalance, _bobBalance, aliceSignature), "Invalid Alice signature.");
        require(_verifySignaturePayment(bob, alice, _aliceBalance, _bobBalance, bobSignature), "Invalid Bob signature.");
        _withdraw();

       
    }
    
    // Allow refund if the channel has expired and no payments were made
    function refund() public {
        require(block.timestamp >= expiration, "Channel has not expired.");
        require(!isClosed, "Channel is already closed.");
        require(msg.sender == alice || msg.sender == bob, "Only Alice or Bob can refund.");

        // Close the channel
        isClosed = true;
        emit ChannelClosed(msg.sender, aliceBalance, bobBalance);

        // Refund all remaining funds
        _withdraw();
    }

    // Withdraw Alice and Bob's respective balances
    function _withdraw() internal {
        if (aliceBalance > 0) {
            uint256 amount = aliceBalance;
            aliceBalance = 0;
            (bool success, ) = alice.call{value: amount}("");
            require(success, "Alice's withdrawal failed.");
            emit FundsWithdrawn(alice, amount);
        }

        if (bobBalance > 0) {
            uint256 amount = bobBalance;
            bobBalance = 0;
            (bool success, ) = bob.call{value: amount}("");
            require(success, "Bob's withdrawal failed.");
            emit FundsWithdrawn(bob, amount);
        }

        isClosed = true;
    }


    // Verify signature for the off-chain balance agreement
    function _verifySignature(address signer, uint256 _aliceBalance, uint256 _bobBalance, bytes memory signature) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(address(this), _aliceBalance, _bobBalance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        return _recoverSigner(ethSignedMessageHash, signature) == signer;
    }

    function _verifySignaturePayment(address sender, address recipient, uint256 _aliceBalance, uint256 _bobBalance, bytes memory signature) internal pure returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(sender, recipient, _aliceBalance, _bobBalance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        return _recoverSigner(ethSignedMessageHash, signature) == sender;
    }

    /*
    function _verifySignature(address signer, uint256 _aliceBalance, uint256 _bobBalance, bytes32 r, bytes32 s, uint8 v) internal pure returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(_aliceBalance, _bobBalance));
        address recoveredAddress = ecrecover(messageHash, v, r, s);
        return recoveredAddress == signer;
    }*/


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
    /*
    function _verifySignature(address signer, uint256 _aliceBalance, uint256 _bobBalance, bytes memory signature) internal pure returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(_aliceBalance, _bobBalance));
        (bytes32 r, bytes32 s, uint8 v) = splitSignature(signature);
        address recoveredAddress = ecrecover(messageHash, v, r, s);
        return recoveredAddress == signer;
    }

    function splitSignature(bytes memory sig) internal pure returns (bytes32 r, bytes32 s, uint8 v) {
        require(sig.length == 65, "invalid signature length");

        assembly {
            r := mload(add(sig, 32))
            s := mload(add(sig, 64))
            v := byte(0, mload(add(sig, 96)))
        }

        // Adjust v if it's 0 or 1
        if (v < 27) {
            v += 27;
        }
    }*/

}
