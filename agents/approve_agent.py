"""
approve_agent.py — Aprova o agent PENDING no registry
Corre em: pasta agents no VPS
"""
import os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

REGISTRY = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
AGENT    = os.getenv("AGENT_ADDRESS", "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc")

ABI = [
    {"inputs":[{"name":"agent","type":"address"}],"name":"approveAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"isActive","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"statusOf","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"score","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"},{"name":"newScore","type":"uint256"}],"name":"updateScore","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"DEFAULT_ADMIN_ROLE","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"name":"hasRole","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
]

rpc = os.getenv("RPC_URL") or os.getenv("ETH_RPC_URL")
w3  = Web3(Web3.HTTPProvider(rpc))
acc = Account.from_key(os.getenv("PRIVATE_KEY"))
reg = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=ABI)

print("=" * 60)
print("APPROVE AGENT")
print("=" * 60)
print(f"Wallet : {acc.address}")
print(f"Agent  : {AGENT}")

# Verificar ADMIN_ROLE
try:
    admin_role = reg.functions.DEFAULT_ADMIN_ROLE().call()
    is_admin   = reg.functions.hasRole(admin_role, acc.address).call()
    print(f"É admin: {is_admin}")
    if not is_admin:
        print("❌ Esta wallet não tem DEFAULT_ADMIN_ROLE.")
        print("   Precisas da wallet que fez o deploy do contrato.")
        input("Prima ENTER para sair...")
        exit(1)
except Exception as e:
    print(f"Erro a verificar admin: {e}")

# Estado actual
status_map = {0:"UNREGISTERED", 1:"PENDING", 2:"ACTIVE", 3:"SUSPENDED", 4:"EXITED"}
try:
    status = reg.functions.statusOf(w3.to_checksum_address(AGENT)).call()
    print(f"Status : {status} ({status_map.get(status,'UNKNOWN')})")
except Exception as e:
    print(f"statusOf: {e}")

# approveAgent
print()
print("── A chamar approveAgent() ────────────────────────────────")
nonce = w3.eth.get_transaction_count(acc.address)
try:
    # Simular primeiro
    reg.functions.approveAgent(w3.to_checksum_address(AGENT)).call({'from': acc.address})
    print("   Simulação OK — a enviar...")

    tx = reg.functions.approveAgent(
        w3.to_checksum_address(AGENT)
    ).build_transaction({
        'from': acc.address, 'nonce': nonce,
        'gas': 150000, 'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed  = acc.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 1:
        print(f"   ✅ approveAgent OK!")
        print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        nonce += 1
    else:
        print(f"   ❌ Falhou: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        input("Prima ENTER para sair...")
        exit(1)

except Exception as e:
    print(f"   ❌ Erro: {e}")
    input("Prima ENTER para sair...")
    exit(1)

# Confirmar estado
print()
print("── Estado após approveAgent ───────────────────────────────")
try:
    status  = reg.functions.statusOf(w3.to_checksum_address(AGENT)).call()
    active  = reg.functions.isActive(w3.to_checksum_address(AGENT)).call()
    print(f"   statusOf  → {status} ({status_map.get(status,'UNKNOWN')})")
    print(f"   isActive  → {active}")
except Exception as e:
    print(f"   Erro: {e}")

# updateScore imediato
print()
print("── updateScore(886) ───────────────────────────────────────")
try:
    import json
    with open("agent_performance.json") as f:
        perf = json.load(f)
    score_val = perf.get("accumulated_score") or perf.get("consistency_score", 886)

    tx = reg.functions.updateScore(
        w3.to_checksum_address(AGENT), int(score_val)
    ).build_transaction({
        'from': acc.address, 'nonce': nonce,
        'gas': 200000, 'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed  = acc.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 1:
        print(f"   ✅ Score {score_val} on-chain!")
        print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        print()
        print("   Pipeline operacional.")
        print("   Actualiza yelden_reporter.py para usar updateScore.")
    else:
        print(f"   ❌ updateScore falhou: {tx_hash.hex()}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print()
input("Prima ENTER para sair...")
