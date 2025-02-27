// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LightningChannel {
    address public alice;
    address public bob;
    uint256 public fundingAmountAlice;
    uint256 public fundingAmountBob;
    bool public isChannelOpen;
    uint256 public aliceBalance;
    uint256 public bobBalance;
    // the most recent commitment transaction ID
    uint256 public latestCommitmentId;
    bool public isFundingComplete;
    
    // record commitment transaction
    struct Commitment {
        uint256 id;
        address DTXRecipient; // DTX recipient
        uint256 DTXAmount;    // DTX amount 
        address RDTXRecipient; // RDTX recipient
        uint256 RDTXAmount;    // RDTX amount
        uint256 timelock;      // time lock expire
        address BRTXRecipient; // BRTX recipient
        uint256 BRTXAmount;    // BRTX amount
    }
    Commitment public broadcastCommitment; 
    event ChannelClosed(address recipient, uint256 amount);
    event RDTXExecuted(address recipient, uint256 amount);
    event BreachRemedyExecuted(address recipient, uint256 amount);

    event ChannelSettled(address recipient, uint256 alice_balance, uint256 bob_balance);

    constructor(address _bob, uint256 _fundingAmountAlice, uint256 _fundingAmountBob) payable {
        require(msg.value == _fundingAmountAlice, "Incorrect funding amount for Alice");
        
        alice = msg.sender;
        bob = _bob;
        fundingAmountAlice = _fundingAmountAlice;
        fundingAmountBob = _fundingAmountBob;
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

    function getLastCommitmentID() external view returns (uint256) {
        return (latestCommitmentId);
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

       // broadcast commitment tx, verify if is the newest one
    function broadcastCTX(
        uint256 commitmentId,
        address DTXRecipient,
        uint256 DTXAmount,
        address RDTXRecipient,
        uint256 RDTXAmount,
        uint256 timelock,
        address BRTXRecipient,
        uint256 BRTXAmount,
        bytes memory signature // ECDSA signature
    ) external {
        require(msg.sender == alice || msg.sender == bob, "Only channel participants can broadcast");
        // verify if is the newest commitment tx
        // require(commitmentId >= latestCommitmentId, "Commitment ID must be greater than the latest commitment ID");
        // Verify the signature
        require(_verifySignature(alice, RDTXAmount, DTXAmount, signature), "Invalid signature");
        // update commitment tx
        broadcastCommitment = Commitment(commitmentId, DTXRecipient, DTXAmount, RDTXRecipient, RDTXAmount, timelock, BRTXRecipient, BRTXAmount);
        // latestCommitmentId = commitmentId;

        // closure OR BRTX 
        if (commitmentId == latestCommitmentId) {
            closeChannel(DTXRecipient, DTXAmount/*, RDTXAmount, RDTXRecipient, RDTXAmount, timelock*/);    
        } else {
            sendBRTX(DTXRecipient, DTXAmount, BRTXRecipient, BRTXAmount);
        }
        
    }
    
    
    // when dispute, alice broadcast her own
    function broadcastRDTX(
        address RDTXRecipient,
        uint256 RDTXAmount,
        bytes memory signature
        //uint256 timelock
        ) external {
        require(broadcastCommitment.RDTXRecipient == RDTXRecipient, "Recipient mismatch");
        require(broadcastCommitment.RDTXAmount == RDTXAmount, "Amount mismatch");
        require(block.timestamp >= broadcastCommitment.timelock, "Timelock not expired"); // make sure that timelock expired
        require(broadcastCommitment.RDTXAmount > 0, "RDTX amount is zero"); // make sure RDTX amount valid
        require(_verifySignatureRDTX(alice, RDTXAmount, signature), "Invalid signature");
        aliceBalance = RDTXAmount;
        // transfer RDTX amount to RDTXRecipient
        (bool success, ) = broadcastCommitment.RDTXRecipient.call{value: broadcastCommitment.RDTXAmount}("");  
        
        require(success, "Payment failed.");                                                                    
        
    }


    // Function to close the channel and distribute funds
    function closeChannel(   
        //uint256 commitmentId,
        address DTXRecipient,
        uint256 DTXAmount
        //address RDTXRecipient,
        //uint256 RDTXAmount
        //uint256 timelock
    ) internal {
        // verify if is the newest commitment tx
        require(broadcastCommitment.DTXRecipient == DTXRecipient, "Recipient mismatch");
        require(broadcastCommitment.DTXAmount == DTXAmount, "Amount mismatch");
        //require(block.timestamp >= broadcastCommitment.timelock, "Timelock not expired"); // check timelock expire

        // pay DTX to the recipient
        //payable(broadcastCommitment.DTXRecipient).transfer(broadcastCommitment.DTXAmount);
        
        //emit ChannelClosed(broadcastCommitment.DTXRecipient, broadcastCommitment.DTXAmount);

        (bool success, ) = broadcastCommitment.DTXRecipient.call{value: broadcastCommitment.DTXAmount}(""); 
        require(success, "Payment failed."); 
        //_executeRDTX(RDTXAmount);

        require(block.timestamp >= broadcastCommitment.timelock, "Timelock not expired"); 
        require(broadcastCommitment.RDTXAmount > 0, "RDTX amount is zero"); 

        // transfer RDTX amount to RDTXRecipient
        //payable(broadcastCommitment.RDTXRecipient).transfer(broadcastCommitment.RDTXAmount);
        //emit RDTXExecuted(broadcastCommitment.RDTXRecipient, broadcastCommitment.RDTXAmount);
        
    }

    // 执行 RDTX 转账
    function _executeRDTX(
        //address RDTXRecipient,
        //uint256 RDTXAmount
        //uint256 timelock
        ) internal {
        require(block.timestamp >= broadcastCommitment.timelock, "Timelock not expired"); // 确保 timelock 已到期
        require(broadcastCommitment.RDTXAmount > 0, "RDTX amount is zero"); // 确保 RDTX 金额有效
        //bobBalance = RDTXAmount;
        // 转移 RDTX 金额到 RDTXRecipient
        //payable(broadcastCommitment.RDTXRecipient).transfer(broadcastCommitment.RDTXAmount);
        //emit RDTXExecuted(broadcastCommitment.RDTXRecipient, broadcastCommitment.RDTXAmount);
        (bool success, ) = broadcastCommitment.RDTXRecipient.call{value: broadcastCommitment.RDTXAmount}("");  // !!!
        require(success, "Payment failed.");                                                                    // !!!
        
    }

    function sendBRTX(
        //uint256 commitmentId,
        address DTXRecipient,
        uint256 DTXAmount,
        address BRTXRecipient,
        uint256 BRTXAmount
    ) internal {
        // 验证提交的承诺交易是否有效
        require(broadcastCommitment.DTXRecipient == DTXRecipient, "Recipient mismatch");
        require(broadcastCommitment.DTXAmount == DTXAmount, "Amount mismatch");
        require(broadcastCommitment.BRTXRecipient == BRTXRecipient, "BRTX Recipient mismatch");
        require(broadcastCommitment.BRTXAmount == BRTXAmount, "BRTX Amount mismatch");

        // 执行 Breach Remedy，转移 BRTX 金额
        (bool successA, ) = broadcastCommitment.BRTXRecipient.call{value: broadcastCommitment.BRTXAmount}("");
        require(successA, "Transfer to Alice failed");

        
        //payable(broadcastCommitment.DTXRecipient).transfer(broadcastCommitment.DTXAmount);
        emit ChannelClosed(broadcastCommitment.DTXRecipient, broadcastCommitment.DTXAmount);
        //payable(broadcastCommitment.BRTXRecipient).transfer(broadcastCommitment.BRTXAmount);
        emit BreachRemedyExecuted(broadcastCommitment.BRTXRecipient, broadcastCommitment.BRTXAmount);
    }

    function CooperateTX(uint256 _newBalanceA, uint256 _newBalanceB, bytes memory _signature) external {
        require(msg.sender == alice || msg.sender == bob, "Only parties can update state");
        //require(_version > version, "New version must be greater than current version");
        //require(block.timestamp < lastUpdated + _timeout, "State update timeout exceeded");  //lastUpdated + _timeout指的是上一个update tx所对应的settle tx可以上链的时间
        require(_verifySignature(msg.sender, _newBalanceA, _newBalanceB, _signature), "Invalid signature");

        emit ChannelSettled(alice, _newBalanceA, _newBalanceB);

        // Transfer the updated balances to each party
        (bool successA, ) = alice.call{value: _newBalanceA}("");
        require(successA, "Transfer to Alice failed");

        (bool successB, ) = bob.call{value: _newBalanceB}("");
        require(successB, "Transfer to Bob failed");
    }

    function _verifySignature(address signer, uint256 _aliceBalance, uint256 _bobBalance, bytes memory signature) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(address(this), _aliceBalance, _bobBalance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        //return _recoverSigner(ethSignedMessageHash, signature) == signer;
        require(_recoverSigner(ethSignedMessageHash, signature) == signer, "Invalid signature in _verify");
        return true;
    }

    function _verifySignatureRDTX(address signer, uint256 _aliceBalance, bytes memory signature) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(address(this), _aliceBalance));
        bytes32 ethSignedMessageHash = _getEthSignedMessageHash(messageHash);
        //return _recoverSigner(ethSignedMessageHash, signature) == signer;
        require(_recoverSigner(ethSignedMessageHash, signature) == signer, "Invalid signature in _verify");
        return true;
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
