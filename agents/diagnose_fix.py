"""
diagnose_fix.py — Diagnóstico e correcção do AIAgentRegistry
Corre em: C:\YeldenBridge\diagnose_fix.py
"""

from web3 import Web3
from eth_account import Account
import json, os
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
RPC_URL      = os.getenv("RPC_URL")
PRIVATE_KEY  = os.getenv("PRIVATE_KEY")
REGISTRY     = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
WALLET       = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"
AGENT        = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

# ABI mínimo para diagnóstico e correcção
ABI = [
    # Roles
    {"inputs": [], "name": "DEFAULT_ADMIN_ROLE",
     "outputs": [{"type": "bytes32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "SCORER_ROLE",
     "outputs": [{"type": "bytes32"}], "stateMutability": "view", "type": "function"},
    # hasRole
    {"inputs": [{"type": "bytes32"}, {"type": "address"}], "name": "hasRole",
     "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
    # grantRole
    {"inputs": [{"type": "bytes32"}, {"type": "address"}], "name": "grantRole",
     "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    # agents
    {"inputs": [{"type": "address"}], "name": "agents",
     "outputs": [
         {"name": "score",       "type": "uint256"},
         {"name": "stake",       "type": "uint256"},
         {"name": "registered",  "type": "bool"},
         {"name": "active",      "type": "bool"},
     ], "stateMutability": "view", "type": "function"},
    # submitScore
    {"inputs": [
        {"name": "agent",     "type": "address"},
        {"name": "score",     "type": "uint256"},
        {"name": "batchHash", "type": "bytes32"}
     ], "name": "submitScore",
     "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    # register (caso precise re-registar)
    {"inputs": [{"name": "stakeAmount", "type": "uint256"}], "name": "register",
     "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    # isEligible
    {"inputs": [{"type": "address"}], "name": "isEligible",
     "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

# ── CONNECT ───────────────────────────────────────────────────────────────────
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)

if not w3.is_connected():
    print("❌ Sem conexão ao RPC. Verifica RPC_URL no .env")
    exit(1)

print(f"✅ Conectado: chain {w3.eth.chain_id}")
print(f"   Wallet: {WALLET}")
print(f"   Registry: {REGISTRY}")
print()

registry = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=ABI)

# ── DIAGNÓSTICO ───────────────────────────────────────────────────────────────
print("=" * 60)
print("DIAGNÓSTICO")
print("=" * 60)

# 1. Roles
try:
    SCORER_ROLE = registry.functions.SCORER_ROLE().call()
    ADMIN_ROLE  = registry.functions.DEFAULT_ADMIN_ROLE().call()
    print(f"SCORER_ROLE hash : {SCORER_ROLE.hex()}")
    print(f"ADMIN_ROLE  hash : {ADMIN_ROLE.hex()}")
except Exception as e:
    print(f"❌ Erro a ler roles: {e}")
    exit(1)

# 2. hasRole
try:
    is_scorer = registry.functions.hasRole(SCORER_ROLE, w3.to_checksum_address(WALLET)).call()
    is_admin  = registry.functions.hasRole(ADMIN_ROLE,  w3.to_checksum_address(WALLET)).call()
    print()
    print(f"Wallet tem SCORER_ROLE : {'✅ SIM' if is_scorer else '❌ NÃO'}")
    print(f"Wallet tem ADMIN_ROLE  : {'✅ SIM' if is_admin  else '❌ NÃO'}")
except Exception as e:
    print(f"❌ Erro a verificar roles: {e}")

# 3. Agent status
try:
    agent_data = registry.functions.agents(w3.to_checksum_address(AGENT)).call()
    score, stake, registered, active = agent_data
    print()
    print(f"Agent registado : {'✅ SIM' if registered else '❌ NÃO'}")
    print(f"Agent activo    : {'✅ SIM' if active     else '❌ NÃO'}")
    print(f"Score actual    : {score}")
    print(f"Stake actual    : {w3.from_wei(stake, 'ether')} YLD")
except Exception as e:
    print(f"❌ Erro a ler agent: {e}")
    registered = False
    active = False
    is_scorer = False
    is_admin = False

# 4. Elegível
try:
    eligible = registry.functions.isEligible(w3.to_checksum_address(AGENT)).call()
    print(f"isEligible      : {'✅ SIM' if eligible else '❌ NÃO'}")
except Exception as e:
    print(f"isEligible      : erro — {e}")

print()
print("=" * 60)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 60)

# ── IDENTIFICAR PROBLEMA ──────────────────────────────────────────────────────
problems = []
if not is_scorer:
    problems.append("SCORER_ROLE em falta")
if not registered:
    problems.append("Agent não registado")
elif not active:
    problems.append("Agent inactivo")

if not problems:
    print("✅ Tudo parece correcto. O problema pode ser outro.")
    print("   Tenta submeter um score manualmente abaixo para confirmar.")
else:
    print(f"⚠️  Problemas encontrados: {', '.join(problems)}")

print()

# ── CORRECÇÃO INTERACTIVA ─────────────────────────────────────────────────────
if problems:
    resp = input("Corrigir automaticamente? (s/n): ").strip().lower()
    if resp != 's':
        print("Saindo sem corrigir.")
        exit(0)

    nonce = w3.eth.get_transaction_count(account.address)

    # FIX 1 — SCORER_ROLE
    if not is_scorer:
        if not is_admin:
            print("❌ Wallet não tem ADMIN_ROLE. Não é possível conceder SCORER_ROLE.")
            print("   Precisas de acesso à wallet que fez o deploy do contrato.")
            print("   Se foi esta mesma wallet num deploy anterior, o contrato pode ter sido redeployado sem reatribuir roles.")
        else:
            print("🔧 A conceder SCORER_ROLE à wallet...")
            try:
                tx = registry.functions.grantRole(
                    SCORER_ROLE,
                    w3.to_checksum_address(WALLET)
                ).build_transaction({
                    'from':     account.address,
                    'nonce':    nonce,
                    'gas':      100000,
                    'gasPrice': w3.to_wei('1', 'gwei'),
                })
                signed = account.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print(f"✅ SCORER_ROLE concedido. TX: {tx_hash.hex()}")
                    nonce += 1
                    is_scorer = True
                else:
                    print(f"❌ grantRole falhou. TX: {tx_hash.hex()}")
            except Exception as e:
                print(f"❌ Erro em grantRole: {e}")

    # Verificar de novo após fix
    if is_scorer or not problems:
        print()
        print("🧪 A testar submitScore com score=802...")
        try:
            import hashlib
            test_hash = w3.keccak(text="test_batch_diagnose")
            tx = registry.functions.submitScore(
                w3.to_checksum_address(AGENT),
                802,
                test_hash
            ).build_transaction({
                'from':     account.address,
                'nonce':    nonce,
                'gas':      200000,
                'gasPrice': w3.to_wei('1', 'gwei'),
            })
            signed = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"✅ submitScore OK! TX: {tx_hash.hex()}")
                print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
                print()
                print("✅ Pipeline está operacional. A próxima run às 06:00 UTC vai funcionar.")
            else:
                print(f"❌ submitScore ainda falha. TX: {tx_hash.hex()}")
                print("   Verifica se o agent está registado no contrato actual.")
        except Exception as e:
            print(f"❌ Erro em submitScore: {e}")

print()
print("=" * 60)
print("FIM DO SCRIPT")
print("=" * 60)
