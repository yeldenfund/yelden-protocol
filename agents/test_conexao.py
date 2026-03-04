# test_conexao.py
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()
print("📁 .env carregado")

rpc = os.getenv("ETH_RPC_URL")
print(f"🔗 RPC: {rpc[:30]}..." if rpc else "❌ RPC não encontrada")

if rpc:
    w3 = Web3(Web3.HTTPProvider(rpc))
    if w3.is_connected():
        print("✅ CONECTADO! Block:", w3.eth.block_number)
        print(f"   Chain ID: {w3.eth.chain_id}")
    else:
        print("❌ Falha na conexão")
