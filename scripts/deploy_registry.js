/**
 * deploy_registry.js — Redesploy AIAgentRegistry com Fix-3
 *
 * Uso:
 *   npx hardhat run scripts/deploy_registry.js --network polygon
 *
 * O que faz:
 *   1. Deploya novo AIAgentRegistry (com collectFeeBatch CEI fix)
 *   2. Mint 50 YLD para o deployer (se necessário)
 *   3. Aprova YLD e regista o Markowitz Bot
 *   4. Aprova o agente (SCORER_ROLE = deployer)
 *   5. Guarda novo endereço em deployed-addresses.json
 *   6. Verifica no Polygonscan (se API key disponível)
 */
const hre = require("hardhat");
const fs  = require("fs");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("===================================================");
  console.log("  AIAgentRegistry — Redesploy com Fix-3");
  console.log("===================================================");
  console.log("  Deployer: " + deployer.address);
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("  Balance:  " + hre.ethers.formatEther(balance) + " MATIC\n");

  // ── Endereços ────────────────────────────────────────────────────────
  const YLD_ADDRESS    = process.env.YLD_ADDRESS;
  const AGENT_ADDRESS  = process.env.AGENT_ADDRESS || "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc";
  const BURN_ADDRESS   = "0x000000000000000000000000000000000000dEaD";
  const MIN_STAKE      = hre.ethers.parseEther("50");
  const MONTHLY_FEE    = hre.ethers.parseEther("1");

  if (!YLD_ADDRESS) throw new Error("YLD_ADDRESS nao definido no .env");

  console.log("  YLD:     " + YLD_ADDRESS);
  console.log("  Agent:   " + AGENT_ADDRESS);
  console.log("  Burn:    " + BURN_ADDRESS + "\n");

  // ── 1. Deploy AIAgentRegistry ────────────────────────────────────────
  console.log("[1/4] Deployando AIAgentRegistry...");
  const Registry = await hre.ethers.getContractFactory("AIAgentRegistry");
  const registry = await Registry.deploy(
    YLD_ADDRESS,
    MIN_STAKE,
    MONTHLY_FEE,
    await getVaultAddress(),
    BURN_ADDRESS,
    deployer.address
  );
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log("  OK: " + registryAddress);

  // ── 2. Aprovar YLD para stake ────────────────────────────────────────
  console.log("\n[2/4] Aprovando YLD para stake...");
  const yld = await hre.ethers.getContractAt("IERC20", YLD_ADDRESS);
  
  // Verificar saldo YLD do deployer
  const yldBalance = await yld.balanceOf(deployer.address);
  console.log("  Saldo YLD deployer: " + hre.ethers.formatEther(yldBalance) + " YLD");
  
  if (yldBalance < MIN_STAKE) {
    throw new Error("Saldo YLD insuficiente para stake. Precisas de pelo menos 50 YLD.");
  }

  const approveTx = await yld.approve(registryAddress, MIN_STAKE);
  await approveTx.wait();
  console.log("  OK approve 50 YLD");

  // ── 3. Registar agente ───────────────────────────────────────────────
  console.log("\n[3/4] Registando Markowitz Bot...");
  const registerTx = await registry.registerAgent(
    "Markowitz Trading Bot",
    "TRADING",
    MIN_STAKE
  );
  await registerTx.wait();
  console.log("  OK registerAgent");

  // ── 4. Aprovar agente ────────────────────────────────────────────────
  console.log("\n[4/4] Aprovando agente (SCORER_ROLE)...");
  const approvAgentTx = await registry.approveAgent(deployer.address);
  await approvAgentTx.wait();
  console.log("  OK approveAgent — status: ACTIVE, score: 300");

  // ── Actualizar deployed-addresses.json ──────────────────────────────
  let addresses = {};
  if (fs.existsSync("deployed-addresses.json")) {
    addresses = JSON.parse(fs.readFileSync("deployed-addresses.json"));
  }
  addresses.AIAgentRegistry     = registryAddress;
  addresses.AIAgentRegistry_old = "0x32F534265090d8645652b76754B07E6648b51571";
  addresses.updatedAt           = new Date().toISOString();
  fs.writeFileSync("deployed-addresses.json", JSON.stringify(addresses, null, 2));

  console.log("\n===================================================");
  console.log("  DEPLOY COMPLETO");
  console.log("===================================================");
  console.log("  AIAgentRegistry (novo): " + registryAddress);
  console.log("  AIAgentRegistry (old):  0x32F534265090d8645652b76754B07E6648b51571");
  console.log("  Agente registado:       " + deployer.address);
  console.log("  Score inicial:          300");
  console.log("===================================================");
  console.log("\n  PROXIMOS PASSOS:");
  console.log("  1. Actualizar REGISTRY_ADDRESS no .env do VPS");
  console.log("  2. Actualizar REGISTRY_ADDRESS no .env local");
  console.log("  3. Actualizar vault.setRegistry com novo endereco");
  console.log("  4. Verificar no Polygonscan");

  // ── Verificar no Polygonscan ─────────────────────────────────────────
  if (process.env.POLYGONSCAN_API_KEY) {
    console.log("\nVerificando no Polygonscan...");
    try {
      await hre.run("verify:verify", {
        address: registryAddress,
        constructorArguments: [
          YLD_ADDRESS, MIN_STAKE, MONTHLY_FEE,
          await getVaultAddress(), BURN_ADDRESS, deployer.address
        ]
      });
      console.log("  OK AIAgentRegistry verificado");
    } catch(e) { console.log("  WARN: " + e.message); }
  }
}

async function getVaultAddress() {
  // Ler o endereço do vault do deployed-addresses.json
  if (fs.existsSync("deployed-addresses.json")) {
    const addresses = JSON.parse(fs.readFileSync("deployed-addresses.json"));
    if (addresses.YeldenVault) return addresses.YeldenVault;
  }
  // Fallback — vault novo deployado hoje
  return "0x26263D5b8b340Ee816D66982048AD5c9BBF3dB85";
}

main().catch((error) => { console.error("Deploy falhou:", error); process.exitCode = 1; });
