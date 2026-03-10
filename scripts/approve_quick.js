const hre = require('hardhat');
async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const registry = await hre.ethers.getContractAt('AIAgentRegistry', '0x0D44524E18366149f64A0fE33343D9D727fEB78D');
  console.log('Aprovando agente...');
  const tx = await registry.approveAgent(deployer.address);
  console.log('Tx enviada: ' + tx.hash);
  await tx.wait();
  console.log('OK confirmado');
  const agent = await registry.getAgent(deployer.address);
  console.log('Status: ' + agent.status + ' (2=ACTIVE)');
  console.log('Score: ' + agent.score);
}
main().catch(console.error);
