const hre = require('hardhat');
async function main() {
  const bal = await hre.ethers.provider.getBalance('0xC76e0a33029c1Bd3Ac4556A58c0b57270a85b4bF');
  console.log('Saldo wallet nova: ' + hre.ethers.formatEther(bal) + ' POL');
}
main().catch(console.error);
