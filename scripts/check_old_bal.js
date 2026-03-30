const hre = require('hardhat');
async function main() {
  const bal = await hre.ethers.provider.getBalance('0xc315a83cD36EC38Fe028C9A4Ed2E271fb2f04E97');
  console.log('Saldo wallet comprometida: ' + hre.ethers.formatEther(bal) + ' POL');
}
main().catch(console.error);
