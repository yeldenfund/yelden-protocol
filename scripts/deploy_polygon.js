/**
 * deploy_polygon.js — Yelden Protocol MVP
 * Deploy completo na Polygon Mainnet
 *
 * Sequência:
 *   1. Deploy $YLD token (ERC-20 simples)
 *   2. Deploy AIAgentRegistry
 *   3. Registrar e aprovar o agente Markowitz
 *   4. Conceder SCORER_ROLE ao reporter wallet
 *
 * Uso:
 *   npx hardhat run deploy_polygon.js --network polygon
 *
 * .env necessário:
 *   PRIVATE_KEY=...
 *   AGENT_ADDRESS=0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc
 *   POLYGONSCAN_API_KEY=... (opcional, para verificação)
 */

const hre = require("hardhat");
const { ethers } = hre;

// ─── Configuração MVP ──────────────────────────────────────────────────────────

const BURN_ADDRESS   = "0x000000000000000000000000000000000000dEaD";
const MIN_STAKE      = ethers.parseEther("50");    // 50 YLD
const MONTHLY_FEE    = ethers.parseEther("1");     // 1 YLD máximo
const INITIAL_MINT   = ethers.parseEther("10000"); // 10.000 YLD para bootstrap
const AGENT_ADDRESS  = process.env.AGENT_ADDRESS  || "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function log(msg)  { console.log(`  ${msg}`); }
function ok(msg)   { console.log(`✅ ${msg}`); }
function warn(msg) { console.log(`⚠️  ${msg}`); }
function sep()     { console.log("─".repeat(55)); }

async function verify(address, args) {
  if (!process.env.POLYGONSCAN_API_KEY) return;
  try {
    await hre.run("verify:verify", { address, constructorArguments: args });
    ok(`Verificado no Polygonscan: ${address}`);
  } catch (e) {
    warn(`Verificação falhou (pode já estar verificado): ${e.message}`);
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  sep();
  console.log("🚀 Yelden Protocol — Deploy Polygon MVP");
  sep();

  const [deployer] = await ethers.getSigners();
  const network    = await ethers.provider.getNetwork();
  const balance    = await ethers.provider.getBalance(deployer.address);

  log(`Network:   ${network.name} (chainId: ${network.chainId})`);
  log(`Deployer:  ${deployer.address}`);
  log(`Balance:   ${ethers.formatEther(balance)} MATIC`);
  log(`Agent:     ${AGENT_ADDRESS}`);
  sep();

  // Validação mínima
  if (balance < ethers.parseEther("0.5")) {
    warn("Saldo baixo — recomendado pelo menos 0.5 MATIC para deploy completo.");
  }

  // ─── STEP 1: Deploy $YLD Token ─────────────────────────────────────────────
  console.log("\n📦 STEP 1: Deploy $YLD Token");

  const YLD = await ethers.getContractFactory("YLDToken");
  const yld = await YLD.deploy(
    "Yelden",          // name
    "YLD",             // symbol
    INITIAL_MINT,      // initial supply para deployer
    deployer.address   // owner
  );
  await yld.waitForDeployment();
  const yldAddress = await yld.getAddress();
  ok(`$YLD deployed: ${yldAddress}`);
  log(`   Supply inicial: ${ethers.formatEther(INITIAL_MINT)} YLD`);

  await verify(yldAddress, ["Yelden", "YLD", INITIAL_MINT, deployer.address]);

  // ─── STEP 2: Deploy AIAgentRegistry ────────────────────────────────────────
  console.log("\n📦 STEP 2: Deploy AIAgentRegistry");

  const Registry = await ethers.getContractFactory("AIAgentRegistry");
  const registry = await Registry.deploy(
    yldAddress,          // _yld
    MIN_STAKE,           // _minStake (50 YLD)
    MONTHLY_FEE,         // _monthlyFee (1 YLD)
    deployer.address,    // _vault (temporário — deployer até vault estar pronto)
    BURN_ADDRESS,        // _burnAddress
    deployer.address     // _admin
  );
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  ok(`AIAgentRegistry deployed: ${registryAddress}`);
  log(`   minStake:    ${ethers.formatEther(MIN_STAKE)} YLD`);
  log(`   monthlyFee:  ${ethers.formatEther(MONTHLY_FEE)} YLD`);
  log(`   burnAddress: ${BURN_ADDRESS}`);

  await verify(registryAddress, [
    yldAddress, MIN_STAKE, MONTHLY_FEE,
    deployer.address, BURN_ADDRESS, deployer.address
  ]);

  // ─── STEP 3: Conceder SCORER_ROLE ao reporter wallet ───────────────────────
  console.log("\n🔑 STEP 3: Configurar SCORER_ROLE");

  const SCORER_ROLE = await registry.SCORER_ROLE();

  // Reporter wallet (agente) precisa de SCORER_ROLE para chamar updateScore
  const tx1 = await registry.grantRole(SCORER_ROLE, AGENT_ADDRESS);
  await tx1.wait();
  ok(`SCORER_ROLE concedido a: ${AGENT_ADDRESS}`);

  // Deployer também mantém SCORER_ROLE para poder aprovar o agente
  // (já tem via constructor — confirmar)
  const hasRole = await registry.hasRole(SCORER_ROLE, deployer.address);
  log(`   Deployer tem SCORER_ROLE: ${hasRole}`);

  // ─── STEP 4: Registrar o agente Markowitz ──────────────────────────────────
  console.log("\n🤖 STEP 4: Registrar agente Markowitz");

  // Aprovar o registry para gastar YLD do deployer
  const approveTx = await yld.approve(registryAddress, MIN_STAKE);
  await approveTx.wait();
  log(`   YLD aprovado para registry: ${ethers.formatEther(MIN_STAKE)} YLD`);

  // Registrar o agente (como deployer, em nome do agente)
  // NOTA: registerAgent usa msg.sender — o agente precisa chamar ele mesmo
  // Para MVP, transferir YLD para o AGENT_ADDRESS e ele se registra
  // OU: usar uma função de registro delegado (V2)
  //
  // Solução MVP: transferir stake para agent wallet e documentar que
  // o agent precisa chamar registerAgent() + approveAgent() manualmente
  
  const transferTx = await yld.transfer(AGENT_ADDRESS, MIN_STAKE * 3n); // 150 YLD
  await transferTx.wait();
  ok(`Transferido ${ethers.formatEther(MIN_STAKE * 3n)} YLD para o agente`);
  warn("AÇÃO MANUAL NECESSÁRIA:");
  log("   O agente precisa chamar registerAgent() com 50 YLD de stake.");
  log("   Depois o deployer chama approveAgent() para ativar.");
  log("   Ver instruções abaixo.");

  // ─── STEP 5: Transferir YLD restante para treasury ─────────────────────────
  console.log("\n💰 STEP 5: Distribuição inicial de YLD");

  const deployerBalance = await yld.balanceOf(deployer.address);
  log(`   Saldo restante no deployer: ${ethers.formatEther(deployerBalance)} YLD`);
  log(`   (Manter para operações futuras — fees, novos agentes, etc.)`);

  // ─── RESUMO FINAL ──────────────────────────────────────────────────────────
  sep();
  console.log("\n🎯 DEPLOY COMPLETO — Resumo");
  sep();
  console.log(`\n  $YLD Token:        ${yldAddress}`);
  console.log(`  AIAgentRegistry:   ${registryAddress}`);
  console.log(`  Admin/Deployer:    ${deployer.address}`);
  console.log(`  Agent (Markowitz): ${AGENT_ADDRESS}`);
  console.log(`  Network:           Polygon Mainnet`);

  sep();
  console.log("\n📋 PRÓXIMOS PASSOS MANUAIS:");
  console.log(`
  1. Adicionar MATIC à wallet do agente para gas:
     ${AGENT_ADDRESS}

  2. O agente chama registerAgent() no registry:
     npx hardhat run scripts/register_agent.js --network polygon

  3. O deployer chama approveAgent():
     npx hardhat run scripts/approve_agent.js --network polygon

  4. Atualizar .env no VPS:
     RPC_URL=https://polygon-rpc.com
     REGISTRY_ADDRESS=${registryAddress}
     YLD_ADDRESS=${yldAddress}

  5. Testar primeira submission:
     py yelden_reporter.py
  `);

  sep();
  console.log("\n📄 Salvar estes endereços no YELDEN_HANDOFF:");
  console.log(JSON.stringify({
    network: "polygon",
    chainId: 137,
    yld: yldAddress,
    registry: registryAddress,
    agent: AGENT_ADDRESS,
    deployedAt: new Date().toISOString()
  }, null, 2));
  sep();
}

main().catch((error) => {
  console.error("\n❌ Deploy falhou:", error.message);
  process.exitCode = 1;
});
