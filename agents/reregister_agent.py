"""
reregister_agent.py — Re-registar agent no AIAgentRegistry
Corre em: C:\YeldenBridge\reregister_agent.py
"""

from web3 import Web3
from eth_account import Account
import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL     = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
REGISTRY    = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"
YLD_TOKEN   = os.getenv("YLD_TOKEN_ADDRESS", "")  # endereço do $YLD

AGENT = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = Account.from_key(PRIVATE_KEY)

print(f"✅ Conectado: chain {w3.eth.chain_id}")
print(f"   Wallet : {account.address}")
print(f"   Registry: {REGISTRY}")
print()

# ── ABI REGISTRY ──────────────────────────────────────────────────────────────
REGISTRY_ABI = [
    # agents() — tenta múltiplas assinaturas
    {"inputs": [{"type": "address"}], "name": "agents",
     "outputs": [
         {"name": "score",      "type": "uint256"},
         {"name": "stake",      "type": "uint256"},
         {"name": "registered", "type": "bool"},
         {"name": "active",     "type": "bool"},
     ], "stateMutability": "view", "type": "function"},
    # register com stake
    {"inputs": [{"name": "stakeAmount", "type": "uint256"}],
     "name": "register", "outputs": [],
     "stateMutability": "nonpayable", "type": "function"},
    # register sem argumento (alguns contratos)
    {"inputs": [], "name": "register", "outputs": [],
     "stateMutability": "nonpayable", "type": "function"},
    # submitScore
    {"inputs": [
        {"name": "agent",     "type": "address"},
        {"name": "score",     "type": "uint256"},
        {"name": "batchHash", "type": "bytes32"}
     ], "name": "submitScore", "outputs": [],
     "stateMutability": "nonpayable", "type": "function"},
    # minimumStake
    {"inputs": [], "name": "minimumStake",
     "outputs": [{"type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    # SCORER_ROLE
    {"inputs": [], "name": "SCORER_ROLE",
     "outputs": [{"type": "bytes32"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"type": "bytes32"}, {"type": "address"}], "name": "hasRole",
     "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
]

# ── ABI YLD TOKEN ─────────────────────────────────────────────────────────────
ERC20_ABI = [
    {"inputs": [{"type": "address"}], "name": "balanceOf",
     "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"type": "address"}, {"type": "uint256"}], "name": "approve",
     "outputs": [{"type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"type": "address"}, {"type": "address"}], "name": "allowance",
     "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals",
     "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
]

registry = w3.eth.contract(
    address=w3.to_checksum_address(REGISTRY), abi=REGISTRY_ABI)

nonce = w3.eth.get_transaction_count(account.address)

# ── STEP 1: verificar estado actual ──────────────────────────────────────────
print("── STEP 1: Estado actual ──────────────────────────")
try:
    data = registry.functions.agents(w3.to_checksum_address(AGENT)).call()
    score, stake, registered, active = data
    print(f"   Registado : {registered}")
    print(f"   Activo    : {active}")
    print(f"   Score     : {score}")
    print(f"   Stake     : {w3.from_wei(stake, 'ether')} YLD")
    if registered and active:
        print("✅ Agent já está registado e activo!")
        print("   O problema pode ser outro. A testar submitScore...")
        raise SystemExit("already_registered")
except SystemExit as e:
    if str(e) == "already_registered":
        # testar submitScore directamente
        pass
    else:
        print(f"   agents() reverteu — agent não registado neste contrato")
        registered = False

# ── STEP 2: minimumStake ──────────────────────────────────────────────────────
print()
print("── STEP 2: minimumStake ───────────────────────────")
try:
    min_stake = registry.functions.minimumStake().call()
    print(f"   minimumStake: {w3.from_wei(min_stake, 'ether')} YLD")
    STAKE_AMOUNT = min_stake
except Exception as e:
    print(f"   minimumStake() não disponível: {e}")
    # fallback: 50 YLD
    STAKE_AMOUNT = w3.to_wei(50, 'ether')
    print(f"   Usando fallback: 50 YLD")

# ── STEP 3: verificar YLD balance e allowance ─────────────────────────────────
print()
print("── STEP 3: YLD Token ──────────────────────────────")

if not YLD_TOKEN:
    print("⚠️  YLD_TOKEN_ADDRESS não está no .env")
    print("   A tentar continuar sem approve (contrato pode não exigir stake)...")
    needs_approve = False
else:
    try:
        yld = w3.eth.contract(
            address=w3.to_checksum_address(YLD_TOKEN), abi=ERC20_ABI)
        decimals = yld.functions.decimals().call()
        balance  = yld.functions.balanceOf(account.address).call()
        allowance = yld.functions.allowance(
            account.address,
            w3.to_checksum_address(REGISTRY)).call()

        print(f"   YLD balance  : {w3.from_wei(balance, 'ether')} YLD")
        print(f"   YLD allowance: {w3.from_wei(allowance, 'ether')} YLD")
        print(f"   Stake needed : {w3.from_wei(STAKE_AMOUNT, 'ether')} YLD")

        needs_approve = allowance < STAKE_AMOUNT

        if balance < STAKE_AMOUNT:
            print(f"❌ Saldo YLD insuficiente!")
            print(f"   Tens {w3.from_wei(balance, 'ether')} YLD, precisas de {w3.from_wei(STAKE_AMOUNT, 'ether')} YLD")
            print(f"   Mint mais YLD ou ajusta o minimumStake no contrato.")
            exit(1)

    except Exception as e:
        print(f"⚠️  Erro a verificar YLD: {e}")
        needs_approve = False

# ── STEP 4: approve YLD ───────────────────────────────────────────────────────
if YLD_TOKEN and needs_approve:
    print()
    print("── STEP 4: Approve YLD ────────────────────────────")
    try:
        tx = yld.functions.approve(
            w3.to_checksum_address(REGISTRY),
            STAKE_AMOUNT
        ).build_transaction({
            'from':     account.address,
            'nonce':    nonce,
            'gas':      60000,
            'gasPrice': w3.to_wei('2', 'gwei'),
        })
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"✅ Approve OK. TX: {tx_hash.hex()}")
            nonce += 1
        else:
            print(f"❌ Approve falhou. TX: {tx_hash.hex()}")
            exit(1)
    except Exception as e:
        print(f"❌ Erro no approve: {e}")
        exit(1)
else:
    print()
    print("── STEP 4: Approve ────────────────────────────────")
    print("   Não necessário ou já aprovado.")

# ── STEP 5: register ──────────────────────────────────────────────────────────
print()
print("── STEP 5: Register ───────────────────────────────")
try:
    # tenta register(stakeAmount)
    tx = registry.functions.register(STAKE_AMOUNT).build_transaction({
        'from':     account.address,
        'nonce':    nonce,
        'gas':      200000,
        'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"✅ Register OK! TX: {tx_hash.hex()}")
        print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        nonce += 1
    else:
        print(f"❌ register(stake) falhou. TX: {tx_hash.hex()}")
        print("   A tentar register() sem argumento...")
        nonce += 1
        tx2 = registry.functions.register().build_transaction({
            'from':     account.address,
            'nonce':    nonce,
            'gas':      200000,
            'gasPrice': w3.to_wei('2', 'gwei'),
        })
        signed2 = account.sign_transaction(tx2)
        tx_hash2 = w3.eth.send_raw_transaction(signed2.raw_transaction)
        receipt2 = w3.eth.wait_for_transaction_receipt(tx_hash2)
        if receipt2.status == 1:
            print(f"✅ register() OK! TX: {tx_hash2.hex()}")
            nonce += 1
        else:
            print(f"❌ register() também falhou. TX: {tx_hash2.hex()}")
            print("   Verifica o contrato no Remix — pode ter uma interface diferente.")
            exit(1)
except Exception as e:
    print(f"❌ Erro em register: {e}")
    exit(1)

# ── STEP 6: testar submitScore ────────────────────────────────────────────────
print()
print("── STEP 6: Testar submitScore ─────────────────────")
try:
    test_hash = w3.keccak(text="reregister_test_batch")
    tx = registry.functions.submitScore(
        w3.to_checksum_address(AGENT),
        886,
        test_hash
    ).build_transaction({
        'from':     account.address,
        'nonce':    nonce,
        'gas':      200000,
        'gasPrice': w3.to_wei('2', 'gwei'),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"✅ submitScore OK! Score 886 registado.")
        print(f"   https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        print()
        print("✅ Pipeline operacional. Próxima run às 06:00 UTC vai funcionar.")
    else:
        print(f"❌ submitScore ainda falha. TX: {tx_hash.hex()}")
        print("   Cola o hash aqui para análise.")
except Exception as e:
    print(f"❌ Erro em submitScore: {e}")

print()
print("=" * 60)
print("FIM")
print("=" * 60)
