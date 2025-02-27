//const hre = require("hardhat");
const { ethers } = require("hardhat");
async function main() {
    const [alice, bob] = await ethers.getSigners();  // Get Alice and Bob signers

    // Get contract factory (this compiles the contract)
    const BidirectionalPaymentChannel = await ethers.getContractFactory("BidirectionalPaymentChannel");
  // Deploy the contract with Alice's funding (1 ETH)
  const bidirectionalPaymentChannel = await BidirectionalPaymentChannel.connect(alice).deploy(bob.address, 3600, {
    value: ethers.utils.parseEther("1.0")  // Alice's deposit
  });

  await bidirectionalPaymentChannel.deployed();
  console.log("BidirectionalPaymentChannel deployed to:", bidirectionalPaymentChannel.address);

  const aliceDeposit = await bidirectionalPaymentChannel.getAliceDeposit(); 
  console.log(`Alice's deposit: ${ethers.utils.formatEther(aliceDeposit)} ETH`);

  // Bob funds the contract by calling the fundByBob() function
  const tx = await bidirectionalPaymentChannel.connect(bob).fundByBob({
    value: ethers.utils.parseEther("2.0")  // Bob's deposit
  });

  await tx.wait();  // Wait for Bob's transaction to complete
  //console.log("Bob has funded the channel with 2 ETH");
  
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
