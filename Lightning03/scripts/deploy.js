const { ethers } = require("hardhat");

async function main() {
    const [alice, bob] = await ethers.getSigners();

    // deploy contract 
    const fundingAmountAlice = ethers.utils.parseEther("1.0");
    const fundingAmountBob = ethers.utils.parseEther("2.0");

    const LightningChannel = await ethers.getContractFactory("LightningChannel");
    const channel = await LightningChannel.connect(alice).deploy(bob.address, fundingAmountAlice, fundingAmountBob, {
        value: fundingAmountAlice // 
    });

    await channel.deployed();
    console.log("LightningChannel deployed at:", channel.address);

    // Bob deposits his money
    const fundByBobTx = await channel.connect(bob).fundByBob({ value: fundingAmountBob });
    await fundByBobTx.wait();
    console.log("Bob has funded the channel, channel is open");

    
    const [aliceBalance, bobBalance] = await channel.getChannelBalance();
    console.log("Alice's Balance:", ethers.utils.formatEther(aliceBalance));
    console.log("Bob's Balance:", ethers.utils.formatEther(bobBalance));
}


main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
