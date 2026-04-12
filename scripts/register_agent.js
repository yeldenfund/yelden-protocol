const hre = require('hardhat');
async function main() {
  const deployer = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY_NEW, hre.ethers.provider);
  const agentWallet = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY_AGENT, hre.ethers.provider);
  const REGISTRY = '0xbC102cDec0DD007E7739ac213b62d5B031B22aF1';
  const YLD_ADDR = '0xE304cafC87698b0056a84f993B7Ed976116eD711';
  const GP = 250000000000n;

  console.log('Agente: ' + agentWallet.address);

  // 1. Transferir YLD para agente
  const yld = await hre.ethers.getContractAt('YLDToken', YLD_ADDR, deployer);
  await (await yld.transfer(agentWallet.address, hre.ethers.parseEther('100'), { gasPrice: GP })).wait();
  console.log('100 YLD transferidos');

  // 2. Transferir POL para agente pagar gas
  await (await deployer.sendTransaction({ to: agentWallet.address, value: hre.ethers.parseEther('0.5'), gasPrice: GP })).wait();
  console.log('0.5 POL transferidos');

  // 3. Agente aprova stake
  const yldAgent = await hre.ethers.getContractAt('YLDToken', YLD_ADDR, agentWallet);
  await (await yldAgent.approve(REGISTRY, hre.ethers.parseEther('50'), { gasPrice: GP })).wait();
  console.log('Stake approved');

  // 4. Agente regista
  const registry = await hre.ethers.getContractAt('AIAgentRegistry', REGISTRY, agentWallet);
  await (await registry.registerAgent('Markowitz Bot', 'TRADING', hre.ethers.parseEther('50'), { gasPrice: GP })).wait();
  console.log('Registered');

  // 5. Deployer aprova agente
  const registryAdmin = await hre.ethers.getContractAt('AIAgentRegistry', REGISTRY, deployer);
  await (await registryAdmin.approveAgent(agentWallet.address, { gasPrice: GP })).wait();
  console.log('ACTIVE');
}
main().catch(console.error);
