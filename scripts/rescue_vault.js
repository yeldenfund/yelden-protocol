const hre = require('hardhat');
async function main() {
  const oldWallet = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY, hre.ethers.provider);
  const vault = await hre.ethers.getContractAt('YeldenVault', '0x26263D5b8b340Ee816D66982048AD5c9BBF3dB85', oldWallet);
  console.log('Owner: ' + await vault.owner());
  console.log('Old wallet: ' + await oldWallet.getAddress());
  // Testa com gasLimit fixo
  const NEW_ADDR = '0xC76e0a33029c1Bd3Ac4556A58c0b57270a85b4bF';
  const tx = await vault.transferOwnership(NEW_ADDR, { 
    gasPrice: 300000000000n,
    gasLimit: 100000n
  });
  await tx.wait();
  console.log('OK: ' + tx.hash);
}
main().catch(console.error);
