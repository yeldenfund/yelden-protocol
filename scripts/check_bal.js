const hre = require('hardhat');
async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const bal = await hre.ethers.provider.getBalance(deployer.address);
  console.log('MATIC: ' + hre.ethers.formatEther(bal));
}
main().catch(console.error);
