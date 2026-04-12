"""
check_agent.py — Verifica estado do agent no registry
Corre em: C:\Users\Paulo\yelden-protocol\agents\
"""
import json, os
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

REGISTRY = "0xca380aC6418f0089CdfE33F1A175F2452A3822d7"

print("=" * 50)
print("Verificando estado do agent...")
print("=" * 50)

try:
    abi = json.load(open(r'..\artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json'))['abi']
    w3  = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
    acc = Account.from_key(os.getenv('PRIVATE_KEY'))
    reg = w3.eth.contract(address=w3.to_checksum_address(REGISTRY), abi=abi)

    print(f"Wallet    : {acc.address}")
    print(f"ETH       : {w3.from_wei(w3.eth.get_balance(acc.address), 'ether'):.6f}")
    print(f"isActive  : {reg.functions.isActive(acc.address).call()}")
    print(f"score     : {reg.functions.score(acc.address).call()}")
    print(f"isEligible: {reg.functions.isEligible(acc.address).call()}")
    print(f"stakeOf   : {w3.from_wei(reg.functions.stakeOf(acc.address).call(), 'ether')} YLD")
    print(f"minStake  : {w3.from_wei(reg.functions.minStake().call(), 'ether')} YLD")

except Exception as e:
    print(f"ERRO: {e}")

print()
input("Prima ENTER para sair...")
