"""
yelden_reporter.py — Envia score pro Yelden Registry (Polygon)
USO: python yelden_reporter.py
"""
import json
import os
import sys
from web3 import Web3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REGISTRY_ADDRESS = "0x32F534265090d8645652b76754B07E6648b51571"
POLYGON_RPC      = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"

ABI = [
    {
        "inputs": [
            {"name": "agent", "type": "address"},
            {"name": "newScore", "type": "uint256"}
        ],
        "name": "updateScore",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"type": "address"}],
        "name": "isActive",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"type": "address"}],
        "name": "score",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

print("=" * 50)
print("Yelden Reporter — Polygon Mainnet")
print("=" * 50)

# 1. Carrega performance
try:
    perf_path = os.path.join(os.path.dirname(__file__), "agent_performance.json")
    with open(perf_path) as f:
        perf = json.load(f)
    score  = perf.get("accumulated_score") or perf.get("consistency_score")
    trades = perf.get("total_trades", 0)
    print(f"Carregado: {trades} trades, score {score}")
except Exception as e:
    print(f"Erro: agent_performance.json nao encontrado — {e}")
    sys.exit(1)

# 2. Conecta Polygon
w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
if not w3.is_connected():
    print("Erro: nao conectou a Polygon")
    sys.exit(1)

private_key   = os.getenv("PRIVATE_KEY")
account       = w3.eth.account.from_key(private_key)
agent_address = os.getenv("AGENT_ADDRESS", account.address)

balance = w3.from_wei(w3.eth.get_balance(account.address), "ether")
print(f"Agente:  {account.address}")
print(f"Saldo:   {balance} MATIC")

# 3. Verifica se agente está ativo
contract = w3.eth.contract(
    address=Web3.to_checksum_address(REGISTRY_ADDRESS),
    abi=ABI
)

try:
    active = contract.functions.isActive(
        Web3.to_checksum_address(agent_address)
    ).call()
    if not active:
        print("ERRO: Agente nao esta ativo no registry Polygon.")
        sys.exit(1)
    current_score = contract.functions.score(
        Web3.to_checksum_address(agent_address)
    ).call()
    print(f"Score atual on-chain: {current_score}")
except Exception as e:
    print(f"AVISO: Nao foi possivel verificar estado: {e}")

# 4. Gera batch hash
import hashlib
batch_data = f"{agent_address}{int(score)}{trades}{datetime.now().date()}"
batch_hash = "0x" + hashlib.sha256(batch_data.encode()).hexdigest()
batch_hash_bytes = bytes.fromhex(batch_hash[2:])

# 5. Prepara transacao
nonce = w3.eth.get_transaction_count(account.address)
tx = contract.functions.updateScore(
    Web3.to_checksum_address(agent_address),
    int(score)
).build_transaction({
    "from":     account.address,
    "nonce":    nonce,
    "gas":      200_000,
    "gasPrice": w3.to_wei(150, "gwei"),
    "chainId":  137,
})

custo = w3.from_wei(tx["gas"] * tx["gasPrice"], "ether")
print(f"\nCusto estimado: {custo:.6f} MATIC")

# 6. Envia
resp = "s" if not sys.stdin.isatty() else input("Enviar? (s/N): ")

if resp.lower() == "s":
    signed  = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status == 1:
        print(f"\n✅ Transacao enviada: {tx_hash.hex()}")
        print(f"https://polygonscan.com/tx/{tx_hash.hex()}")

        receipt_path = os.path.join(os.path.dirname(__file__), "submission_receipt.json")
        with open(receipt_path, "w") as f:
            json.dump({
                "date":    datetime.now().isoformat(),
                "score":   int(score),
                "trades":  trades,
                "tx":      tx_hash.hex(),
                "chain":   "polygon",
                "status":  "success"
            }, f, indent=2)
    else:
        print(f"\n❌ Transacao falhou: {tx_hash.hex()}")
        print(f"https://polygonscan.com/tx/{tx_hash.hex()}")
        sys.exit(1)
else:
    print("Cancelado")