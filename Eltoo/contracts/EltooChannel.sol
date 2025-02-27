// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EltooChannel {
    address public alice;
    address public bob;
    uint256 public fundingAmountAlice;
    uint256 public fundingAmountBob;
    bool public isChannelOpen;
    uint256 public aliceBalance;
    uint256 public bobBalance;

    uint256 public version;
    uint256 public timeout;
    uint256 public lastUpdated;
    bool public isFundingComplete;
    
    // Store the current balance of both parties
    mapping(address => uint256) public balances;

    // Event for state updates
    event StateUpdated(uint256 version, address indexed sender);
    event VersionUpdated(uint256 version, uint256 _version);
    // Event for channel settlement
    //event ChannelSettled(address indexed winner, uint256 amount);
    
    event ChannelSettled(address recipient, uint256 version, uint256 alice_balance, uint256 bob_balance);
    

    constructor(address _bob, uint256 _fundingAmountAlice, uint256 _fundingAmountBob /*, uint256 _timeout*/ ) payable {
        require(msg.value == _fundingAmountAlice, "Incorrect funding amount for Alice");
        
        alice = msg.sender;
        bob = _bob;
        fundingAmountAlice = _fundingAmountAlice;
        fundingAmountBob = _fundingAmountBob;
        version = 0;          // Initial version
        timeout = 10;   // Timeout duration
        lastUpdated = block.timestamp; // Last update timestamp
        isChannelOpen = false;
        isFundingComplete = false; 
    }

    function fundByBob() external payable {
        require(msg.sender == bob, "Only Bob can fund this");
        require(msg.value == fundingAmountBob, "Incorrect funding amount for Bob");

        aliceBalance = fundingAmountAlice;
        bobBalance = fundingAmountBob;
        isChannelOpen = true;
    }

    function getChannelBalance() external view returns (uint256, uint256) {
        return (aliceBalance, bobBalance);
    }

     // Once both parties confirm signatures off-chain, they sign the funding transaction
    function signFundingTransaction(uint256 _aliceDeposit, uint256 _bobDeposit) external {
        //require(aliceSignatureComplete && bobSignatureComplete, "Both parties must confirm signatures.");
        require(fundingAmountAlice > 0 && fundingAmountBob > 0, "Both parties must deposit funds.");
        require(!isFundingComplete, "Funding is already complete.");
        aliceBalance = _aliceDeposit;
        bobBalance = _bobDeposit;

        // Mark the funding as complete
        isFundingComplete = true;
    }

    // broadcast Trigger tx, from here system knows the timestamp that trigger tx broadcasted and stores it in lastUpdated.
    // when broadcast Settle tx later, the system only check if the timelock expires based on laterUpdated
    function broadcastTriggerTX(uint256 _newBalanceA, uint256 _newBalanceB, uint256 _version, bytes memory _signature) external {
        require(msg.sender == alice || msg.sender == bob, "Only parties can update state");
        //require(_version > version, "New version must be greater than current version");
        //require(block.timestamp < lastUpdated + _timeout, "State update timeout exceeded");  //lastUpdated + _timeout指的是上一个update tx所对应的settle tx可以上链的时间
        require(_verifySignature(msg.sender, _newBalanceA, _newBalanceB, _signature), "Invalid signature");

        balances[alice] = _newBalanceA;
        balances[bob] = _newBalanceB;
        version = _version; // Update version
        lastUpdated = block.timestamp; // Update the timestamp
        emit VersionUpdated(version, _version);
        emit StateUpdated(version, msg.sender);
    }
       // broadcast Trigger, Update Transaction 
    function updateState(uint256 _newBalanceA, uint256 _newBalanceB, uint256 _version, uint256 _timeout, bytes memory _signature) external {
        require(msg.sender == alice || msg.sender == bob, "Only parties can update state");
        require(_version > version, "New version must be greater than current version");
        require(block.timestamp < lastUpdated + _timeout, "State update timeout exceeded");  //lastUpdated + _timeout refers to the time when the settle transaction corresponding to the previous update transaction can be submitted to the blockchain.
        require(_verifySignature(msg.sender, _newBalanceA, _newBalanceB, _signature), "Invalid signature");

        balances[alice] = _newBalanceA;
        balances[bob] = _newBalanceB;
        version = _version; // Update version
        lastUpdated = block.timestamp; // Update the timestamp
        emit VersionUpdated(version, _version);
        emit StateUpdated(version, msg.sender);
    }
    
    // Settle the channel when timelock expires
    function settleChannel(uint256 _balanceA, uint256 _balanceB, uint256 _version, uint256 _timelock, bytes memory _signature) external {
        require(_version == version, "Invalid version: must match the latest state"); 
        require(block.timestamp >= lastUpdated + _timelock, "Timelock not reached"); 

        
        require(_verifySignature(alice, _balanceA, _balanceB, _signature), "Invalid signature: only Alice can settle");

        // update balances
        balances[alice] = _balanceA;
        balances[bob] = _balanceB;

       
        emit ChannelSettled(alice, version, _balanceA, _balanceB);

        // Transfer the updated balances to each party
        (bool successA, ) = alice.call{value: _balanceA}("");
        require(successA, "Transfer to Alice failed");

        (bool successB, ) = bob.call{value: _balanceB}("");
        require(successB, "Transfer to Bob failed");
    }
    
    function CooperateTX(uint256 _newBalanceA, uint256 _newBalanceB, bytes memory _signature) external {
        require(msg.sender == alice || msg.sender == bob, "Only parties can update state");
        //require(_version > version, "New version must be greater than current version");
        //require(block.timestamp < lastUpdated + _timeout, "State update timeout exceeded");  
        require(_verifySignature(msg.sender, _newBalanceA, _newBalanceB, _signature), "Invalid signature");

        //balances[alice] = _newBalanceA;
        //balances[bob] = _newBalanceB;
        aliceBalance = _newBalanceA;
        bobBalance = _newBalanceB;
        emit ChannelSettled(alice, version, _newBalanceA, _newBalanceB);
        //emit StateUpdated(version, msg.sender);

        // Transfer the updated balances to each party
        (bool successA, ) = alice.call{value: _newBalanceA}("");
        require(successA, "Transfer to Alice failed");

        (bool successB, ) = bob.call{value: _newBalanceB}("");
        require(successB, "Transfer to Bob failed");
    }

    function _verifySignature(address signer, uint256 _aliceBalance, uint256 _bobBalance, bytes memory signature) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(address(this), _aliceBalance, _bobBalance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        return _recoverSigner(ethSignedMessageHash, signature) == signer;
        //require(_recoverSigner(ethSignedMessageHash, signature) == signer, "Invalid signature in _verify");
        //return true;
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
