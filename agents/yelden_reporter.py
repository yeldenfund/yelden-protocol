"""
yelden_reporter.py — Envia score pro Yelden Registry
USO: python yelden_reporter.py
"""

import json
import os
from web3 import Web3
from datetime import datetime
from dotenv import load_dotenv

# Carrega config
load_dotenv()

# Endereço do contrato (SUBSTITUA PELO CORRETO)
# Endereço do contrato (SUBSTITUA PELO CORRETO)
REGISTRY_ADDRESS = REGISTRY_ADDRESS = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"

# ABI mínimo
ABI = [{
    "inputs": [
        {"name": "agent", "type": "address"},
        {"name": "score", "type": "uint256"},
        {"name": "proofHash", "type": "bytes32"}
    ],
    "name": "reportPerformance",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
}]

print("="*50)
print("Yelden Reporter - Enviando para Blockchain")
print("="*50)

# 1. Carrega performance
try:
    with open("agent_performance.json") as f:
        perf = json.load(f)
    print(f"✅ Carregado: {perf['total_trades']} trades, score {perf['consistency_score']}")
except:
    print("❌ Erro: agent_performance.json não encontrado")
    exit(1)

# 2. Conecta
w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))
if not w3.is_connected():
    print("❌ Erro: não conectou à Ethereum")
    exit(1)

account = w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))
print(f"✅ Conectado: {account.address[:10]}...")
print(f"   Saldo: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

# 3. Prepara hash de prova
proof = w3.keccak(text=f"{perf['window_start']}|{perf['total_trades']}|{perf['consistency_score']}")

# 4. Prepara transação
contract = w3.eth.contract(
    address=Web3.to_checksum_address(REGISTRY_ADDRESS),
    abi=ABI
)

tx = contract.functions.reportPerformance(
    Web3.to_checksum_address(os.getenv("AGENT_ADDRESS")),
    perf['consistency_score'],
    proof
).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 200000,
    'gasPrice': w3.eth.gas_price
})

# 5. Mostra custo e pergunta
custo = w3.from_wei(tx['gas'] * tx['gasPrice'], 'ether')
print(f"\n💰 Custo estimado: {custo:.6f} ETH")
import sys
resp = "s" if not sys.stdin.isatty() else input("Enviar? (s/N): ")

if resp.lower() == 's':
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"✅ Transação enviada: 0x{tx_hash.hex()}")
    
    # Salva recibo
    with open("submission_receipt.json", "w") as f:
        json.dump({
            "data": datetime.now().isoformat(),
            "score": perf['consistency_score'],
            "tx": tx_hash.hex()
        }, f, indent=2)
else:
    print("Cancelado")
