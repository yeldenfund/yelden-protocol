const hre = require('hardhat');

async function main() {
  const newWallet = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY_NEW, hre.ethers.provider);
  const oldWallet = new hre.ethers.Wallet("0x" + process.env.PRIVATE_KEY, hre.ethers.provider);
  const NEW_ADDR = await newWallet.getAddress();
  const OLD_ADDR = await oldWallet.getAddress();

  const gasPrice = 300000000000n;

  let newNonce = await hre.ethers.provider.getTransactionCount(NEW_ADDR, 'latest');
  console.log('Enviando 2 POL para wallet comprometida...');
  const gasTx = await newWallet.sendTransaction({
    to: OLD_ADDR,
    value: hre.ethers.parseEther('2'),
    gasPrice,
    nonce: newNonce
  });
  console.log('TX enviada: ' + gasTx.hash);
  console.log('Aguardando confirmacao...');
  await gasTx.wait();
  console.log('Gas confirmado!');

  const bal = await hre.ethers.provider.getBalance(OLD_ADDR);
  console.log('Saldo wallet comprometida: ' + hre.ethers.formatEther(bal) + ' POL');

  let oldNonce = await hre.ethers.provider.getTransactionCount(OLD_ADDR, 'latest');
  console.log('Old nonce: ' + oldNonce);

  const vault = await hre.ethers.getContractAt('YeldenVault', '0x26263D5b8b340Ee816D66982048AD5c9BBF3dB85', oldWallet);
  const tx1 = await vault.transferOwnership(NEW_ADDR, { gasPrice, nonce: oldNonce++ });
  await tx1.wait();
  console.log('OK Vault: ' + tx1.hash);

  const dist = await hre.ethers.getContractAt('YeldenDistributor', '0xDc473d77Cd5253fBa3D636B2472C2bf603F9430b', oldWallet);
  const tx2 = await dist.transferOwnership(NEW_ADDR, { gasPrice, nonce: oldNonce++ });
  await tx2.wait();
  console.log('OK Dist: ' + tx2.hash);

  const registry = await hre.ethers.getContractAt('AIAgentRegistry', '0x0D44524E18366149f64A0fE33343D9D727fEB78D', oldWallet);
  const adminRole = await registry.DEFAULT_ADMIN_ROLE();
  const tx3 = await registry.grantRole(adminRole, NEW_ADDR, { gasPrice, nonce: oldNonce++ });
  await tx3.wait();
  console.log('OK Registry grant: ' + tx3.hash);
  const tx4 = await registry.revokeRole(adminRole, OLD_ADDR, { gasPrice, nonce: oldNonce++ });
  await tx4.wait();
  console.log('OK Registry revoke: ' + tx4.hash);

  console.log('RESCUE COMPLETO');
}
main().catch(console.error);
