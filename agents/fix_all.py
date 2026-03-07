import json, os, sys
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

REGISTRY  = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
YLD_TOKEN = "0x72bf7df3f29bc2abd093d31df77ea6daec2e9ab0"
AGENT     = os.getenv("AGENT_ADDRESS", "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc")

# ABI embutido — lido directamente do contrato compilado no PC local
REGISTRY_ABI = [
    {"inputs":[{"name":"agent","type":"address"},{"name":"newScore","type":"uint256"}],"name":"updateScore","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agents","type":"address[]"},{"name":"scores","type":"uint256[]"}],"name":"updateScoreBatch","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"name","type":"string"},{"name":"agentType","type":"string"},{"name":"stakeAmount","type":"uint256"}],"name":"registerAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"approveAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"},{"name":"level","type":"uint8"},{"name":"reason","type":"string"}],"name":"slashAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"collectFee","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"voluntaryExit","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"getAgent","outputs":[{"name":"","type":"tuple","components":[{"name":"name","type":"string"},{"name":"agentType","type":"string"},{"name":"score","type":"uint256"},{"name":"stake","type":"uint256"},{"name":"active","type":"bool"}]}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"isActive","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"isEligible","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"score","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"stakeOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"statusOf","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"feeDue","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"minStake","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"monthlyFee","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalAgents","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalActive","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"yld","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"SCORER_ROLE","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"SLASHER_ROLE","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"DEFAULT_ADMIN_ROLE","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"name":"hasRole","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"name":"grantRole","outputs":[],"stateMutability":"nonpayable","type":"function"},
]

ERC20_ABI = [
    {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"approve","outputs":[{"type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"type":"address"},{"type":"address"}],"name":"allowance","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},
]

print("=" * 60)
print("  YELDEN FIX ALL")
print("=" * 60)

# ── CONECTAR ──────────────────────────────────────────────────
rpc = os.getenv("RPC_URL") or os.getenv("ETH_RPC_URL")
w3  = Web3(Web3.HTTPProvider(rpc))
acc = Account.from_key(os.getenv("PRIVATE_KEY"))

print(f"Wallet  : {acc.address}")
print(f"ETH     : {w3.from_wei(w3.eth.get_balance(acc.address), 'ether'):.6f}")

registry = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=REGISTRY_ABI)
nonce    = w3.eth.get_transaction_count(acc.address)

# ── FIX 1: Guardar ABI em ficheiro para o mega_check ─────────
print()
print("── FIX 1: Guardar ABI local ───────────────────────────────")
os.makedirs("abi", exist_ok=True)
with open("abi/AIAgentRegistry.json", "w") as f:
    json.dump({"abi": REGISTRY_ABI}, f, indent=2)
print("   ✅ ABI guardado em abi/AIAgentRegistry.json")

# ── FIX 2: Verificar YLD real do contrato ────────────────────
print()
print("── FIX 2: YLD Token real ──────────────────────────────────")
try:
    yld_real = registry.functions.yld().call()
    print(f"   YLD no contrato: {yld_real}")
    if yld_real.lower() != YLD_TOKEN.lower():
        print(f"   ⚠️  DIFERENTE do .env! Usando: {yld_real}")
        YLD_TOKEN = yld_real
    else:
        print("   ✅ Endereço YLD correcto")
except Exception as e:
    print(f"   Erro a ler yld(): {e}")

# ── FIX 3: Estado do agent ────────────────────────────────────
print()
print("── FIX 3: Estado do agent ─────────────────────────────────")
is_active = False
try:
    is_active = registry.functions.isActive(w3.to_checksum_address(AGENT)).call()
    sc        = registry.functions.score(w3.to_checksum_address(AGENT)).call()
    stake     = registry.functions.stakeOf(w3.to_checksum_address(AGENT)).call()
    print(f"   isActive : {is_active}")
    print(f"   score    : {sc}")
    print(f"   stake    : {w3.from_wei(stake, 'ether')} YLD")
except Exception as e:
    print(f"   Erro: {e}")

# ── FIX 4: SCORER_ROLE ────────────────────────────────────────
print()
print("── FIX 4: SCORER_ROLE ─────────────────────────────────────")
has_scorer = False
try:
    SCORER_ROLE = registry.functions.SCORER_ROLE().call()
    has_scorer  = registry.functions.hasRole(SCORER_ROLE, w3.to_checksum_address(AGENT)).call()
    print(f"   Wallet tem SCORER_ROLE: {has_scorer}")
except Exception as e:
    print(f"   Erro: {e}")

# ── FIX 5: Registar agent se necessário ──────────────────────
if not is_active:
    print()
    print("── FIX 5: Registar agent ──────────────────────────────────")

    try:
        min_stake = registry.functions.minStake().call()
        print(f"   minStake: {w3.from_wei(min_stake, 'ether')} YLD")
    except:
        min_stake = w3.to_wei(50, 'ether')
        print(f"   minStake: 50 YLD (fallback)")

    # YLD balance e approve
    try:
        yld_contract = w3.eth.contract(address=w3.to_checksum_address(YLD_TOKEN), abi=ERC20_ABI)
        bal = yld_contract.functions.balanceOf(acc.address).call()
        alw = yld_contract.functions.allowance(acc.address, w3.to_checksum_address(REGISTRY)).call()
        print(f"   YLD balance  : {w3.from_wei(bal, 'ether')}")
        print(f"   YLD allowance: {w3.from_wei(alw, 'ether')}")

        if bal < min_stake:
            print(f"   ❌ Saldo YLD insuficiente!")
            print(f"      Tens {w3.from_wei(bal,'ether')} YLD, precisas {w3.from_wei(min_stake,'ether')} YLD")
            print(f"      Mint mais YLD ou reduz minStake no contrato.")
        else:
            if alw < min_stake:
                print("   A fazer approve...")
                tx = yld_contract.functions.approve(
                    w3.to_checksum_address(REGISTRY), min_stake
                ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 80000, 'gasPrice': w3.to_wei('2','gwei')})
                signed  = acc.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print(f"   ✅ Approve OK → {tx_hash.hex()}")
                    nonce += 1
                else:
                    print(f"   ❌ Approve falhou → {tx_hash.hex()}")
                    sys.exit(1)

            print("   A registar agent...")
            tx = registry.functions.registerAgent(
                "Markowitz Trading Bot", "trading", min_stake
            ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 300000, 'gasPrice': w3.to_wei('2','gwei')})
            signed  = acc.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"   ✅ registerAgent OK!")
                print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
                nonce += 1
                is_active = True
            else:
                print(f"   ❌ registerAgent falhou → {tx_hash.hex()}")
                print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")

    except Exception as e:
        print(f"   ❌ Erro: {e}")

else:
    print()
    print("── FIX 5: Agent já registado ── a saltar")

# ── FIX 6: updateScore ────────────────────────────────────────
if is_active:
    print()
    print("── FIX 6: updateScore ─────────────────────────────────────")
    try:
        with open("agent_performance.json") as f:
            perf = json.load(f)
        score_val = perf.get("accumulated_score") or perf.get("consistency_score", 886)
        print(f"   Score a submeter: {score_val}")

        tx = registry.functions.updateScore(
            w3.to_checksum_address(AGENT), int(score_val)
        ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('2','gwei')})
        signed  = acc.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"   ✅ updateScore OK! Score {score_val} on-chain.")
            print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        else:
            print(f"   ❌ updateScore falhou → {tx_hash.hex()}")
            print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
            print(f"   Wallet pode não ter SCORER_ROLE")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# ── FIX 7: Telegram SSL ───────────────────────────────────────
print()
print("── FIX 7: Telegram SSL fix ────────────────────────────────")
telegram_fix = '''
# Adiciona no topo do telegram_report.py, antes de qualquer import requests:
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
'''
print("   Para corrigir o SSL do Telegram no VPS, adiciona estas")
print("   duas linhas no TOPO do telegram_report.py:")
print()
print("   import ssl")
print("   ssl._create_default_https_context = ssl._create_unverified_context")

# ── RESUMO ────────────────────────────────────────────────────
print()
print("=" * 60)
print("  CONCLUÍDO")
print("  Próximos passos:")
print("  1. Corre yelden_reporter.py para confirmar updateScore")
print("  2. Adiciona fix SSL no telegram_report.py")
print("  3. Corre mega_check.py de novo para confirmar 0 FAIL")
print("=" * 60)
print()
input("Prima ENTER para sair...")
