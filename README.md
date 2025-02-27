# Project Description

This project is a smart contract development example based on Hardhat. Below are the setup and running instructions.

---

## 1. Environment Setup

### Install Dependencies
Ensure the following tools are installed:
- Node.js (recommended v16.x or higher)
- Git

Install project dependencies:
```bash
npm install
```

## 2. Start Ganache and Retrieve Private Keys

### Start Ganache
Run the following command to start Ganache and create two accounts:
```bash
ganache-cli --accounts 2 --defaultBalanceEther 10
```

### Retrieve Private Keys
Once Ganache is running, it will display the private keys of the two accounts. For example:
```bash
Private Keys:
  - 0xAlicePrivateKey
  - 0xBobPrivateKey
```

### Modify Code
Replace the contract address in your code.

## 3. Deploy Smart Contract
### Deploy Contract
Run the following command to deploy the contract to the local network:
```bash
npx hardhat run scripts/deploy.js --network localhost
```

### Retrieve Contract Address
After deployment, the console will output the contract address. For example:
```bash
Contract deployed to: 0xYourContractAddress
```
### Modify Code
Replace the contract address in your code.
