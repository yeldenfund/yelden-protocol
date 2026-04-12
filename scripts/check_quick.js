const hre = require('hardhat');
async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const registry = await hre.ethers.getContractAt('AIAgentRegistry', '0x0D44524E18366149f64A0fE33343D9D727fEB78D');
  const agent = await registry.getAgent(deployer.address);
  console.log('Status: ' + agent.status);
  console.log('Score: ' + agent.score);
  console.log('Stake: ' + hre.ethers.formatEther(agent.stake));
}
main().catch(console.error);
