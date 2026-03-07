from web3 import Web3
from dotenv import load_dotenv
import os, json

load_dotenv()

PK = os.getenv("PRIVATE_KEY")
if not PK.startswith("0x"):
    PK = "0x" + PK

RPC              = "https://polygon-mainnet.g.alchemy.com/v2/4VTK2RA3hYVSgiuPshrx1"
YLD_ADDRESS      = os.getenv("YLD_ADDRESS", "0xE5Cc95489eC4Afb957f5C71593f6e4e028410cd4")
REGISTRY_ADDRESS = os.getenv("REGISTRY_ADDRESS", "0x32F534265090d8645652b76754B07E6648b51571")
AGENT_ADDRESS    = "0xfD3d7fdda54360Dc29CAa2f746aD77278A266cFc"
MIN_STAKE        = 50  # YLD

w3      = Web3(Web3.HTTPProvider(RPC))
account = w3.eth.account.from_key(PK)
print(f"Deployer: {account.address}")

# ABIs
ERC20_ABI = [
    {"name": "approve", "type": "function", "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "transfer", "type": "function", "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable"},
    {"name": "balanceOf", "type": "function", "inputs": [{"name": "account", "type": "address"}], "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view"},
]

with open(r"artifacts\contracts\AIAgentRegistry.sol\AIAgentRegistry.json") as f:
    registry_artifact = json.load(f)

yld      = w3.eth.contract(address=YLD_ADDRESS, abi=ERC20_ABI)
registry = w3.eth.contract(address=REGISTRY_ADDRESS, abi=registry_artifact["abi"])

# Saldo YLD do deployer
balance = yld.functions.balanceOf(account.address).call()
print(f"YLD balance deployer: {w3.from_wei(balance, 'ether')} YLD")

stake_amount = w3.to_wei(MIN_STAKE, "ether")

# STEP 1 — Transferir 150 YLD para o agente
print(f"\nSTEP 1 — Transferindo 150 YLD para o agente {AGENT_ADDRESS}...")
nonce = w3.eth.get_transaction_count(account.address)
tx = yld.functions.transfer(AGENT_ADDRESS, w3.to_wei(150, "ether")).build_transaction({
    "from": account.address, "nonce": nonce,
    "gas": 100_000, "gasPrice": w3.to_wei(150, "gwei"), "chainId": 137,
})
signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ Transferido: {tx_hash.hex()}")

# STEP 2 — Conceder SCORER_ROLE ao agente
print(f"\nSTEP 2 — Concedendo SCORER_ROLE ao agente...")
SCORER_ROLE = registry.functions.SCORER_ROLE().call()
nonce += 1
tx = registry.functions.grantRole(SCORER_ROLE, AGENT_ADDRESS).build_transaction({
    "from": account.address, "nonce": nonce,
    "gas": 100_000, "gasPrice": w3.to_wei(150, "gwei"), "chainId": 137,
})
signed  = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
print(f"✅ SCORER_ROLE concedido: {tx_hash.hex()}")

print(f"\n🎯 Próximo passo: agente precisa chamar registerAgent()")
print(f"   Execute: python scripts\\approve_agent.py")
print(f"\n📋 Endereços Polygon:")
print(f"   YLD:      {YLD_ADDRESS}")
print(f"   Registry: {REGISTRY_ADDRESS}")
print(f"   Agente:   {AGENT_ADDRESS}")