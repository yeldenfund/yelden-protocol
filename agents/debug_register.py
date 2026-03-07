"""
debug_register.py — Descobre porque registerAgent falhou
Corre em: pasta agents no VPS
"""
import json, os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

REGISTRY  = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
YLD_TOKEN = "0x72D6971A5A13E250fd907E9212A9839D1B24B4b3"
AGENT     = os.getenv("AGENT_ADDRESS", "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc")

REGISTRY_ABI = [
    {"inputs":[{"name":"name","type":"string"},{"name":"agentType","type":"string"},{"name":"stakeAmount","type":"uint256"}],"name":"registerAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"isActive","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"score","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"stakeOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"statusOf","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"getAgent","outputs":[{"name":"","type":"tuple","components":[{"name":"name","type":"string"},{"name":"agentType","type":"string"},{"name":"score","type":"uint256"},{"name":"stake","type":"uint256"},{"name":"active","type":"bool"}]}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"minStake","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalAgents","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalRegistered","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"approveAgent","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"}],"name":"updateScore","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"agent","type":"address"},{"name":"newScore","type":"uint256"}],"name":"updateScore","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"SCORER_ROLE","outputs":[{"name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"name":"hasRole","outputs":[{"name":"","type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"role","type":"bytes32"},{"name":"account","type":"address"}],"name":"grantRole","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"name":"yld","outputs":[{"name":"","type":"address"}],"stateMutability":"view","type":"function"},
]

ERC20_ABI = [
    {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"},{"type":"address"}],"name":"allowance","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"approve","outputs":[{"type":"bool"}],"stateMutability":"nonpayable","type":"function"},
]

rpc = os.getenv("RPC_URL") or os.getenv("ETH_RPC_URL")
w3  = Web3(Web3.HTTPProvider(rpc))
acc = Account.from_key(os.getenv("PRIVATE_KEY"))

registry = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=REGISTRY_ABI)
yld      = w3.eth.contract(address=w3.to_checksum_address(YLD_TOKEN), abi=ERC20_ABI)

print("=" * 60)
print("DEBUG registerAgent")
print("=" * 60)

# Estado actual
print()
print("── Estado actual ──────────────────────────────────────────")
try:
    data = registry.functions.getAgent(w3.to_checksum_address(AGENT)).call()
    print(f"   getAgent → {data}")
except Exception as e:
    print(f"   getAgent → {e}")

try:
    status = registry.functions.statusOf(w3.to_checksum_address(AGENT)).call()
    status_map = {0: "UNREGISTERED", 1: "PENDING", 2: "ACTIVE", 3: "SUSPENDED", 4: "EXITED"}
    print(f"   statusOf → {status} ({status_map.get(status, 'UNKNOWN')})")
except Exception as e:
    print(f"   statusOf → {e}")

try:
    stake = registry.functions.stakeOf(w3.to_checksum_address(AGENT)).call()
    print(f"   stakeOf  → {w3.from_wei(stake, 'ether')} YLD")
    if stake > 0:
        print("   ⚠️  Agent já tem stake — pode já estar registado mas PENDING (aguarda approveAgent)")
except Exception as e:
    print(f"   stakeOf  → {e}")

try:
    total = registry.functions.totalAgents().call()
    print(f"   totalAgents → {total}")
except Exception as e:
    print(f"   totalAgents → {e}")

try:
    totalReg = registry.functions.totalRegistered().call()
    print(f"   totalRegistered → {totalReg}")
except Exception as e:
    print(f"   totalRegistered → {e}")

# YLD
print()
print("── YLD Token ──────────────────────────────────────────────")
bal = yld.functions.balanceOf(acc.address).call()
alw = yld.functions.allowance(acc.address, w3.to_checksum_address(REGISTRY)).call()
print(f"   balance   → {w3.from_wei(bal, 'ether')} YLD")
print(f"   allowance → {w3.from_wei(alw, 'ether')} YLD")

# Simular registerAgent para ver o erro exacto
print()
print("── Simular registerAgent (eth_call) ───────────────────────")
try:
    min_stake = registry.functions.minStake().call()
    registry.functions.registerAgent(
        "Markowitz Trading Bot",
        "trading",
        min_stake
    ).call({'from': acc.address})
    print("   ✅ Simulação passou — registerAgent deve funcionar")
    print("   A enviar transacção real...")

    nonce = w3.eth.get_transaction_count(acc.address)

    # approve se necessário
    if alw < min_stake:
        tx = yld.functions.approve(
            w3.to_checksum_address(REGISTRY), min_stake
        ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 80000, 'gasPrice': w3.to_wei('2','gwei')})
        signed = acc.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"   Approve: {'✅' if receipt.status==1 else '❌'} {tx_hash.hex()}")
        nonce += 1

    tx = registry.functions.registerAgent(
        "Markowitz Trading Bot", "trading", min_stake
    ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 300000, 'gasPrice': w3.to_wei('2','gwei')})
    signed  = acc.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"   ✅ registerAgent OK!")
        print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    else:
        print(f"   ❌ Ainda falha: {tx_hash.hex()}")

except Exception as e:
    print(f"   ❌ Simulação falhou: {e}")
    print()
    print("   CAUSA PROVÁVEL:")
    err = str(e).lower()
    if "already" in err:
        print("   → Agent já está registado (mesmo inactivo)")
        print("   → Tenta directamente updateScore sem registar")
    elif "stake" in err:
        print("   → Problema com stake — balance ou allowance insuficiente")
    elif "transfer" in err:
        print("   → YLD transferFrom falhou — allowance insuficiente")
    else:
        print(f"   → Erro desconhecido: {e}")

# Tentar updateScore directamente (independente do registo)
print()
print("── Tentar updateScore directamente ───────────────────────")
try:
    registry.functions.updateScore(
        w3.to_checksum_address(AGENT), 886
    ).call({'from': acc.address})
    print("   ✅ Simulação updateScore passou!")
    print("   Agent pode já estar registado — updateScore funciona.")

    nonce = w3.eth.get_transaction_count(acc.address)
    tx = registry.functions.updateScore(
        w3.to_checksum_address(AGENT), 886
    ).build_transaction({'from': acc.address, 'nonce': nonce, 'gas': 200000, 'gasPrice': w3.to_wei('2','gwei')})
    signed  = acc.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"   ✅ updateScore OK! Score 886 on-chain.")
        print(f"   TX: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    else:
        print(f"   ❌ updateScore falhou: {tx_hash.hex()}")
except Exception as e:
    print(f"   ❌ Simulação updateScore falhou: {e}")

print()
input("Prima ENTER para sair...")
