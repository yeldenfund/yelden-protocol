const hre = require('hardhat');
async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const vault = await hre.ethers.getContractAt('YeldenVault', '0x26263D5b8b340Ee816D66982048AD5c9BBF3dB85');
  const tx = await vault.setRegistry('0x0D44524E18366149f64A0fE33343D9D727fEB78D');
  console.log('Tx: ' + tx.hash);
  await tx.wait();
  console.log('OK vault.setRegistry actualizado');
}
main().catch(console.error);
