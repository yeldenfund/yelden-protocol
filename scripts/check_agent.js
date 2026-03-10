const hre = require('hardhat');
async function main() {
  const registry = await hre.ethers.getContractAt('AIAgentRegistry', '0xbC102cDec0DD007E7739ac213b62d5B031B22aF1');
  const agent = await registry.getAgent('0x84d00C78866A98CC2c7f985bdbF4871c552fF986');
  console.log('Nome:   ' + agent.name);
  console.log('Status: ' + agent.status);
  console.log('Score:  ' + agent.score);
  console.log('Stake:  ' + hre.ethers.formatEther(agent.stakeAmount) + ' YLD');
}
main().catch(console.error);
