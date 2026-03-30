const hre = require('hardhat');
async function main() {
  const deployer = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY_NEW, hre.ethers.provider);
  const agent = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY_AGENT, hre.ethers.provider);
  console.log('Deployer: ' + deployer.address);
  console.log('Agent:    ' + agent.address);
}
main().catch(console.error);
