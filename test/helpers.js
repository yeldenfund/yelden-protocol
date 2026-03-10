const { ethers } = require("hardhat");

async function deployVaultOnly() {
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const mockUSDC = await MockERC20.deploy("Mock USDC", "USDC", 6);
  await mockUSDC.waitForDeployment();

  const YeldenVault = await ethers.getContractFactory("YeldenVault");
  const vault = await YeldenVault.deploy(
    await mockUSDC.getAddress(),
    "Yelden USD",
    "yUSD"
  );
  await vault.waitForDeployment();
  return { vault, usdc: mockUSDC };
}

async function deployConnected() {
  const { vault, usdc } = await deployVaultOnly();

  // FIX-1: yieldOracle é o signer[1] — separado do owner (signer[0])
  // Os testes que chamavam vault.connect(owner).harvest() devem usar yieldOracle
  const [owner, yieldOracle] = await ethers.getSigners();
  await vault.setYieldOracle(await yieldOracle.getAddress());

  const YeldenDistributor = await ethers.getContractFactory("YeldenDistributor");
  const distributor = await YeldenDistributor.deploy();
  await distributor.waitForDeployment();

  // Configura o vault no distribuidor
  await distributor.setVault(await vault.getAddress());
  // Configura o distribuidor no vault
  await vault.setDistributor(await distributor.getAddress());

  return { vault, distributor, usdc, owner, yieldOracle };
}

async function deployWithVerifier() {
  const { vault, distributor, usdc, owner, yieldOracle } = await deployConnected();

  // FIX: ZKVerifier agora recebe (verifierAddress, distributorAddress)
  // Em testes sem Groth16Verifier real, passa address(0) para o verifier
  const ZKVerifier = await ethers.getContractFactory("ZKVerifier");
  const verifier = await ZKVerifier.deploy(
    ethers.ZeroAddress,                    // verifier stub (sem Groth16 em testes)
    await distributor.getAddress()         // distributor
  );
  await verifier.waitForDeployment();

  return { vault, distributor, usdc, verifier, owner, yieldOracle };
}

module.exports = {
  deployVaultOnly,
  deployConnected,
  deployWithVerifier
};
