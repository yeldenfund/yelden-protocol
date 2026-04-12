import json, os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────────────────────
ABI_PATH  = r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json"
REGISTRY  = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
YLD_TOKEN = "0x72bf7df3f29bc2abd093d31df77ea6daec2e9ab0"
AGENT     = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

ERC20_ABI = [
    {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"approve","outputs":[{"type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"type":"address"},{"type":"address"}],"name":"allowance","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
]

# ── CONNECT ───────────────────────────────────────────────────────────────────
with open(ABI_PATH) as f:
    abi = json.load(f)['abi']

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = Account.from_key(os.getenv("PRIVATE_KEY"))

print("=" * 60)
print(f"Conectado : chain {w3.eth.chain_id}")
print(f"Wallet    : {account.address}")
print(f"ETH       : {w3.from_wei(w3.eth.get_balance(account.address), 'ether'):.6f}")
print("=" * 60)

registry = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=abi)
yld      = w3.eth.contract(address=w3.to_checksum_address(YLD_TOKEN), abi=ERC20_ABI)
nonce    = w3.eth.get_transaction_count(account.address)

# ── STEP 1: estado actual ─────────────────────────────────────────────────────
print()
print("── STEP 1: Estado actual ──────────────────────────────────")
try:
    agent_data = registry.functions.getAgent(w3.to_checksum_address(AGENT)).call()
    print(f"   getAgent() → {agent_data}")
except Exception as e:
    print(f"   getAgent() → {e}")

try:
    active = registry.functions.isActive(w3.to_checksum_address(AGENT)).call()
    print(f"   isActive() → {active}")
except Exception as e:
    print(f"   isActive() → {e}")

try:
    sc = registry.functions.score(w3.to_checksum_address(AGENT)).call()
    print(f"   score()    → {sc}")
except Exception as e:
    print(f"   score()    → {e}")

try:
    min_stake = registry.functions.minStake().call()
    print(f"   minStake() → {w3.from_wei(min_stake, 'ether')} YLD")
except Exception as e:
    print(f"   minStake() → {e}")
    min_stake = w3.to_wei(50, 'ether')
    print(f"   Usando fallback: 50 YLD")

# ── STEP 2: YLD balance ───────────────────────────────────────────────────────
print()
print("── STEP 2: YLD Balance ────────────────────────────────────")
balance   = yld.functions.balanceOf(account.address).call()
allowance = yld.functions.allowance(account.address, w3.to_checksum_address(REGISTRY)).call()
print(f"   Balance   : {w3.from_wei(balance, 'ether')} YLD")
print(f"   Allowance : {w3.from_wei(allowance, 'ether')} YLD")
print(f"   Necessário: {w3.from_wei(min_stake, 'ether')} YLD")

if balance < min_stake:
    print(f"❌ Saldo YLD insuficiente!")
    exit(1)

# ── STEP 3: approve se necessário ────────────────────────────────────────────
if allowance < min_stake:
    print()
    print("── STEP 3: Approve YLD ────────────────────────────────────")
    tx = yld.functions.approve(
        w3.to_checksum_address(REGISTRY),
        min_stake
    ).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 60000, 'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"   ✅ Approve OK → {tx_hash.hex()}")
        nonce += 1
    else:
        print(f"   ❌ Approve falhou → {tx_hash.hex()}")
        exit(1)
else:
    print()
    print("── STEP 3: Approve ── já aprovado, a saltar")

# ── STEP 4: registerAgent ────────────────────────────────────────────────────
print()
print("── STEP 4: registerAgent ──────────────────────────────────")
try:
    tx = registry.functions.registerAgent(
        "Markowitz Trading Bot",
        "trading",
        min_stake
    ).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 300000, 'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"   ✅ registerAgent OK!")
        print(f"   TX: {tx_hash.hex()}")
        print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        nonce += 1
    else:
        print(f"   ❌ registerAgent falhou → {tx_hash.hex()}")
        print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        exit(1)
except Exception as e:
    print(f"   ❌ Erro: {e}")
    exit(1)

# ── STEP 5: updateScore ───────────────────────────────────────────────────────
print()
print("── STEP 5: updateScore(886) ───────────────────────────────")
try:
    tx = registry.functions.updateScore(
        w3.to_checksum_address(AGENT),
        886
    ).build_transaction({
        'from': account.address, 'nonce': nonce,
        'gas': 200000, 'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"   ✅ updateScore OK! Score 886 on-chain.")
        print(f"   TX: {tx_hash.hex()}")
        print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    else:
        print(f"   ❌ updateScore falhou → {tx_hash.hex()}")
        print(f"   Pode precisar de SCORER_ROLE — verifica no Etherscan")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# ── STEP 6: confirmar estado ──────────────────────────────────────────────────
print()
print("── STEP 6: Confirmar estado final ─────────────────────────")
try:
    print(f"   isActive() → {registry.functions.isActive(w3.to_checksum_address(AGENT)).call()}")
    print(f"   score()    → {registry.functions.score(w3.to_checksum_address(AGENT)).call()}")
    print(f"   isEligible()→ {registry.functions.isEligible(w3.to_checksum_address(AGENT)).call()}")
except Exception as e:
    print(f"   Erro: {e}")

print()
print("=" * 60)
print("PROXIMO PASSO:")
print("Actualiza yelden_reporter.py — troca submitScore por updateScore")
print("=" * 60)
