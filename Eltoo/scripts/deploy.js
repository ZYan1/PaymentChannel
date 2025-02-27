const { ethers } = require("hardhat");

async function main() {
    const [alice, bob] = await ethers.getSigners();

    
    const fundingAmountAlice = ethers.utils.parseEther("1.0");
    const fundingAmountBob = ethers.utils.parseEther("2.0");

    const EltooChannel = await ethers.getContractFactory("EltooChannel");
    const channel = await EltooChannel.connect(alice).deploy(bob.address, fundingAmountAlice, fundingAmountBob, {
        value: fundingAmountAlice 
    });

    await channel.deployed();
    console.log("EltooChannel deployed at:", channel.address);

   
    const fundByBobTx = await channel.connect(bob).fundByBob({ value: fundingAmountBob });
    await fundByBobTx.wait();
    console.log("Bob has funded the channel, channel is open");

   
    const [aliceBalance, bobBalance] = await channel.getChannelBalance();
    console.log("Alice's Balance:", ethers.utils.formatEther(aliceBalance));
    console.log("Bob's Balance:", ethers.utils.formatEther(bobBalance));

    const version = await channel.version();
   
}


main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
