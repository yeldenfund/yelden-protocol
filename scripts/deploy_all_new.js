const hre = require('hardhat');
const fs = require('fs');

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log('Deployer: ' + deployer.address);
  const bal = await hre.ethers.provider.getBalance(deployer.address);
  console.log('Balance: ' + hre.ethers.formatEther(bal) + ' POL');

  const gasPrice = 250000000000n;
  const USDC = '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174';

  // 1. YLDToken - 1B supply
  console.log('\n1. Deploying YLDToken...');
  const YLDToken = await hre.ethers.getContractFactory('YLDToken');
  const yld = await YLDToken.deploy('Yelden Token', 'YLD', hre.ethers.parseEther('1000000000'), deployer.address, { gasPrice });
  await yld.waitForDeployment();
  const yldAddr = await yld.getAddress();
  console.log('YLDToken: ' + yldAddr);

  // 2. ZKVerifier
  console.log('\n2. Deploying ZKVerifier...');
  const ZKVerifier = await hre.ethers.getContractFactory('ZKVerifier');
  const zkv = await ZKVerifier.deploy(deployer.address, deployer.address, { gasPrice });
  await zkv.waitForDeployment();
  const zkvAddr = await zkv.getAddress();
  console.log('ZKVerifier: ' + zkvAddr);

  // 3. YeldenVault
  console.log('\n3. Deploying YeldenVault...');
  const YeldenVault = await hre.ethers.getContractFactory('YeldenVault');
  const vault = await YeldenVault.deploy(USDC, yldAddr, deployer.address, { gasPrice });
  await vault.waitForDeployment();
  const vaultAddr = await vault.getAddress();
  console.log('YeldenVault: ' + vaultAddr);

  // 4. YeldenDistributor
  console.log('\n4. Deploying YeldenDistributor...');
  const YeldenDistributor = await hre.ethers.getContractFactory('YeldenDistributor');
  const dist = await YeldenDistributor.deploy({ gasPrice });
  await dist.waitForDeployment();
  const distAddr = await dist.getAddress();
  console.log('YeldenDistributor: ' + distAddr);

  // 5. AIAgentRegistry
  console.log('\n5. Deploying AIAgentRegistry...');
  const AIAgentRegistry = await hre.ethers.getContractFactory('AIAgentRegistry');
  const registry = await AIAgentRegistry.deploy(yldAddr, hre.ethers.parseEther("50"), hre.ethers.parseEther("1"), vaultAddr, "0x000000000000000000000000000000000000dead", deployer.address, { gasPrice });
  await registry.waitForDeployment();
  const registryAddr = await registry.getAddress();
  console.log('AIAgentRegistry: ' + registryAddr);

  // 6. Configure
  console.log('\n6. Configuring...');
  await (await vault.setDistributor(distAddr, { gasPrice })).wait();
  await (await vault.setRegistry(registryAddr, { gasPrice })).wait();
  await (await dist.setVault(vaultAddr, { gasPrice })).wait();
  console.log('Configured');

  // 7. Save addresses
  const addresses = {
    YLDToken: yldAddr,
    YeldenVault: vaultAddr,
    YeldenDistributor: distAddr,
    ZKVerifier: zkvAddr,
    AIAgentRegistry: registryAddr,
    USDC: USDC,
    deployer: deployer.address,
    oldDeployer: '0xc315a83cD36EC38Fe028C9A4Ed2E271fb2f04E97',
    network: 'polygon',
    deployedAt: new Date().toISOString()
  };
  fs.writeFileSync('deployed-addresses.json', JSON.stringify(addresses, null, 2));
  console.log('\ndeployed-addresses.json actualizado');
  console.log('\n=== DEPLOY COMPLETO ===');
  console.log(JSON.stringify(addresses, null, 2));
}
main().catch(console.error);
