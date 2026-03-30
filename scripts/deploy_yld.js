const hre = require('hardhat');
async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log('Deployer: ' + deployer.address);
  const YLDToken = await hre.ethers.getContractFactory('YLDToken');
  const yld = await YLDToken.deploy(
    'Yelden Token',
    'YLD',
    hre.ethers.parseEther('1000000000'),
    deployer.address
  );
  await yld.waitForDeployment();
  const addr = await yld.getAddress();
  console.log('YLDToken: ' + addr);
  const supply = await yld.totalSupply();
  console.log('Supply: ' + hre.ethers.formatEther(supply) + ' YLD');
}
main().catch(console.error);
