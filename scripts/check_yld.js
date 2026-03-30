const hre = require('hardhat');
async function main() {
  const yld = await hre.ethers.getContractAt('YLDToken', '0xE304cafC87698b0056a84f993B7Ed976116eD711');
  const supply = await yld.totalSupply();
  console.log('Total Supply: ' + hre.ethers.formatEther(supply) + ' YLD');
}
main().catch(console.error);
