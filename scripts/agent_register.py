from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

# Chave do AGENTE (0xfD3d7fdd...) — não do deployer
AGENT_PK = os.getenv("PRIVATE_KEY_AGENT")
if not AGENT_PK:
    print("❌ PRIVATE_KEY_AGENT não encontrada no .env")
    print("   Adiciona a private key do agente 0xfD3d7fdd... no .env")
    exit(1)
if not AGENT_PK.startswith("0x"):
    AGENT_PK = "0x" + AGENT_PK

RPC              = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
YLD_ADDRESS      = "0xE5Cc95489eC4Afb957f5C71593f6e4e028410cd4"
REGISTRY_ADDRESS = "0x32F534265090d8645652b76754B07E6648b51571"
MIN_STAKE        = 50

w3    = Web3(Web3.HTTPProvider(RPC))
agent = w3.eth.account.from_key(AGENT_PK)
print(f"Agente: {agent.address}")

ERC20_ABI = [
    {"name": "approve", "type": "function", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"},
]

with open(r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json") as f:
    registry_artifact = json.load(f)

yld      = w3.eth.contract(address=YLD_ADDRESS, abi=ERC20_ABI)
registry = w3.eth.contract(address=REGISTRY_ADDRESS, abi=registry_artifact["abi"])

balance = yld.functions.balanceOf(agent.address).call()
print(f"YLD balance agente: {w3.from_wei(balance, 'ether')} YLD")

stake_amount = w3.to_wei(MIN_STAKE, "ether")
nonce = w3.eth.get_transaction_count(agent.address)

# STEP 1 — Approve
print(f"\nSTEP 1 — Aprovando {MIN_STAKE} YLD para o registry...")
tx = registry.functions.registerAgent(
    "Markowitz Bot", "trading", stake_amount
).build_transaction({
    "from": agent.address, "nonce": nonce,
    "gas": 800_000, "gasPrice": w3.to_wei(150, "gwei"), "chainId": 137,
})
signed  = agent.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ Aprovado: {tx_hash.hex()}")

# STEP 2 — Register
print(f"\nSTEP 2 — Registrando agente...")
nonce += 1
tx = registry.functions.registerAgent(
    "Markowitz Bot", "trading", stake_amount
).build_transaction({
    "from": agent.address, "nonce": nonce,
    "gas": 300_000, "gasPrice": w3.to_wei(150, "gwei"), "chainId": 137,
})
signed  = agent.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ Agente registrado: {tx_hash.hex()}")
print(f"   Status: PENDING — aguarda aprovação do deployer")

