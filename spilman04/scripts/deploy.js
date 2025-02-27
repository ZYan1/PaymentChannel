const { ethers } = require("hardhat");

async function main() {
    const [owner, recipient] = await ethers.getSigners();
    const SpilmanChannel = await ethers.getContractFactory("SpilmanChannel");
    const duration = 3600; // Lifetime of the channel = 1h
    const initialBalance = ethers.utils.parseEther("1.0"); // initial deposit 1 ETH

    // Alice (the owner) funds the contract with 1 ETH on creation.
    // The contract will hold 1 ETH until the off-chain process completes and Bob submits the final state on-chain to claim the remaining funds.
    const paymentChannel = await SpilmanChannel.deploy(recipient.address, duration, { value: initialBalance });
    await paymentChannel.deployed();

    console.log("PaymentChannel deployed to, i.e the contract address:", paymentChannel.address);
    // console.log("Owner(Alice's) address:", owner.address);
    // console.log("Recipient(Bob's) address:", recipient.address);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
