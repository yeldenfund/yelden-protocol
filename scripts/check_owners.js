const hre = require('hardhat');
async function main() {
  const vault = await hre.ethers.getContractAt('YeldenVault', '0x26263D5b8b340Ee816D66982048AD5c9BBF3dB85');
  const dist = await hre.ethers.getContractAt('YeldenDistributor', '0xDc473d77Cd5253fBa3D636B2472C2bf603F9430b');
  const registry = await hre.ethers.getContractAt('AIAgentRegistry', '0x0D44524E18366149f64A0fE33343D9D727fEB78D');
  console.log('Vault owner:    ' + await vault.owner());
  console.log('Dist owner:     ' + await dist.owner());
  const adminRole = await registry.DEFAULT_ADMIN_ROLE();
  const oldWallet = '0xc315a83cD36EC38Fe028C9A4Ed2E271fb2f04E97';
  const newWallet = '0xC76e0a33029c1Bd3Ac4556A58c0b57270a85b4bF';
  console.log('Registry old admin: ' + await registry.hasRole(adminRole, oldWallet));
  console.log('Registry new admin: ' + await registry.hasRole(adminRole, newWallet));
}
main().catch(console.error);
